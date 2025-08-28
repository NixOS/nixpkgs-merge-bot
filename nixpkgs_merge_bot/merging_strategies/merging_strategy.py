import logging
from abc import ABC, abstractmethod
from typing import Any, ClassVar
from urllib.parse import urlparse

from nixpkgs_merge_bot.github.github_client import GithubClient
from nixpkgs_merge_bot.github.issue import IssueComment
from nixpkgs_merge_bot.github.pull_request import PullRequest
from nixpkgs_merge_bot.settings import Settings

log = logging.getLogger(__name__)


class MergingStrategyTemplate(ABC):
    allowed_branches: ClassVar[frozenset[str]]
    allowed_user: ClassVar[str]

    def __init__(self, client: GithubClient, settings: Settings) -> None:
        self.github_client: GithubClient = client
        self.settings: Settings = settings

    def run_technical_limits_check(
        self,
        pull_request: PullRequest,
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
            message = f"PR is not open, state is {pull_request.state}"
            decline_reasons.append(message)
            log.info(f"{pull_request.number}: {message}")

        if pull_request.ref not in self.allowed_branches:
            result = False
            message = f"PR is not targeting any of the allowed branches: {', '.join(self.allowed_branches)}"
            decline_reasons.append(message)
            log.info(f"{pull_request.number}: {message}")

        for file in body:
            filename = file["filename"]
            file_size_bytes = self.get_file_size_bytes(pull_request, file)
            if file_size_bytes > self.settings.max_file_size_bytes:
                result = False
                message = f"{filename} exceeds the maximum allowed file size of {self.settings.max_file_size_mb} MB"
                decline_reasons.append(message)
            if not filename.startswith("pkgs/by-name/"):
                result = False
                message = f"{filename} is not in pkgs/by-name/"
                decline_reasons.append(message)
                log.info(f"{pull_request.number}: {message}")
        return result, decline_reasons

    def get_file_size_bytes(
        self, pull_request: PullRequest, file: dict[str, Any]
    ) -> int:
        file_contents_url = urlparse(file["contents_url"])
        response = self.github_client.get_request_file_content(
            pull_request.repo_owner,
            pull_request.repo_name,
            file["filename"],
            file_contents_url.query,
        )
        return response.json()["size"]

    @abstractmethod
    def run(
        self, pull_request: PullRequest, comment: IssueComment
    ) -> tuple[bool, list[str]]:
        # Analyze the pull request here
        # This is just a placeholder implementation
        raise NotImplementedError

    def __str__(self) -> str:
        return self.__class__.__name__
