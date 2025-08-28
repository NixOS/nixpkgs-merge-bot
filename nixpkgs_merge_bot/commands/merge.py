import logging
from dataclasses import dataclass

from nixpkgs_merge_bot.database import Database
from nixpkgs_merge_bot.github.github_client import (
    GithubClient,
    GithubClientError,
    get_github_client,
)
from nixpkgs_merge_bot.github.issue import IssueComment
from nixpkgs_merge_bot.github.pull_request import PullRequest
from nixpkgs_merge_bot.merging_strategies.backport import Backport
from nixpkgs_merge_bot.merging_strategies.committer_pr import CommitterPR
from nixpkgs_merge_bot.merging_strategies.maintainer_update import MaintainerUpdate
from nixpkgs_merge_bot.settings import Settings
from nixpkgs_merge_bot.webhook.http_response import HttpResponse
from nixpkgs_merge_bot.webhook.utils.issue_response import issue_response

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

    log.debug(f"{pull_request.number}: Getting check suites for commit")
    check_runs_for_commit = client.get_check_runs_for_commit(
        pull_request.repo_owner, pull_request.repo_name, pull_request.head_sha
    )
    for check_run in check_runs_for_commit.json()["check_runs"]:
        log.debug(
            f"{pull_request.number}: {check_run['name']} conclusion: {check_run['conclusion']} and status: {check_run['status']}"
        )
        # ofborg currently doesn't build anything, so we don't rely on it
        if check_run["app"]["id"] == 20500 and check_run["status"] in (
            "queued",
            "neutral",
        ):
            log.debug(f"{pull_request.number}: Ignoring ofborg")
            continue

        if check_run["status"] != "completed":
            message = f"Check run {check_run['name']} is not completed, we will wait for it to finish and if it succeeds we will merge this."
            check_run_result.messages.append(message)
            log.info(f"{pull_request.number}: {message}")
            check_run_result.success = False
            if check_run["status"] == "in_progress" or check_run["status"] == "queued":
                log.debug(f"{pull_request.number}: Check run is in progress or queued")
                check_run_result.pending = True
        # if the state is not success or skipped we will decline the merge. The state can be
        # Can be one of: success, failure, neutral, cancelled, timed_out, action_required, stale, null, skipped, startup_failure
        elif not (
            check_run["conclusion"] == "success"
            or check_run["conclusion"] == "skipped"
            or check_run["conclusion"] == "neutral"
        ):
            check_run_result.success = False
            check_run_result.failed = True
            message = f"Check suite {check_run['app']['name']} has the state: {check_run['conclusion']}"
            check_run_result.messages.append(message)
            log.info(f"{pull_request.number}: {message}")

    return check_run_result


def merge_command(issue_comment: IssueComment, settings: Settings) -> HttpResponse:
    log.debug(
        f"{issue_comment.issue_number}: We have been called with the merge command"
    )
    log.debug(f"{issue_comment.issue_number}: Getting GitHub client")
    client = get_github_client(settings)
    pull_request = PullRequest.from_json(
        client.pull_request(
            issue_comment.repo_owner,
            issue_comment.repo_name,
            issue_comment.issue_number,
        ).json()
    )
    # Setup for this comment is done we ensured that this is address to us and we have a command

    log.info(f"{issue_comment.issue_number}: Checking mergeability")
    merge_strategies = [
        MaintainerUpdate(client, settings),
        Backport(client, settings),
        CommitterPR(client, settings),
    ]
    log.info(
        f"{issue_comment.issue_number}: {len(merge_strategies)} merge strategies configured"
    )

    one_merge_strategy_passed = False
    decline_reasons = []
    for merge_strategy in merge_strategies:
        log.info(
            f"{issue_comment.issue_number}: Running {merge_strategy} merge strategy"
        )
        check, decline_reasons_strategy = merge_strategy.run(
            pull_request, issue_comment
        )
        decline_reasons.extend(decline_reasons_strategy)
        if check:
            one_merge_strategy_passed = True
            decline_reasons = []
            break
    for reason in decline_reasons:
        log.info(f"{issue_comment.issue_number}: {reason}")

    if one_merge_strategy_passed:
        log.info(
            f"{issue_comment.issue_number}: A merge strategy passed we will notify the user with a rocket emoji"
        )
        client.create_issue_reaction(
            issue_comment.repo_owner,
            issue_comment.repo_name,
            issue_comment.comment_id,
            "rocket",
            issue_comment.comment_type,
        )
        check_suite_result = process_pull_request_status(client, pull_request)
        decline_reasons.extend(check_suite_result.messages)
        log.info(decline_reasons)
        if check_suite_result.pending:
            db = Database(settings)
            db.add(
                pull_request.head_sha,
                f"{issue_comment.issue_number!s};{issue_comment.commenter_id};{issue_comment.commenter_login};{issue_comment.comment_id}",
            )
            msg = "One or more checks are still pending, I will retry this after they complete. Darwin checks can be ignored."
            log.info(f"{issue_comment.issue_number}: {msg}")
            client.create_issue_comment(
                issue_comment.repo_owner,
                issue_comment.repo_name,
                issue_comment.issue_number,
                msg,
            )
            return issue_response("merge-postponed")
        if check_suite_result.success:
            try:
                log.info(
                    f"{issue_comment.issue_number}: Trying to merge pull request, with head_sha: {pull_request.head_sha}"
                )
                client.merge_pull_request(
                    issue_comment.issue_number,
                    pull_request.node_id,
                    pull_request.head_sha,
                )
                merge_tracker_link = (
                    "Merge completed (#306934)"  # Link Issue to track merges
                )
                log.info(f"{issue_comment.issue_number}: {merge_tracker_link}")
                client.create_issue_comment(
                    issue_comment.repo_owner,
                    issue_comment.repo_name,
                    issue_comment.issue_number,
                    merge_tracker_link,
                )
                return issue_response("merged")
            except GithubClientError as e:
                log.exception(f"{issue_comment.issue_number}: merge failed")
                msg = "GitHub API error (#371492):"  # Link Issue to track errors
                decline_reasons.append(msg)
                decline_reasons.extend(
                    [
                        f"@{issue_comment.commenter_login} merge failed:",
                        "```",
                        f"{e.code} {e.reason}: {e.body}",
                        "```",
                    ]
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
                f"{issue_comment.issue_number}: OfBorg failed, we let the user know"
            )
            msg = f"@{issue_comment.commenter_login} merge not possible, check suite failed: \n"
            decline_reasons = list(set(decline_reasons))
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
            msg = f"@{issue_comment.commenter_login} merge not permitted. The check suite result is neither failed,success nor pending\n"
            decline_reasons = list(set(decline_reasons))
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
        msg = f"@{issue_comment.commenter_login} merge not permitted (#305350): \n"  # Link Issue to track failed merges
        decline_reasons = list(set(decline_reasons))
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
