from pathlib import Path

from webhookclient import WebhookClient

from nixpkgs_merge_bot.webhook.handler import GithubWebHook

TEST_ROOT = Path(__file__).parent
TEST_DATA = TEST_ROOT / "data"


def test_get(webhook_client: WebhookClient) -> None:
    client = webhook_client.http_connect()
    client.request("GET", "/")
    GithubWebHook(webhook_client.server_sock, webhook_client.addr, "foo")
    response = client.getresponse()
    assert response.status == 200


def test_post(webhook_client: WebhookClient) -> None:
    client = webhook_client.http_connect()
    create_event = (TEST_DATA / "issue_comment.created.json").read_bytes()
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "issue_comment",
        "X-Hub-Signature": "sha1=f45b7e310e6e36f11c7e17bbca15dd31e6538956",
        "X-Hub-Signature-256": "sha256=286913f698705a38a157eb947acf716a32879c0eb8adf3a8e0155f2a6eb51960",
    }
    #
    client.request("POST", "/", body=create_event, headers=headers)

    GithubWebHook(webhook_client.server_sock, webhook_client.addr, "foo")

    response = client.getresponse()
    response_body = response.read().decode("utf-8")
    assert response.status == 200, f"Response: {response.status}, {response_body}"
