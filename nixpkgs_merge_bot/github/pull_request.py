import logging
from dataclasses import dataclass
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class PullRequest:
    user_id: int
    user_login: str
    text: str
    repo_owner: str
    repo_name: str
    number: int
    title: str
    state: str
    head_sha: str
    ref: str

    @staticmethod
    def from_json(body: dict[str, Any]) -> "PullRequest":
        try:
            return PullRequest(
                user_id=body["user"]["id"],
                user_login=body["user"]["login"],
                text=body["body"],
                repo_owner=body["base"]["repo"]["owner"]["login"],
                repo_name=body["base"]["repo"]["name"],
                number=body["number"],
                title=body["title"],
                state=body["state"],
                head_sha=body["head"]["sha"],
                ref=body["base"]["ref"],
            )
        except KeyError as e:
            log.debug(e)
            log.debug(body)
            raise

    def __str__(self) -> str:
        return f"Pull Request: {self.title} by {self.user_login} with head sha {self.head_sha} "
