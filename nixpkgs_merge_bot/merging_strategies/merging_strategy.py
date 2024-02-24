import logging

from nixpkgs_merge_bot.github.GitHubClient import GithubClient
from nixpkgs_merge_bot.settings import Settings

from ..github.PullRequest import PullRequest

log = logging.getLogger(__name__)


class MergingStrategyTemplate:
    def __init__(self, client: GithubClient, settings: Settings) -> None:
        self.github_client: GithubClient = client
        self.settings: Settings = settings

    def run_technical_limits_check(
        self, pull_request: PullRequest, commenter_id: int
    ) -> tuple[bool, list[str]]:
        result = True
        decline_reasons = []
        files_response = self.github_client.pull_request_files(
            pull_request.repo_owner, pull_request.repo_name, pull_request.number
        )
        body = files_response.json()
        sha = pull_request.head_sha
        log.info(
            f"{pull_request.number}: Checking mergeability of {pull_request.number} with sha {sha}"
        )

        if pull_request.state != "open":
            result = False
            message = f"pr is not open, state is {pull_request.state}"
            decline_reasons.append(message)
            log.info(f"{pull_request.number}: {message}")

        if pull_request.ref not in ("staging", "staging-next", "master"):
            result = False
            message = "pr is not targeted to any of the allowed branches: staging, staging-next, master"
            decline_reasons.append(message)
            log.info(f"{pull_request.number}: {message}")

        for file in body:
            filename = file["filename"]
            if not filename.startswith("pkgs/by-name/"):
                result = False
                message = f"{filename} is not in pkgs/by-name/"
                decline_reasons.append(message)
                log.info(f"{pull_request.number}: {message}")
        return result, decline_reasons

    def run(
        self, pull_request: PullRequest, commenter_id: int
    ) -> tuple[bool, list[str]]:
        # Analyze the pull request here
        # This is just a placeholder implementation
        raise NotImplementedError

    def __str__(self) -> str:
        return self.__class__.__name__
