import logging
from pathlib import Path

from ..github.PullRequest import PullRequest
from ..nix.nix_utils import get_package_maintainers, is_maintainer
from .merging_strategy import MergingStrategyTemplate

log = logging.getLogger(__name__)


class MaintainerUpdate(MergingStrategyTemplate):
    def run(
        self, pull_request: PullRequest, commenter_id: int
    ) -> tuple[bool, list[str]]:
        # Analyze the pull request here
        # This is just a placeholder implementation
        result, decline_reasons = self.run_technical_limits_check(
            pull_request, commenter_id
        )
        if not result:
            return result, decline_reasons

        allowed_users = ["r-ryantm"]
        if pull_request.user_login not in allowed_users:
            result = False
            message = f"pr author is not in restricted authors list, in the list are: {','.join(allowed_users)}"
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
                if not is_maintainer(commenter_id, maintainers):
                    result = False
                    message = (
                        f"github id: {commenter_id} is not in maintainers, valid maintainers are: "
                        + ", ".join(m.name for m in maintainers)
                    )
                    decline_reasons.append(message)
                    log.info(f"{pull_request.number}: {message}")

        return result, decline_reasons
