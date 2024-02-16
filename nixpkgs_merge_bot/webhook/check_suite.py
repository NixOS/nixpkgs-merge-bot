import json
import logging
from dataclasses import dataclass
from typing import Any

from ..settings import Settings
from .http_response import HttpResponse

logger = logging.getLogger(__name__)


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
    print(check_suite)
    return check_suite_response("success")
