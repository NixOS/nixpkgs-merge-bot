import logging
from pathlib import Path
from typing import Final

from nixpkgs_merge_bot.github.issue import IssueComment
from nixpkgs_merge_bot.github.pull_request import PullRequest
from nixpkgs_merge_bot.nix.nix_utils import get_package_maintainers, is_maintainer

from .merging_strategy import MergingStrategyTemplate

log = logging.getLogger(__name__)


class MaintainerUpdate(MergingStrategyTemplate):
    allowed_branches: Final[frozenset[str]] = [
        "master",
        "staging",
        "staging-next",
    ]
    allowed_user: Final[str] = "r-ryantm"

    def run(
        self, pull_request: PullRequest, issue_comment: IssueComment
    ) -> tuple[bool, list[str]]:
        result, decline_reasons = self.run_technical_limits_check(pull_request)
        if not result:
            return result, decline_reasons

        if pull_request.user_login != self.allowed_user:
            result = False
            message = f"MaintainerUpdate: pr author is not {self.allowed_user}"
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
                        f"MaintainerUpdate: {issue_comment.commenter_login} is not a package maintainer, valid maintainers are: "
                        + ", ".join(m.name for m in maintainers)
                    )
                    decline_reasons.append(message)
                    log.info(f"{pull_request.number}: {message}")

        return result, decline_reasons
