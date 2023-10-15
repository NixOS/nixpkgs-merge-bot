import json
import subprocess
from pathlib import Path

from .github import GithubClient


class MergeResponse:
    def __init__(self, permitted: bool, meta: dict):
        self.permitted = permitted
        self.meta = meta


def get_package_maintainers(path: str) -> list[str]:
    path_ = Path(path)
    proc = subprocess.run(
        [
            "nix",
            "eval",
            "--refresh",
            "--json",
            f"github:nixos/nixpkgs/master#{path_.parent.name}.meta.maintainers",
        ],
        check=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    maintainers = json.loads(proc.stdout.decode("utf-8"))
    return [maintainer["githubId"] for maintainer in maintainers]


def merge_pr(pr_number: int, github_id: int) -> MergeResponse:
    c = GithubClient(None)
    files_response = c.pull_request_files("nixos", "nixpkgs", pr_number)
    meta = {}
    permitted = True
    for file in files_response.json():
        filename = file["filename"]
        if not filename.startswith("pkgs/by-name/"):
            permitted = False
            meta[filename] = "path is not in pkgs/by-name/"
        else:
            maintainers = get_package_maintainers(filename)
            if github_id not in maintainers:
                permitted = False
                meta[filename] = (
                    "github id is not in maintainers, valid maintainers are: "
                    + ", ".join(maintainers)
                )
    return MergeResponse(permitted, meta)
