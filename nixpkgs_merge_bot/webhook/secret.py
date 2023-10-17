import hashlib
import hmac
from email.message import Message
from pathlib import Path

from .errors import HttpError


class WebhookSecret:
    def __init__(self, secret: Path) -> None:
        self.secret = secret.read_text().strip()

    def validate_signature(self, body: bytes, headers: Message) -> bool:
        # Get the signature from the payload
        signature_header = headers.get("X-Hub-Signature")
        if not signature_header:
            raise HttpError(401, "X-Hub-Signature header missing")
        sha_name, github_signature = signature_header.split("=")
        if sha_name != "sha1":
            raise HttpError(401, "X-Hub-Signature sha_name is not sha1")

        # Create our own signature
        local_signature = hmac.new(
            self.secret.encode("utf-8"),
            msg=body,
            digestmod=hashlib.sha1,
        )

        # See if they match
        return hmac.compare_digest(local_signature.hexdigest(), github_signature)
