import logging
from dataclasses import dataclass
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class IssueComment:
    commenter_id: int
    commenter_login: str
    text: str
    action: str
    comment_id: int
    comment_type: str
    repo_owner: str
    repo_name: str
    issue_number: int
    is_bot: bool
    title: str
    state: str
    is_pull_request: bool = True

    @staticmethod
    def from_issue_comment_json(body: dict[str, Any]) -> "IssueComment":
        try:
            if body["issue"]["pull_request"] is not None:
                is_pull_request = True
            else:
                is_pull_request = False
        except KeyError:
            is_pull_request = False

        try:
            if body["action"] is not None:
                action = body["action"]
            else:
                action = "created"
        except KeyError:
            action = "created"

        try:
            return IssueComment(
                action=action,
                commenter_id=body["comment"]["user"]["id"],
                commenter_login=body["comment"]["user"]["login"],
                text=body["comment"]["body"],
                comment_id=body["comment"]["id"],
                comment_type="issue_comment",
                repo_owner=body["repository"]["owner"]["login"],
                repo_name=body["repository"]["name"],
                issue_number=body["issue"]["number"],
                is_bot=body["comment"]["user"]["type"] == "Bot",
                title=body["issue"]["title"],
                state=body["issue"]["state"],
                is_pull_request=is_pull_request,
            )
        except KeyError as e:
            log.debug(e)
            log.debug(body)
            raise e

    @staticmethod
    def from_review_comment_json(body: dict[str, Any]) -> "IssueComment":
        try:
            return IssueComment(
                action=body["action"],
                commenter_id=body["comment"]["user"]["id"],
                commenter_login=body["comment"]["user"]["login"],
                text=body["comment"]["body"],
                comment_id=body["comment"]["id"],
                comment_type="review_comment",
                repo_owner=body["repository"]["owner"]["login"],
                repo_name=body["repository"]["name"],
                issue_number=body["pull_request"]["number"],
                is_bot=body["comment"]["user"]["type"] == "Bot",
                title=body["pull_request"]["title"],
                state=body["pull_request"]["state"],
            )
        except KeyError as e:
            log.debug(e)
            log.debug(body)
            raise e

    @staticmethod
    def from_review_json(body: dict[str, Any]) -> "IssueComment":
        try:
            log.debug(body)
            return IssueComment(
                action=body["action"],
                commenter_id=body["review"]["user"]["id"],
                commenter_login=body["review"]["user"]["login"],
                text=body["review"]["body"],
                comment_id=body["review"]["id"],
                comment_type="review",
                repo_owner=body["repository"]["owner"]["login"],
                repo_name=body["repository"]["name"],
                issue_number=body["pull_request"]["number"],
                is_bot=body["review"]["user"]["type"] == "Bot",
                title=body["pull_request"]["title"],
                state=body["pull_request"]["state"],
            )
        except KeyError as e:
            log.debug(e)
            log.debug(body)
            raise e

    def __str__(self) -> str:
        return f"{self.issue_number}: Pull Request:  {self.title} by {self.commenter_login}"
