import logging
from pathlib import Path

from ..github.Issue import IssueComment
from ..github.PullRequest import PullRequest
from ..nix.nix_utils import get_package_maintainers, is_maintainer
from .merging_strategy import MergingStrategyTemplate

log = logging.getLogger(__name__)


class CommitterMerge(MergingStrategyTemplate):
    def run(
        self, pull_request: PullRequest, issue_comment: IssueComment
    ) -> tuple[bool, list[str]]:
        # Analyze the pull request here
        # This is just a placeholder implementation
        result, decline_reasons = self.run_technical_limits_check(
            pull_request, issue_comment.commenter_id
        )
        if not result:
            return result, decline_reasons

        committer_list = self.github_client.get_team_members(
            pull_request.repo_owner, self.settings.committer_team_slug
        )

        allowed_users = [committer["id"] for committer in committer_list]
        if not issue_comment.commenter_id in allowed_users:
            result = False
            message = (
                f"CommitterMerge: {issue_comment.commenter_login} is not in the NixOS nixpkgs-committer team."
            )
            decline_reasons.append(message)
            log.info(f"{pull_request.number}: {message}")
        if result:
            log.info(f"{pull_request.number}: CommitterMerge accepted the merge")


        return result, decline_reasons
