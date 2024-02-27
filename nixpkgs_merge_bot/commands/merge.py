import logging
from dataclasses import dataclass

from ..database import Database
from ..github.GitHubClient import GithubClient, GithubClientError, get_github_client
from ..github.Issue import IssueComment
from ..github.PullRequest import PullRequest
from ..merging_strategies.maintainer_update import MaintainerUpdate
from ..settings import Settings
from ..webhook.http_response import HttpResponse
from ..webhook.utils.issue_response import issue_response

log = logging.getLogger(__name__)


@dataclass
class CheckRunResult:
    success: bool
    pending: bool
    failed: bool
    messages: list[str]


def process_pull_request_status(
    client: GithubClient, pull_request: PullRequest
) -> CheckRunResult:
    check_run_result = CheckRunResult(True, False, False, [])

    # As ofBorg takes a while to add a check_suite to the pull request we have to check the statues first if this is still pending

    statuses = client.get_statuses_for_commit(
        pull_request.repo_owner, pull_request.repo_name, pull_request.head_sha
    ).json()
    if statuses["state"] != "success":
        check_run_result.success = False
        log.info(f"{pull_request.number}: Status {statuses['state']} is not success")
    if statuses["state"] == "pending":
        check_run_result.success = False
        check_run_result.pending = True
        message = "Some status is still pending"
        log.info(f"{pull_request.number}: {message}")
        check_run_result.messages.append(message)
    if check_run_result.success:
        log.debug(
            f"{pull_request.number} All the statues where fine we now move to check the check_suites"
        )
        log.debug(f"{pull_request.number}: Getting check suites for commit")
        check_runs_for_commit = client.get_check_runs_for_commit(
            pull_request.repo_owner, pull_request.repo_name, pull_request.head_sha
        )
        for check_run in check_runs_for_commit.json()["check_runs"]:
            log.debug(
                f"{check_run['app']['name']} conclusion: {check_run['conclusion']} and status: {check_run['status']}"
            )
            # Ignoring darwin checks for ofborg as these get stucked quite often
            if (
                "darwin" in check_run["name"]
                and check_run["app"]["name"] == "ofborg"
                and (
                    check_run["status"] == "queued" or check_run["status"] == "neutral"
                )
            ):
                continue
            if check_run["status"] != "completed":
                message = f"Check run {check_run['app']['name']} is not completed, we will wait for it to finish and if it succeeds we will merge this."
                check_run_result.messages.append(message)
                log.info(f"{pull_request.number}: {message}")
                check_run_result.success = False
                if (
                    check_run["status"] == "in_progress"
                    or check_run["status"] == "queued"
                ):
                    log.debug(
                        f"{pull_request.number}: Check run is in progress or queued"
                    )
                    check_run_result.pending = True
            else:
                # if the state is not success or skipped we will decline the merge. The state can be
                # Can be one of: success, failure, neutral, cancelled, timed_out, action_required, stale, null, skipped, startup_failure
                if not (
                    check_run["conclusion"] == "success"
                    or check_run["conclusion"] == "skipped"
                    or check_run["conclusion"] == "neutral"
                ):
                    check_run_result.success = False
                    check_run_result.failed = True
                    message = f"Check suite {check_run['app']['name']} is {check_run['conclusion']}"
                    check_run_result.messages.append(message)
                    log.info(f"{pull_request.number}: message")
    return check_run_result


