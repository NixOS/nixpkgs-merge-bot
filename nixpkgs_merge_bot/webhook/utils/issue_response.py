import json

from nixpkgs_merge_bot.webhook.http_response import HttpResponse


def issue_response(action: str) -> HttpResponse:
    return HttpResponse(200, {}, json.dumps({"action": action}).encode("utf-8"))
