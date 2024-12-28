import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from pytest_mock import MockerFixture
from webhookclient import WebhookClient

from nixpkgs_merge_bot.settings import Settings
from nixpkgs_merge_bot.webhook.handler import GithubWebHook

TEST_ROOT = Path(__file__).parent
TEST_DATA = TEST_ROOT / "data"
DUMMY_NIXPKGS = TEST_ROOT / "nixpkgs"
DUMMY_NIXPKGS.mkdir(exist_ok=True)

SETTINGS = Settings(
    webhook_secret=TEST_DATA / "webhook-secret.txt",
    github_app_id=408064,
    github_app_login="nixpkgs-merge",
    github_app_private_key=TEST_DATA / "github_app_key.pem",
    restricted_authors=["r-ryantm"],
    repo_path=DUMMY_NIXPKGS,
)


def test_get(webhook_client: WebhookClient) -> None:
    client = webhook_client.http_connect()
    client.request("GET", "/")
    GithubWebHook(webhook_client.server_sock, webhook_client.addr, SETTINGS)
    response = client.getresponse()
    assert response.status == 200


def test_post_no_merge(webhook_client: WebhookClient) -> None:
    client = webhook_client.http_connect()
    create_event = (TEST_DATA / "issue_comment.no-merge.json").read_bytes()
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "issue_comment",
        "X-Hub-Signature": "sha1=f45b7e310e6e36f11c7e17bbca15dd31e6538956",
        "X-Hub-Signature-256": "sha256=286913f698705a38a157eb947acf716a32879c0eb8adf3a8e0155f2a6eb51960",
    }
    #
    client.request("POST", "/", body=create_event, headers=headers)
    GithubWebHook(webhook_client.server_sock, webhook_client.addr, SETTINGS)

    response = client.getresponse()
    response_body = json.loads(response.read().decode("utf-8"))
    assert response.status == 200, f"Response: {response.status}, {response_body}"
    assert response_body["action"] == "no-command"


@dataclass
class FakeHttpResponse:
    path: Path
    fake_headers: dict[str, str] = field(default_factory=dict)

    def json(self) -> Any:
        return json.loads(self.path.read_bytes())

    def headers(self) -> dict[str, str]:
        return self.fake_headers


def default_mocks(mocker: MockerFixture) -> dict[str, Any]:
    return {
        "nixpkgs_merge_bot.github.GitHubClient.GithubClient.app_installations": FakeHttpResponse(
            TEST_DATA / "app_installations.json"
        ),
        "nixpkgs_merge_bot.github.GitHubClient.GithubClient.create_installation_access_token": FakeHttpResponse(
            TEST_DATA / "installation_access_token.json"
        ),
        "nixpkgs_merge_bot.github.GitHubClient.GithubClient.pull_request": FakeHttpResponse(
            TEST_DATA / "pull_request.json"
        ),
        "nixpkgs_merge_bot.github.GitHubClient.GithubClient.merge_pull_request": FakeHttpResponse(
            TEST_DATA / "merge_pull_request.json"
        ),
        "nixpkgs_merge_bot.github.GitHubClient.GithubClient.pull_request_files": FakeHttpResponse(
            TEST_DATA / "pull_request_files.json"
        ),
        "nixpkgs_merge_bot.git.checkout_newest_master": "",
        "nixpkgs_merge_bot.nix.nix_utils.nix_eval": (
            TEST_DATA / "nix-eval.json"
        ).read_bytes(),
        "nixpkgs_merge_bot.github.GitHubClient.GithubClient.get_check_suites_for_commit": FakeHttpResponse(
            TEST_DATA / "get_check_suites_for_commit.json"
        ),
        "nixpkgs_merge_bot.github.GitHubClient.GithubClient.get_check_runs_for_commit": FakeHttpResponse(
            TEST_DATA / "get_check_run_for_commit.json"
        ),
        "nixpkgs_merge_bot.github.GitHubClient.GithubClient.create_issue_comment": FakeHttpResponse(
            TEST_DATA / "issue_comment.merge.json"
        ),  # unused
        "nixpkgs_merge_bot.github.GitHubClient.GithubClient.create_issue_reaction": FakeHttpResponse(
            TEST_DATA / "issue_comment.merge.json"
        ),  # unused
        "nixpkgs_merge_bot.github.GitHubClient.GithubClient.get_request_file_content": FakeHttpResponse(
            TEST_DATA / "pull_request_file_content.package.json"
        ),  # h
        "nixpkgs_merge_bot.github.GitHubClient.GithubClient.get_committer_list": json.load(
            open(TEST_DATA / "get_collaborators.json")
        ),
    }


def test_post_merge(webhook_client: WebhookClient, mocker: MockerFixture) -> None:
    for name, return_value in default_mocks(mocker).items():
        mocker.patch(name, return_value=return_value)

    client = webhook_client.http_connect()
    create_event = (TEST_DATA / "issue_comment.merge.json").read_bytes()
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "issue_comment",
        "X-Hub-Signature": "sha1=46879ac80229482672e9d7acde7b37834a49b8c3",
        "X-Hub-Signature-256": "sha256=53e04dda8e5d322028f7111eb9b92dc0056c8bc0bcb084edec7c9b87d594a4bb",
    }
    client.request("POST", "/", body=create_event, headers=headers)

    GithubWebHook(webhook_client.server_sock, webhook_client.addr, SETTINGS)

    response = client.getresponse()
    response_body = json.loads(response.read().decode("utf-8"))
    assert response.status == 200, f"Response: {response.status}, {response_body}"
    assert response_body["action"] == "merged"


