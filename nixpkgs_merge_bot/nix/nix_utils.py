import json
import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

from ..settings import Settings

log = logging.getLogger(__name__)


@dataclass
class MergeResponse:
    permitted: bool
    decline_reasons: list[str]
    sha: str


@dataclass
class Maintainer:
    github_id: int
    name: str


def nix_eval(folder: Path, attr: str) -> bytes:
    log.info(f"Running nix-instantiate with attr: {attr} and folder: {folder}")
    proc = subprocess.run(
        [
            "nix-instantiate",
            "--eval",
            "--strict",
            "--json",
            str(folder),
            "-A",
            attr,
        ],
        check=True,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
    )
    return proc.stdout


def get_package_maintainers(settings: Settings, path: Path) -> list[Maintainer]:
    from ..git import checkout_newest_master

    checkout_newest_master(settings.repo_path)
    package_name = path.parts[3]
    # TODO maybe we want to check the merge target remote here?
    proc = nix_eval(settings.repo_path, f"{package_name}.meta.maintainers")
    maintainers = json.loads(proc.decode("utf-8"))
    log.debug(f"Found {maintainers} for {path}")
    return [
        Maintainer(maintainer["githubId"], maintainer["github"])
        for maintainer in maintainers
    ]


def is_maintainer(github_id: int, maintainers: list[Maintainer]) -> bool:
    for m in maintainers:
        if m.github_id == github_id:
            return True
    return False
