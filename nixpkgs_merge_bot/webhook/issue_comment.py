import logging
import re
from typing import Any

from ..commands.merge import merge_command
from ..github.Issue import Issue
from ..settings import Settings
from .http_response import HttpResponse
from .utils.issue_response import issue_response

log = logging.getLogger(__name__)


def issue_comment(body: dict[str, Any], settings: Settings) -> HttpResponse:
    issue = Issue.from_json(body)
    log.debug(issue)
    # ignore our own comments and comments from other bots (security)
    if issue.is_bot:
        log.debug(f"{issue.issue_number}: ignoring event as it is from a bot")
        return issue_response("ignore-bot")
    if not body["issue"].get("pull_request"):
        log.debug(f"{issue.issue_number}: ignoring event as it is not a pull request")
        return issue_response("ignore-not-pr")

    if issue.action not in ("created", "edited"):
        log.debug(
            f"{issue.issue_number}: ignoring event as actions is not created or edited"
        )
        return issue_response("ignore-action")

    stripped = re.sub("(<!--.*?-->)", "", issue.text, flags=re.DOTALL)
    bot_name = re.escape(settings.bot_name)
    if re.match(rf"@{bot_name}\s+merge", stripped):
        return merge_command(issue, settings)
    else:
        log.debug(f"{issue.issue_number}: no command was found in comment")
        return issue_response("no-command")
