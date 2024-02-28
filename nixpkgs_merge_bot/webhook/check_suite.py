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
class CheckSuite:
    after: str
    before: str
    check_runs_url: str
    conclusion: int
    created_at: str
    head_branch: str
    head_sha: str
    repo_name: str
    repo_owner: str
    id: int
    latest_check_runs_count: int
    node_id: str
    pull_requests: list[dict[str, Any]]
    status: str
    updated_at: str
    url: str
    app_name: str

    @staticmethod
    def from_json(body: dict[str, Any]) -> "CheckSuite":
        return CheckSuite(
            after=body["check_suite"]["after"],
            before=body["check_suite"]["before"],
            conclusion=body["check_suite"]["conclusion"],
            check_runs_url=body["check_suite"]["check_runs_url"],
            created_at=body["check_suite"]["created_at"],
            head_branch=body["check_suite"]["head_branch"],
            head_sha=body["check_suite"]["head_sha"],
            id=body["check_suite"]["id"],
            latest_check_runs_count=body["check_suite"]["latest_check_runs_count"],
            node_id=body["check_suite"]["node_id"],
            pull_requests=body["check_suite"]["pull_requests"],
            status=body["check_suite"]["status"],
            updated_at=body["check_suite"]["updated_at"],
            url=body["check_suite"]["url"],
            repo_name=body["repository"]["name"],
            repo_owner=body["repository"]["owner"]["login"],
            app_name=body["check_suite"]["app"]["name"],
        )


def check_suite_response(action: str) -> HttpResponse:
    return HttpResponse(200, {}, json.dumps({"action": action}).encode("utf-8"))


def check_suite(body: dict[str, Any], settings: Settings) -> HttpResponse:
    check_suite = CheckSuite.from_json(body)
    log.debug(
        f"Check Suite {check_suite.app_name} with commit id {check_suite.head_sha} is in state: {check_suite.status}"
    )
    if check_suite.conclusion == "completed":
        db = Database(settings)
        log.debug(
            f"Check Suite {check_suite.app_name} with commit id {check_suite.head_sha} is in state: {check_suite.status}"
        )
        values = db.get(check_suite.head_sha)
        for value in values:
            issue_number_str, commenter_id_str, commenter_login = value.split(";")
            issue_number = int(issue_number_str)
            log.debug(f"{issue_number}: Found pr for commit it {check_suite.head_sha}")
            commenter_id = int(commenter_id_str)
            client = get_github_client(settings)
            issue = IssueComment.from_issue_comment_json(
                client.get_issue(
                    check_suite.repo_owner, check_suite.repo_name, issue_number
                ).json()
            )
            issue.comment_id = commenter_id
            issue.commenter_login = commenter_login
            log.debug(f"{issue_number} Rerunning merge command for this")

            return merge_command(issue, settings)
    return check_suite_response("success")
