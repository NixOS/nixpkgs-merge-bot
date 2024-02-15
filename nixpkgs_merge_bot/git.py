import logging
import subprocess
from pathlib import Path


def clone(repo: str, folder: Path) -> None:
    if not Path(folder).exists():
        logging.info(f"Cloning {repo} into {folder}")
        subprocess.run(["git", "clone", repo, folder], check=True)
    else:
        logging.info("Repo already exists, skipping")


def fetch(folder: Path) -> None:
    logging.info(f"Fetching {folder}")
    subprocess.run(["git", "fetch"], cwd=folder, check=True)


def checkout_newest_master(folder: Path) -> None:
    logging.info(f"Checking out newest master: {folder}")
    fetch(folder)
    subprocess.run(["git", "reset", "--hard", "origin/master"], cwd=folder, check=True)
