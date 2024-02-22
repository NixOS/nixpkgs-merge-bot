import logging
from dataclasses import dataclass

from ..database import Database
from ..github.GitHubClient import GithubClient, GithubClientError, get_github_client
from ..github.Issue import Issue
from ..github.PullRequest import PullRequest
from ..merging_startegies.maintainer_update import MaintainerUpdate
from ..settings import Settings
from ..webhook.http_response import HttpResponse
from ..webhook.utils.issue_response import issue_response

log = logging.getLogger(__name__)


@dataclass
class CheckSuiteResult:
    success: bool
    pending: bool
    failed: bool
    messages: list[str]


def process_pull_request_status(
    client: GithubClient, pull_request: PullRequest
) -> CheckSuiteResult:
    messages = []
    check_suite_result = CheckSuiteResult(True, False, False, [])

    # As ofBorg takes a while to add a check_suite to the pull request we have to check the statues first if this is still pending

    statuses = client.get_statuses_for_commit(
        pull_request.repo_owner, pull_request.repo_name, pull_request.head_sha
    ).json()
    if statuses["state"] != "success":
        check_suite_result.success = False
        log.info(f"Status {statuses['state']} is not success")
    if statuses["state"] == "pending":
        check_suite_result.success = False
        check_suite_result.pending = True
        message = "Some status is still pending"
        log.info(message)
        messages.append(message)
    if check_suite_result.success:
        log.debug(
            f"{pull_request.number} All the statues where fine we now move to check the check_suites"
        )
        log.debug(f"{pull_request.number}Getting check suites for commit")
        check_suites_for_commit = client.get_check_suites_for_commit(
            pull_request.repo_owner, pull_request.repo_name, pull_request.head_sha
        )
        for check_suite in check_suites_for_commit.json()["check_suites"]:
            log.debug(
                f"{check_suite['app']['name']} conclusion: {check_suite['conclusion']} and status: {check_suite['status']}"
            )
            # First check if all check suites are completed if not we will add them to the database and wait for the webhook for finished check suites
            # The summary status for all check runs that are part of the check suite. Can be requested, in_progress, or completed.
            if check_suite["status"] != "completed":
                message = f"Check suite {check_suite['app']['name']} is not completed, we will wait for it to finish and if it succeeds we will merge this."
                messages.append(message)
                log.info(message)
                check_suite_result.success = False
                if check_suite["status"] == "in_progress":
                    check_suite_result.pending = True
            else:
                # if the state is not success or skipped we will decline the merge. The state can be
                # Can be one of: success, failure, neutral, cancelled, timed_out, action_required, stale, null, skipped, startup_failure
                if not (
                    check_suite["conclusion"] == "success"
                    or check_suite["conclusion"] == "skipped"
                ):
                    check_suite_result.success = False
                    check_suite_result.failed = True
                    message = f"Check suite {check_suite['app']['name']} is {check_suite['conclusion']}"
                    messages.append(message)
                    log.info(message)
    return check_suite_result


def merge_command(issue: Issue, settings: Settings) -> HttpResponse:
    log.debug(f"{issue.issue_number }: We have been called with the merge command")
    log.debug(f"{issue.issue_number }: Getting GitHub client")
    client = get_github_client(settings)
    pull_request = PullRequest.from_json(
        client.pull_request(
            issue.repo_owner, issue.repo_name, issue.issue_number
        ).json()
    )
    # Setup for this comment is done we ensured that this is address to us and we have a command

    log.info(f"{issue.issue_number }: Checking meragability")
    merge_stragies = [MaintainerUpdate(client, settings)]

    one_merge_strategy_passed = False
    decline_reasons = []
    for merge_stragy in merge_stragies:
        log.info(f"{issue.issue_number}: Running {merge_stragy} merge strategy")
        check, decline_reasons_strategy = merge_stragy.run(pull_request)
        decline_reasons.extend(decline_reasons_strategy)
        if check:
            one_merge_strategy_passed = True
    for reason in decline_reasons:
        log.info(f"{issue.issue_number}: {reason}")

    if one_merge_strategy_passed:
        log.info(
            f"{issue.issue_number }: A merge strategy passed we will notify the user with a rocket emoji"
        )
        client.create_issue_reaction(
            issue.repo_owner,
            issue.repo_name,
            issue.issue_number,
            issue.comment_id,
            "rocket",
        )
        check_suite_result = process_pull_request_status(client, pull_request)
        decline_reasons.extend(check_suite_result.messages)
        if check_suite_result.success:
            check_suite_result.success = False
            decline_reasons.append("Dry run bot")
            log.info(f"{issue.issue_number }: dry running aborting here")
        if check_suite_result.pending:
            db = Database(settings)
            db.add(pull_request.head_sha, str(issue.issue_number))
            msg = "One or more checks are still pending, we will wait for them to finish and if it succeeds we will merge this."
            log.info(f"{issue.issue_number}: {msg}")
            client.create_issue_comment(
                issue.repo_owner,
                issue.repo_name,
                issue.issue_number,
                msg,
            )
            return issue_response("merge-postponed")
        elif check_suite_result.success:
            try:
                log.info(f"{issue.issue_number }: Trying to merge pull request")
                client.merge_pull_request(
                    issue.repo_owner,
                    issue.repo_name,
                    issue.issue_number,
                    pull_request.head_sha,
                )
                log.info(f"{issue.issue_number }: Merge completed")
                client.create_issue_comment(
                    issue.repo_owner,
                    issue.repo_name,
                    issue.issue_number,
                    "Merge completed",
                )
                return issue_response("merged")
            except GithubClientError as e:
                log.exception(f"{issue.issue_number}: merge failed")
                decline_reasons.extend(
                    "\n".join(
                        [
                            f"@{issue.user_login} merge failed:",
                            "```",
                            f"{e.code} {e.reason}: {e.body}",
                            "```",
                        ]
                    )
                )

                client.create_issue_comment(
                    issue.repo_owner,
                    issue.repo_name,
                    issue.issue_number,
                    msg,
                )
                return issue_response("merge-failed")
        elif check_suite_result.failed:
            log.info(f"{issue.issue_number }: OfBorg failed, we let the user know")
            msg = f"@{issue.user_login} merge not permitted: \n"
            for reason in decline_reasons:
                msg += f"{reason}\n"

            log.info(msg)
            client.create_issue_comment(
                issue.repo_owner,
                issue.repo_name,
                issue.issue_number,
                msg,
            )
            return issue_response("not-permitted")
        else:
            msg = f"@{issue.user_login} merge not permitted: \n"
            for reason in decline_reasons:
                msg += f"{reason}\n"

            log.info(msg)
            client.create_issue_comment(
                issue.repo_owner,
                issue.repo_name,
                issue.issue_number,
                msg,
            )
            return issue_response("not-permitted")

    else:
        log.info(
            f"{issue.issue_number}: No merge stratgey passed, we let the user know"
        )
        msg = f"@{issue.user_login} merge not permitted: \n"
        for reason in decline_reasons:
            msg += f"{reason}\n"

        log.info(msg)
        client.create_issue_comment(
            issue.repo_owner,
            issue.repo_name,
            issue.issue_number,
            msg,
        )
        return issue_response("not-permitted")
