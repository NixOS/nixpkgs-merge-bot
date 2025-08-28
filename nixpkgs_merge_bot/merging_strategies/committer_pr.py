import logging
from typing import Final

from nixpkgs_merge_bot.github.issue import IssueComment
from nixpkgs_merge_bot.github.pull_request import PullRequest

from .merging_strategy import MergingStrategyTemplate

log = logging.getLogger(__name__)


class CommitterPR(MergingStrategyTemplate):
    allowed_branches: Final[frozenset[str]] = frozenset(
        [
            "master",
            "staging",
            "staging-next",
        ]
    )

    def run(
        self, pull_request: PullRequest, issue_comment: IssueComment
    ) -> tuple[bool, list[str]]:
        result, decline_reasons = self.run_technical_limits_check(pull_request)
        if not result:
            return result, decline_reasons

        committer_list = self.github_client.get_team_members(
            pull_request.repo_owner, self.settings.committer_team_slug
        )

        allowed_users = [committer["login"] for committer in committer_list]

        if pull_request.user_login not in allowed_users:
            result = False
            message = "CommitterPR: PR author is not a committer"
            decline_reasons.append(message)
            log.info(f"{pull_request.number}: {message}")
            return result, decline_reasons

        result, decline_reasons = self.run_maintainer_check(pull_request, issue_comment)

        if result:
            log.info(f"{pull_request.number}: CommitterPR accepted the merge")

        return result, decline_reasons
