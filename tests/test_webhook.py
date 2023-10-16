import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from webhookclient import WebhookClient

from nixpkgs_merge_bot.settings import Settings
from nixpkgs_merge_bot.webhook.handler import GithubWebHook

TEST_ROOT = Path(__file__).parent
TEST_DATA = TEST_ROOT / "data"

SETTINGS = Settings(
    webhook_secret="foo",
    github_app_id=408064,
    github_app_login="nixpkgs-merge",
    github_app_private_key=str(TEST_DATA / "github_app_key.pem"),
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


def test_post_merge(webhook_client: WebhookClient, mocker) -> None:
    mock = mocker.patch("nixpkgs_merge_bot.github.GithubClient.app_installations")
    mock.return_value = FakeHttpResponse(TEST_DATA / "app_installations.json")

    mock = mocker.patch(
        "nixpkgs_merge_bot.github.GithubClient.create_installation_access_token"
    )
    mock.return_value = FakeHttpResponse(TEST_DATA / "installation_access_token.json")

    mock = mocker.patch("nixpkgs_merge_bot.github.GithubClient.pull_request")
    mock.return_value = FakeHttpResponse(TEST_DATA / "pull_request.json")

    mock = mocker.patch("nixpkgs_merge_bot.github.GithubClient.merge_pull_request")
    mock.return_value = FakeHttpResponse(TEST_DATA / "merge_pull_request.json")


    mock = mocker.patch("nixpkgs_merge_bot.github.GithubClient.pull_request_files")
    mock.return_value = FakeHttpResponse(TEST_DATA / "pull_request_files.json")

    mock = mocker.patch("nixpkgs_merge_bot.github.GithubClient.create_issue_comment")
    mock.return_value = FakeHttpResponse(TEST_DATA / "create_issue_comment.json") # unused

    mock = mocker.patch("nixpkgs_merge_bot.github.GithubClient.create_issue_reaction")
    mock.return_value = FakeHttpResponse(TEST_DATA / "create_issue_reaction.json") # unused

    client = webhook_client.http_connect()
    create_event = (TEST_DATA / "issue_comment.merge.json").read_bytes()
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "issue_comment",
        "X-Hub-Signature": "sha1=e95fecb50e56ce292855e84d129449d39bb1cdd7",
        "X-Hub-Signature-256": "sha256=53e04dda8e5d322028f7111eb9b92dc0056c8bc0bcb084edec7c9b87d594a4bb",
    }
    client.request("POST", "/", body=create_event, headers=headers)

    GithubWebHook(webhook_client.server_sock, webhook_client.addr, SETTINGS)

    response = client.getresponse()
    response_body = json.loads(response.read().decode("utf-8"))
    assert response.status == 200, f"Response: {response.status}, {response_body}"
    breakpoint()
    assert response_body["action"] == "merge"
