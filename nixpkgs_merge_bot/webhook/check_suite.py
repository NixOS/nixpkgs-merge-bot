import json
import logging
import sqlite3
from dataclasses import dataclass
from typing import Any

from ..github import GithubClientError, get_github_client
from ..settings import Settings
from .http_response import HttpResponse

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
    id: int
    latest_check_runs_count: int
    node_id: str
    pull_requests: list[dict[str, Any]]
    status: str
    updated_at: str
    url: str

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
        )


def check_suite_response(action: str) -> HttpResponse:
    return HttpResponse(200, {}, json.dumps({"action": action}).encode("utf-8"))


def check_suite(body: dict[str, Any], settings: Settings) -> HttpResponse:
    check_suite = CheckSuite.from_json(body)
    if check_suite.conclusion == "completed":
        con = sqlite3.connect(f"{settings.database_path}/nixpkgs_merge_bot.db")
        cur = con.cursor()
        cur.execute(
            """SELECT repo_owner, repo_name, github_id, pr_number, sha
                       FROM prs_to_merge
                       WHERE sha=?""",
            (check_suite.head_sha),
        )
        repo_owner, repo_name, github_user_id, issue_number, sha = cur.fetchone()
        con.close()
        if sha:
            client = get_github_client(settings)
            try:
                log.info("Trying to merge pull request after check suite completion")
                client.merge_pull_request(repo_owner, repo_name, issue_number, sha)
                log.info("Merge completed")
            except GithubClientError as e:
                log.exception("merge failed")
                msg = "\n".join(
                    [
                        f"@{github_user_id} merge failed:",
                        "```",
                        f"{e.code} {e.reason}: {e.body}",
                        "```",
                    ]
                )

                client.create_issue_comment(
                    repo_owner,
                    repo_name,
                    issue_number,
                    msg,
                )
                return check_suite_response("merge-failed")

            return check_suite_response("merged")
    return check_suite_response("success")