@pytest.mark.parametrize(
    "mock_overrides",
    [
        {
            "nixpkgs_merge_bot.nix.nix_utils.nix_eval": (
                TEST_DATA / "nix-eval-no-maintainer.json"
            ).read_bytes()
        },
        {
            "nixpkgs_merge_bot.nix.nix_utils.nix_eval": (
                TEST_DATA / "nix-eval-wrong-maintainer.json"
            ).read_bytes()
        },
        {
            "nixpkgs_merge_bot.nix.nix_utils.nix_eval": (
                TEST_DATA / "nix-eval-wrong-maintainer.json"
            ).read_bytes()
        },
        {
            "nixpkgs_merge_bot.github.GitHubClient.GithubClient.pull_request_files": FakeHttpResponse(
                TEST_DATA / "pull_request_files.not-by-name.json"
            )
        },
    ],
)
def test_post_merge_maintainer(
    webhook_client: WebhookClient, mocker: MockerFixture, mock_overrides: dict[str, Any]
) -> None:
    mocks = default_mocks(mocker)
    mocks.update(mock_overrides)
    for name, return_value in mocks.items():
        mocker.patch(name, return_value=return_value)

    client = webhook_client.http_connect()
    create_event = (TEST_DATA / "issue_comment.merge.json").read_bytes()
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "issue_comment",
        "X-Hub-Signature": "sha1=46879ac80229482672e9d7acde7b37834a49b8c3",
        "X-Hub-Signature-256": "sha256=53e04dda8e5d322028f7111eb9b92dc0056c8bc0bcb084edec7c9b87d594a4bb",
    }
    client.request("POST", "/", body=create_event, headers=headers)

    GithubWebHook(webhook_client.server_sock, webhook_client.addr, SETTINGS)

    response = client.getresponse()
    response_body = json.loads(response.read().decode("utf-8"))
    assert response.status == 200, f"Response: {response.status}, {response_body}"
    assert response_body["action"] == "not-permitted"


@pytest.mark.parametrize(
    "mock_overrides",
    [
        {
            "nixpkgs_merge_bot.nix.nix_utils.nix_eval": (
                TEST_DATA / "nix-eval-no-maintainer.json"
            ).read_bytes()
        },
        {
            "nixpkgs_merge_bot.nix.nix_utils.nix_eval": (
                TEST_DATA / "nix-eval-wrong-maintainer.json"
            ).read_bytes()
        },
        {
            "nixpkgs_merge_bot.nix.nix_utils.nix_eval": (
                TEST_DATA / "nix-eval-wrong-maintainer.json"
            ).read_bytes()
        },
        {
            "nixpkgs_merge_bot.github.GitHubClient.GithubClient.pull_request_files": FakeHttpResponse(
                TEST_DATA / "pull_request_files.not-by-name.json"
            )
        },
    ],
)
def test_post_merge_maintainer_multiline(
    webhook_client: WebhookClient, mocker: MockerFixture, mock_overrides: dict[str, Any]
) -> None:
    mocks = default_mocks(mocker)
    mocks.update(mock_overrides)
    for name, return_value in mocks.items():
        mocker.patch(name, return_value=return_value)

    client = webhook_client.http_connect()
    create_event = (TEST_DATA / "issue_comment_multiline.merge.json").read_bytes()
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "issue_comment",
        "X-Hub-Signature": "sha1=eff1fea4ebf0cc443d53a499e2466904da8c3062",
        "X-Hub-Signature-256": "sha256=53e04dda8e5d322028f7111eb9b92dc0056c8bc0bcb084edec7c9b87d594a4bb",
    }
    client.request("POST", "/", body=create_event, headers=headers)

    GithubWebHook(webhook_client.server_sock, webhook_client.addr, SETTINGS)

    response = client.getresponse()
    response_body = json.loads(response.read().decode("utf-8"))
    assert response.status == 200, f"Response: {response.status}, {response_body}"
    assert response_body["action"] == "not-permitted"


@pytest.mark.parametrize(
    "mock_overrides",
    [
        {
            "nixpkgs_merge_bot.github.GitHubClient.GithubClient.get_request_file_content": FakeHttpResponse(
                TEST_DATA / "pull_request_file_content.large.json"
            )
        },
    ],
)
def test_post_merge_too_large_file(
    webhook_client: WebhookClient, mocker: MockerFixture, mock_overrides: dict[str, Any]
) -> None:
    mocks = default_mocks(mocker)
    mocks.update(mock_overrides)
    for name, return_value in mocks.items():
        mocker.patch(name, return_value=return_value)

    client = webhook_client.http_connect()
    create_event = (TEST_DATA / "issue_comment_multiline.merge.json").read_bytes()
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "issue_comment",
        "X-Hub-Signature": "sha1=eff1fea4ebf0cc443d53a499e2466904da8c3062",
        "X-Hub-Signature-256": "sha256=53e04dda8e5d322028f7111eb9b92dc0056c8bc0bcb084edec7c9b87d594a4bb",
    }
    client.request("POST", "/", body=create_event, headers=headers)

    SETTINGS.max_file_size_mb = 1
    GithubWebHook(webhook_client.server_sock, webhook_client.addr, SETTINGS)

    response = client.getresponse()
    response_body = json.loads(response.read().decode("utf-8"))
    assert response.status == 200, f"Response: {response.status}, {response_body}"
    assert response_body["action"] == "not-permitted"
