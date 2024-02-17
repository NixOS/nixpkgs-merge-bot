import logging
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)


def clone(repo: str, folder: Path) -> None:
    if not Path(folder).exists():
        log.info(f"Cloning {repo} into {folder}")
        subprocess.run(["git", "clone", repo, folder], check=True)
    else:
        log.info("Repo already exists, skipping")


def fetch(folder: Path) -> None:
    log.info(f"Fetching {folder}")
    subprocess.run(["git", "fetch"], cwd=folder, check=True)


def checkout_newest_master(folder: Path) -> None:
    log.info(f"Checking out newest master: {folder}")
    fetch(folder)
    subprocess.run(["git", "reset", "--hard", "origin/master"], cwd=folder, check=True)
