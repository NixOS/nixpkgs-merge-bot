import json
import logging
import re
from dataclasses import dataclass
from typing import Any

from ..github import GithubClientError, get_github_client
from ..nix import merge_check
from ..settings import Settings
from .http_response import HttpResponse

log = logging.getLogger(__name__)


@dataclass
class Issue:
    user_id: int
    user_login: str
    text: str
    action: str
    comment_id: int
    repo_owner: str
    repo_name: str
    issue_number: int
    is_bot: bool

    @staticmethod
    def from_json(body: dict[str, Any]) -> "Issue":
        return Issue(
            action=body["action"],
            user_id=body["comment"]["user"]["id"],
            user_login=body["comment"]["user"]["login"],
            text=body["comment"]["body"],
            comment_id=body["comment"]["id"],
            repo_owner=body["repository"]["owner"]["login"],
            repo_name=body["repository"]["name"],
            issue_number=body["issue"]["number"],
            is_bot=body["comment"]["user"]["type"] == "Bot",
        )


def issue_response(action: str) -> HttpResponse:
    return HttpResponse(200, {}, json.dumps({"action": action}).encode("utf-8"))


def issue_comment(body: dict[str, Any], settings: Settings) -> HttpResponse:
    issue = Issue.from_json(body)
    log.debug(f"issue_comment: {issue}")

    # ignore our own comments and comments from other bots (security)
    if issue.is_bot:
        log.debug("ignoring event as it is from a bot")
        return issue_response("ignore-bot")
    if not body["issue"].get("pull_request"):
        log.debug("ignoring event as it is not a pull request")
        return issue_response("ignore-not-pr")

    if issue.action not in ("created", "edited"):
        log.debug("ignoring event as actions is not created or edited")
        return issue_response("ignore-action")

    stripped = re.sub("(<!--.*?-->)", "", issue.text, flags=re.DOTALL)
    bot_name = re.escape(settings.bot_name)
    if not re.match(rf"@{bot_name}\s+merge", stripped):
        log.debug("no command was found in comment")
        return issue_response("no-command")

    log.debug("getting github client")
    client = get_github_client(settings)
    log.info("Checking meragability")
    check = merge_check(
        client,
        issue.repo_owner,
        issue.repo_name,
        issue.issue_number,
        issue.user_id,
        settings,
    )
    log.info("Creating issue reaction")
    client.create_issue_reaction(
        issue.repo_owner,
        issue.repo_name,
        issue.issue_number,
        issue.comment_id,
        "rocket",
    )
    if not check.permitted:
        msg = f"@{issue.user_login} merge not permitted: \n"
        for reason in check.decline_reasons:
            msg += f"{reason}\n"

        log.info(msg)
        client.create_issue_comment(
            issue.repo_owner,
            issue.repo_name,
            issue.issue_number,
            msg,
        )
        return issue_response("not-permitted")

    try:
        log.info("Trying to merge pull request")
        client.merge_pull_request(
            issue.repo_owner, issue.repo_name, issue.issue_number, check.sha
        )
        log.info("Merge completed")
    except GithubClientError as e:
        log.exception("merge failed")
        msg = "\n".join(
            [
                f"@{issue.user_login} merge failed:",
                "```",
                f"{e.code} {e.reason}: {e.body}",
                "```",
            ]
        )

        client.create_issue_comment(
            issue.repo_owner,
            issue.repo_name,
            issue.issue_number,
            msg,
        )
        return issue_response("merge-failed")

    return issue_response("merge")
