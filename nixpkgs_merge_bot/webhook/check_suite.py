import json
import logging
from dataclasses import dataclass
from typing import Any

from ..database import Database
from ..github.GitHubClient import get_github_client
from ..github.Issue import IssueComment
from ..settings import Settings
from .http_response import HttpResponse
from .issue_comment import merge_command

log = logging.getLogger(__name__)


@dataclass
class CheckRun:
    conclusion: int
    head_sha: str
    repo_name: str
    repo_owner: str
    id: int
    node_id: str
    name: str
    status: str
    pull_requests: list[dict[str, Any]]

    @staticmethod
    def from_json(body: dict[str, Any]) -> "CheckRun":
        return CheckRun(
            conclusion=body["check_run"]["conclusion"],
            head_sha=body["check_run"]["head_sha"],
            id=body["check_run"]["id"],
            node_id=body["check_run"]["node_id"],
            pull_requests=body["check_run"]["pull_requests"],
            status=body["check_run"]["status"],
            repo_name=body["repository"]["name"],
            repo_owner=body["repository"]["owner"]["login"],
            name=body["check_run"]["name"],
        )


def check_run_response(action: str) -> HttpResponse:
    return HttpResponse(200, {}, json.dumps({"action": action}).encode("utf-8"))


def check_run(body: dict[str, Any], settings: Settings) -> HttpResponse:
    check_run = CheckRun.from_json(body)
    log.debug(
        f"Check Run {check_run.name} with commit id {check_run.head_sha} is in state: {check_run.status}"
    )
    if check_run.conclusion == "completed":
        db = Database(settings)
        log.debug(
            f"Check Run {check_run.name} with commit id {check_run.head_sha} is in state: {check_run.status}"
        )
        values = db.get(check_run.head_sha)
        for value in values:
            issue_number_str, commenter_id_str, commenter_login = value.split(";")
            issue_number = int(issue_number_str)
            log.debug(f"{issue_number}: Found pr for commit it {check_run.head_sha}")
            commenter_id = int(commenter_id_str)
            client = get_github_client(settings)
            issue = IssueComment.from_issue_comment_json(
                client.get_issue(
                    check_run.repo_owner, check_run.repo_name, issue_number
                ).json()
            )
            issue.comment_id = commenter_id
            issue.commenter_login = commenter_login
            log.debug(f"{issue_number} Rerunning merge command for this")

            return merge_command(issue, settings)
    return check_run_response("success")
