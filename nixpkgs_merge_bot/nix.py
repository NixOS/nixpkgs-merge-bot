import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .github import GithubClient


@dataclass
class MergeResponse:
    permitted: bool
    decline_reasons: dict[str, str]
    sha: str


@dataclass
class Maintainer:
    github_id: int
    name: str


def get_package_maintainers(path: Path) -> list[Maintainer]:
    package_name = path.parts[3]
    # TODO maybe we want to check the merge target remote here?
    flake_url = f"github:nixos/nixpkgs/master#{package_name}.meta.maintainers"

    proc = subprocess.run(
        [
            "nix",
            "eval",
            "--refresh",
            "--json",
            flake_url,
        ],
        check=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    maintainers = json.loads(proc.stdout.decode("utf-8"))
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
    repo_owner: str, repo_name: str, pr_number: int, github_id: int
) -> MergeResponse:
    c = GithubClient(None)
    pr = c.pull_request(repo_owner, repo_name, pr_number).json()
    files_response = c.pull_request_files(repo_owner, repo_name, pr_number)
    decline_reasons = {}
    permitted = True
    body = files_response.json()
    sha = pr["head"]["sha"]
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
        if not filename.startswith("pkgs/by-name/"):
            permitted = False
            decline_reasons[filename] = "path is not in pkgs/by-name/"
        else:
            maintainers = get_package_maintainers(Path(filename))
            if not is_maintainer(github_id, maintainers):
                permitted = False
                decline_reasons[filename] = (
                    "github id is not in maintainers, valid maintainers are: "
                    + ", ".join(m.name for m in maintainers)
                )
    return MergeResponse(permitted, decline_reasons, sha)