def merge_command(issue_comment: IssueComment, settings: Settings) -> HttpResponse:
    log.debug(
        f"{issue_comment.issue_number }: We have been called with the merge command"
    )
    log.debug(f"{issue_comment.issue_number }: Getting GitHub client")
    client = get_github_client(settings)
    pull_request = PullRequest.from_json(
        client.pull_request(
            issue_comment.repo_owner,
            issue_comment.repo_name,
            issue_comment.issue_number,
        ).json()
    )
    # Setup for this comment is done we ensured that this is address to us and we have a command

    log.info(f"{issue_comment.issue_number }: Checking meragability")
    merge_stragies = [MaintainerUpdate(client, settings)]

    one_merge_strategy_passed = False
    decline_reasons = []
    for merge_stragy in merge_stragies:
        log.info(f"{issue_comment.issue_number}: Running {merge_stragy} merge strategy")
        check, decline_reasons_strategy = merge_stragy.run(
            pull_request, issue_comment.commenter_id
        )
        decline_reasons.extend(decline_reasons_strategy)
        if check:
            one_merge_strategy_passed = True
    for reason in decline_reasons:
        log.info(f"{issue_comment.issue_number}: {reason}")

    if one_merge_strategy_passed:
        log.info(
            f"{issue_comment.issue_number }: A merge strategy passed we will notify the user with a rocket emoji"
        )
        client.create_issue_reaction(
            issue_comment.repo_owner,
            issue_comment.repo_name,
            issue_comment.issue_number,
            issue_comment.comment_id,
            "rocket",
        )
        check_suite_result = process_pull_request_status(client, pull_request)
        decline_reasons.extend(check_suite_result.messages)
        if check_suite_result.pending:
            db = Database(settings)
            db.add(
                pull_request.head_sha,
                f"{str(issue_comment.issue_number)};{issue_comment.commenter_id};{issue_comment.commenter_login}",
            )
            msg = "One or more checks are still pending, we will wait for them to finish and if it succeeds we will merge this."
            log.info(f"{issue_comment.issue_number}: {msg}")
            client.create_issue_comment(
                issue_comment.repo_owner,
                issue_comment.repo_name,
                issue_comment.issue_number,
                msg,
            )
            return issue_response("merge-postponed")
        elif check_suite_result.success:
            try:
                log.info(f"{issue_comment.issue_number }: Trying to merge pull request")
                client.merge_pull_request(
                    issue_comment.repo_owner,
                    issue_comment.repo_name,
                    issue_comment.issue_number,
                    pull_request.head_sha,
                )
                log.info(f"{issue_comment.issue_number }: Merge completed")
                client.create_issue_comment(
                    issue_comment.repo_owner,
                    issue_comment.repo_name,
                    issue_comment.issue_number,
                    "Merge completed",
                )
                return issue_response("merged")
            except GithubClientError as e:
                log.exception(f"{issue_comment.issue_number}: merge failed")
                decline_reasons.extend(
                    "\n".join(
                        [
                            f"@{issue_comment.commenter_login} merge failed:",
                            "```",
                            f"{e.code} {e.reason}: {e.body}",
                            "```",
                        ]
                    )
                )

                client.create_issue_comment(
                    issue_comment.repo_owner,
                    issue_comment.repo_name,
                    issue_comment.issue_number,
                    "\n".join(decline_reasons),
                )
                return issue_response("merge-failed")
        elif check_suite_result.failed:
            log.info(
                f"{issue_comment.issue_number }: OfBorg failed, we let the user know"
            )
            msg = f"@{issue_comment.commenter_login} merge not possible, check suite failed: \n"
            for reason in decline_reasons:
                msg += f"{reason}\n"

            log.info(msg)
            client.create_issue_comment(
                issue_comment.repo_owner,
                issue_comment.repo_name,
                issue_comment.issue_number,
                msg,
            )
            return issue_response("not-permitted-check-run-failed")
        else:
            msg = f"@{issue_comment.commenter_login} merge not permitted: \n"
            for reason in decline_reasons:
                msg += f"{reason}\n"

            log.info(msg)
            client.create_issue_comment(
                issue_comment.repo_owner,
                issue_comment.repo_name,
                issue_comment.issue_number,
                msg,
            )
            return issue_response("not-permitted")

    else:
        log.info(
            f"{issue_comment.issue_number}: No merge stratgey passed, we let the user know"
        )
        msg = f"@{issue_comment.commenter_login} merge not permitted: \n"
        for reason in decline_reasons:
            msg += f"{reason}\n"

        log.info(msg)
        client.create_issue_comment(
            issue_comment.repo_owner,
            issue_comment.repo_name,
            issue_comment.issue_number,
            msg,
        )
        return issue_response("not-permitted")
