import logging
from pathlib import Path

from ..github.PullRequest import PullRequest
from ..nix.nix_utils import get_package_maintainers, is_maintainer
from .merging_strategy import MergingStrategyTemplate
from ..github.Issue import IssueComment

log = logging.getLogger(__name__)


class CommitterPR(MergingStrategyTemplate):
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

        committer_list = self.github_client.get_committer_list(
            pull_request.repo_owner, self.settings.committer_team_slug
        )

        allowed_users = [
            committer["login"]
            for committer in committer_list
        ]

        if pull_request.user_login not in allowed_users:
            result = False
            message = "CommitterPR: pr author is not committer"
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
                            f"CommitterPR: {issue_comment.commenter_login} is not a package maintainer, valid maintainers are: "
                        + ", ".join(m.name for m in maintainers)
                    )
                    decline_reasons.append(message)
                    log.info(f"{pull_request.number}: {message}")
            if result:
                log.info(f"{pull_request.number}: CommitterPR accepted the merge")


        return result, decline_reasons
