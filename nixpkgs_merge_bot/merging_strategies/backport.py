import logging
from typing import Final

from nixpkgs_merge_bot.github.issue import IssueComment
from nixpkgs_merge_bot.github.pull_request import PullRequest

from .merging_strategy import MergingStrategyTemplate

log = logging.getLogger(__name__)


class Backport(MergingStrategyTemplate):
    allowed_branches: Final[frozenset[str]] = frozenset(
        [
            "release-25.05",
            "staging-25.05",
            "staging-next-25.05",
        ]
    )
    allowed_user: Final[str] = "nixpkgs-ci[bot]"

    def run(
        self, pull_request: PullRequest, issue_comment: IssueComment
    ) -> tuple[bool, list[str]]:
        result, decline_reasons = self.run_technical_limits_check(pull_request)
        if not result:
            return result, decline_reasons

        if pull_request.user_login != self.allowed_user:
            result = False
            message = f"Backport: PR author is not {self.allowed_user}"
            decline_reasons.append(message)
            log.info(f"{pull_request.number}: {message}")

        result, decline_reasons = self.run_maintainer_check(pull_request, issue_comment)

        if result:
            log.info(f"{pull_request.number}: Backport accepted the merge")

        return result, decline_reasons
