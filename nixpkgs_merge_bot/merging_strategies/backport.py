import logging
from pathlib import Path

from nixpkgs_merge_bot.github.issue import IssueComment
from nixpkgs_merge_bot.github.pull_request import PullRequest
from nixpkgs_merge_bot.nix.nix_utils import get_package_maintainers, is_maintainer

from .merging_strategy import MergingStrategyTemplate

log = logging.getLogger(__name__)


class Backport(MergingStrategyTemplate):
    def run(
        self, pull_request: PullRequest, issue_comment: IssueComment
    ) -> tuple[bool, list[str]]:
        result, decline_reasons = self.run_technical_limits_check(
            pull_request, allowed_branches=["release-25.05", "staging-25.05"]
        )
        if not result:
            return result, decline_reasons

        allowed_users = ["nixpkgs-ci[bot]"]
        if pull_request.user_login not in allowed_users:
            result = False
            message = "Backport merge: pr author is not nixpkgs-ci"
            decline_reasons.append(message)
            log.info(f"{pull_request.number}: {message}")
        else:
            files_response = self.github_client.pull_request_files(
                pull_request.repo_owner,
                pull_request.repo_name,
                pull_request.number,
            )
            body = files_response.json()
            for file in body:
                filename = file["filename"]
                maintainers = get_package_maintainers(self.settings, Path(filename))
                if not is_maintainer(issue_comment.commenter_id, maintainers):
                    result = False
                    message = (
                        f"Backport merge: {issue_comment.commenter_login} is not a package maintainer, valid maintainers are: "
                        + ", ".join(m.name for m in maintainers)
                    )
                    decline_reasons.append(message)
                    log.info(f"{pull_request.number}: {message}")

        return result, decline_reasons
