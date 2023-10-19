import subprocess
from pathlib import Path


def clone(repo: str, folder: Path) -> None:
    if not Path(folder).exists():
        subprocess.run(["git", "clone", repo, folder], check=True)


def fetch(folder: Path) -> None:
    subprocess.run(["git", "fetch"], cwd=folder, check=True)


def checkout_newest_master(folder: Path) -> None:
    fetch(folder)
    subprocess.run(["git", "reset", "--hard", "origin/master"], cwd=folder, check=True)
