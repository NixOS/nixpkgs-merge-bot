import json
import logging
import socket
from http.server import BaseHTTPRequestHandler

from nixpkgs_merge_bot.settings import Settings

from . import http_header
from .check_run import check_run
from .errors import HttpError
from .issue_comment import issue_comment, review, review_comment
from .secret import WebhookSecret

log = logging.getLogger(__name__)


class GithubWebHook(BaseHTTPRequestHandler):
    def __init__(
        self,
        conn: socket.socket,
        addr: tuple[str, int],
        settings: Settings,
    ) -> None:
        self.rfile = conn.makefile("rb")
        self.wfile = conn.makefile("wb")
        self.client_address = addr
        self.secret = WebhookSecret(settings.webhook_secret)
        self.settings = settings
        self.client_address = (
            "",
            0,
        )  # avoid exception in BaseHTTPServer.py log_message() when using unix sockets
        self.handle()

    # for testing
    def do_GET(self) -> None:
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.send_header("Content-length", "2")
        self.end_headers()
        self.wfile.write(b"ok")

    def process_event(self, body: bytes) -> None:
        event_type = self.headers.get("X-Github-Event")
        if not event_type:
            log.error("X-Github-Event header missing")
            return self.send_error(400, explain="X-Github-Event header missing")
        payload = json.loads(body)
        log.info(f"event_type '{event_type}' was triggered")
        # TODO case "pull_request_review_comment":

        match event_type:
            case "issue_comment":
                handler = issue_comment
            case "check_run":
                handler = check_run
            case "check_suite":
                # unhandled
                return None
            case "pull_request_review_comment":
                handler = review_comment
            case "pull_request_review":
                handler = review
            case _:
                log.error(f"event_type '{event_type}' not registered")
                return self.send_error(
                    404, explain=f"event_type '{event_type}' not registered"
                )

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as e:
            log.exception("invalid json")
            return self.send_error(400, explain=f"invalid json: {e}")

        resp = handler(payload, self.settings)

        self.send_response(resp.code)
        for k, v in resp.headers.items():
            self.send_header(k, v)
        self.send_header("Content-length", str(len(resp.body)))
        self.end_headers()
        self.wfile.write(resp.body)
        return None

    def do_POST(self) -> None:
        content_type = self.headers.get("content-type", "")
        content_type, _ = http_header.parse_header(content_type)

        # refuse to receive non-json content
        if content_type != "application/json":
            return self.send_error(
                415, explain="Unsupported content-type: please use application/json"
            )

        length = int(self.headers.get("content-length", 0))
        body = self.rfile.read(length)

        try:
            if not self.secret.validate_signature(body, self.headers):
                log.debug("Invalid Signature")
                return self.send_error(403, explain="invalid signature")

            self.process_event(body)
        except HttpError as e:
            self.send_error(e.code, e.message)
        except Exception as e:
            log.exception("internal error")
            return self.send_error(500, explain=f"internal error: {e}")
