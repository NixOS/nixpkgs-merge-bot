#!/usr/bin/env python3

import argparse
import base64
import http.client
import json
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def rs256_sign(data: str, private_key: Path) -> str:
    signature = subprocess.run(
        ["openssl", "dgst", "-binary", "-sha256", "-sign", private_key],
        input=data.encode("utf-8"),
        stdout=subprocess.PIPE,
        check=True,
    ).stdout
    return base64url(signature)


def build_jwt_payload(app_id: int) -> dict[str, Any]:
    jwt_iat_drift = 60
    jwt_exp_delta = 600
    now = int(time.time())
    iat = now - jwt_iat_drift
    jwt_payload = {"iat": iat, "exp": iat + jwt_exp_delta, "iss": str(app_id)}
    return jwt_payload


class HttpResponse:
    def __init__(self, raw: http.client.HTTPResponse) -> None:
        self.raw = raw

    def json(self) -> Any:
        return json.load(self.raw)

    def headers(self) -> http.client.HTTPMessage:
        return self.raw.headers


class GithubClient:
    def __init__(self, api_token: str | None) -> None:
        self.api_token = api_token

    def _request(
        self,
        path: str,
        method: str,
        data: dict[str, Any] | None = None,
        headers: dict[str, str] = {},
    ) -> Any:
        url = urllib.parse.urljoin("https://api.github.com/", path)
        headers = headers.copy()
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        headers["User-Agent"] = "nixpkgs-merge-bot"

        body = None
        if data:
            body = json.dumps(data).encode("ascii")

        req = urllib.request.Request(url, headers=headers, method=method, data=body)
        try:
            resp = urllib.request.urlopen(req)
        except urllib.request.HTTPError as e:
            resp_body = ""
            try:
                resp_body = e.fp.read().decode("utf-8", "replace")
            except Exception:
                pass
            raise Exception(
                f"Request for {method} {url} failed with {e.code} {e.reason}: {resp_body}"
            ) from e
        return HttpResponse(resp)

    def get(self, path: str) -> Any:
        return self._request(path, "GET")

    def post(self, path: str, data: dict[str, str]) -> Any:
        return self._request(path, "POST", data)

    def put(self, path: str) -> Any:
        return self._request(path, "PUT")

    def app_installations(self) -> Any:
        return self.get("/app/installations")

    def pull_request_files(self, owner: str, repo: str, pr_number: int) -> Any:
        return self.get(f"/repos/{owner}/{repo}/pulls/{pr_number}/files")


def request_access_token(app_login: str, app_id: int, app_private_key: Path) -> str:
    jwt_payload = json.dumps(build_jwt_payload(app_id)).encode("utf-8")
    json_headers = json.dumps({"alg": "RS256", "typ": "JWT"}).encode("utf-8")
    encoded_jwt_parts = f"{base64url(json_headers)}.{base64url(jwt_payload)}"
    encoded_mac = rs256_sign(encoded_jwt_parts, app_private_key)
    generated_jwt = f"{encoded_jwt_parts}.{encoded_mac}"

    client = GithubClient(generated_jwt)
    response = client.app_installations()

    access_token_url = None
    for item in response.json():
        if item["account"]["login"] == app_login and item["app_id"] == app_id:
            access_token_url = item["access_tokens_url"]
            break
    if not access_token_url:
        raise ValueError("Access token URL not found")

    resp = client.post(access_token_url, data={}).json()
    return resp["token"]


def main() -> None:
    parser = argparse.ArgumentParser(description="Get Github App Token")
    parser.add_argument(
        "--login",
        type=str,
        help="User or organization name that installed the app",
        required=True,
    )
    parser.add_argument("--app-id", type=int, help="Github App ID", required=True)
    parser.add_argument(
        "--app-private-key-file", type=str, help="Github App Private Key", required=True
    )
    args = parser.parse_args()
    app_private_key = Path(args.app_private_key_file)
    token = request_access_token(args.login, args.app_id, app_private_key)
    print(token)


if __name__ == "__main__":
    main()
