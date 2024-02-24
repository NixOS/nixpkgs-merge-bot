import logging
from typing import Any

from ..settings import Settings
from .http_response import HttpResponse
from .utils.issue_response import issue_response

log = logging.getLogger(__name__)


def review_comment(body: dict[str, Any], settings: Settings) -> HttpResponse:
    print(body)
    return issue_response("no-command")
