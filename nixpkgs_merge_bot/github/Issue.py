from dataclasses import dataclass
from typing import Any


@dataclass
class IssueComment:
    commenter_id: int
    commenter_login: str
    text: str
    action: str
    comment_id: int
    repo_owner: str
    repo_name: str
    issue_number: int
    is_bot: bool
    title: str
    state: str

    @staticmethod
    def from_json(body: dict[str, Any]) -> "IssueComment":
        return IssueComment(
            action=body["action"],
            commenter_id=body["comment"]["user"]["id"],
            commenter_login=body["comment"]["user"]["login"],
            text=body["comment"]["body"],
            comment_id=body["comment"]["id"],
            repo_owner=body["repository"]["owner"]["login"],
            repo_name=body["repository"]["name"],
            issue_number=body["issue"]["number"],
            is_bot=body["comment"]["user"]["type"] == "Bot",
            title=body["issue"]["title"],
            state=body["issue"]["state"],
        )

    def __str__(self) -> str:
        return f"{self.issue_number}: Pull Request:  {self.title} by {self.commenter_login}"
