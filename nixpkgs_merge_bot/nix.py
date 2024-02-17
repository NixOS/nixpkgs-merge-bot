import json
import logging
import sqlite3
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .github import GithubClient
from .settings import Settings

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
    from .git import checkout_newest_master

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
    decline_reasons = ["bot is running in dry-run mode"]
    permitted = True
    body = files_response.json()
    sha = pr["head"]["sha"]
    log.info(f"Checking mergeability of {pr_number} with sha {sha}")

    if pr["user"]["login"] not in settings.restricted_authors:
        permitted = False
        message = (
            "pr author is not in restricted authors list, in the list are: "
            + ", ".join(settings.restricted_authors)
        )
        decline_reasons.append(message)
        log.info(message)

    if pr["state"] != "open":
        permitted = False
        message = f"pr is not open, state is {pr['state']}"
        decline_reasons.append(message)
        log.info(message)

    if pr["base"]["ref"] not in ("staging", "staging-next", "master"):
        permitted = False
        message = "pr is not targeted to any of the allowed branches: staging, staging-next, master"
        decline_reasons.append(message)
        log.info(message)

    # Check if check_run is completed

    statuses = client.get_statuses_for_commit(repo_owner, repo_name, sha).json()
    if statuses["state"] != "success":
        message = f"Status {statuses['state']} is not success"
        decline_reasons.append(message)
        log.info(message)
        permitted = False
        if statuses["state"] == "pending":
            con = sqlite3.connect(f"{settings.database_path}/nixpkgs_merge_bot.db")
            cur = con.cursor()
            sql = """ INSERT INTO prs_to_merge(repo_owner,repo_name,user_github_id,issue_number,sha)
              VALUES(?,?,?,?,?) """
            cur.execute(sql, (repo_owner, repo_name, github_id, pr_number, sha))
            con.close()
            message = "We are still waiting for evaluation, we will wait and try to merge later"
            decline_reasons.append(message)
            log.info(message)

    log.debug("Getting check suites for commit")
    check_suites_for_commit = client.get_check_suites_for_commit(
        repo_owner, repo_name, sha
    )
    all_check_suites_completed = True
    for check_suite in check_suites_for_commit.json()["check_suites"]:
        log.debug(
            f"{check_suite['app']['name']} conclusion: {check_suite['conclusion']} and status: {check_suite['status']}"
        )
        # First check if all check suites are completed if not we will add them to the database and wait for the webhook for finished check suites
        # The summary status for all check runs that are part of the check suite. Can be requested, in_progress, or completed.
        if check_suite["status"] != "completed":
            message = f"Check suite {check_suite['app']['name']} is not completed, we will wait for it to finish and if it succeeds we will merge this."
            decline_reasons.append(message)
            log.info(message)
            all_check_suites_completed = False
        else:
            # if the state is not success or skipped we will decline the merge. The state can be
            # Can be one of: success, failure, neutral, cancelled, timed_out, action_required, stale, null, skipped, startup_failure
            if not (
                check_suite["conclusion"] == "success"
                or check_suite["conclusion"] == "skipped"
            ):
                message = f"Check suite {check_suite['app']['name']} is {check_suite['conclusion']}"
                decline_reasons.append(message)
                log.info(message)
                permitted = False
    if not all_check_suites_completed:
        con = sqlite3.connect(f"{settings.database_path}/nixpkgs_merge_bot.db")
        cur = con.cursor()
        sql = """ INSERT INTO prs_to_merge(repo_owner,repo_name,user_github_id,issue_number,sha)
          VALUES(?,?,?,?,?) """
        cur.execute(sql, (repo_owner, repo_name, github_id, pr_number, sha))
        con.close()
        message = f"Not all check suites are completed, we will wait for them to finish issue_number: {pr_number}, sha: {sha}"
        decline_reasons.append(message)
        log.info(message)
        permitted = False

    for file in body:
        filename = file["filename"]
        if not filename.startswith("pkgs/by-name/"):
            permitted = False
            message = f"{filename} is not in pkgs/by-name/"
            decline_reasons.append(message)
            log.info(message)
        else:
            maintainers = get_package_maintainers(settings, Path(filename))
            if not is_maintainer(github_id, maintainers):
                permitted = False
                message = (
                    f"github id: {github_id} is not in maintainers, valid maintainers are: "
                    + ", ".join(m.name for m in maintainers)
                )
                decline_reasons.append(message)
                log.info(message)
    # merging is disabled for now, until we have sufficient consensus
    permitted = False

    return MergeResponse(permitted, decline_reasons, sha)
