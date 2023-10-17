import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .github import GithubClient
from .settings import Settings


@dataclass
class MergeResponse:
    permitted: bool
    decline_reasons: dict[str, str]
    sha: str


@dataclass
class Maintainer:
    github_id: int
    name: str


def nix_eval(url: str) -> bytes:
    proc = subprocess.run(
        [
            "nix",
            "eval",
            "--experimental-features",
            "nix-command flakes",
            "--refresh",
            "--json",
            url,
        ],
        check=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    return proc.stdout


def get_package_maintainers(path: Path) -> list[Maintainer]:
    package_name = path.parts[3]
    # TODO maybe we want to check the merge target remote here?
    proc = nix_eval(f"github:nixos/nixpkgs/master#{package_name}.meta.maintainers")
    maintainers = json.loads(proc.decode("utf-8"))
    return [
        Maintainer(maintainer["githubId"], maintainer["github"])
        for maintainer in maintainers
    ]


def is_maintainer(github_id: int, maintainers: list[Maintainer]) -> bool:
    for m in maintainers:
        if m.github_id == github_id:
            return True
    return False


def merge_check(
    client: GithubClient,
    repo_owner: str,
    repo_name: str,
    pr_number: int,
    github_id: int,
    settings: Settings,
) -> MergeResponse:
    pr = client.pull_request(repo_owner, repo_name, pr_number).json()
    files_response = client.pull_request_files(repo_owner, repo_name, pr_number)
    decline_reasons = {}
    permitted = True
    body = files_response.json()
    sha = pr["head"]["sha"]

    if pr["user"]["login"] not in settings.restricted_authors:
        permitted = False
        decline_reasons[
            "pr"
        ] = f"pr author is not in restricted authors list: {settings.restricted_authors}"
        return MergeResponse(permitted, decline_reasons, sha)

    if pr["state"] != "open":
        permitted = False
        decline_reasons["pr"] = "pr is not open"
        return MergeResponse(permitted, decline_reasons, sha)

    if pr["base"]["ref"] not in ("staging", "staging-next", "master"):
        permitted = False
        decline_reasons[
            "pr"
        ] = "pr is not targed to any of the allowed branches: staging, staging-next, master"
        return MergeResponse(permitted, decline_reasons, sha)

    for file in body:
        filename = file["filename"]
        # Currently disabled this check because we limit the to only allow ryantm-r PRs to be merged.
        # if not filename.startswith("pkgs/by-name/"):
        #    permitted = False
        #    decline_reasons[filename] = "path is not in pkgs/by-name/"
        # else:
        maintainers = get_package_maintainers(Path(filename))
        if not is_maintainer(github_id, maintainers):
            permitted = False
            decline_reasons[
                filename
            ] = "github id is not in maintainers, valid maintainers are: " + ", ".join(
                m.name for m in maintainers
            )
    return MergeResponse(permitted, decline_reasons, sha)
