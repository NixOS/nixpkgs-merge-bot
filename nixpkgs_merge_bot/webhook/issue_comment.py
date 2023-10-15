from typing import Any

from .http_response import HttpResponse


def issue_comment(body: dict[str, Any]) -> HttpResponse:
    return HttpResponse(200, {}, b"ok")
