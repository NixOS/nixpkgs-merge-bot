import argparse
import logging
import os
import sqlite3
from pathlib import Path

from .custom_logger import setup_logging
from .server import Settings, start_server

LOGLEVEL = os.environ.get("LOGLEVEL", "WARNING").upper()


setup_logging(LOGLEVEL)
log = logging.getLogger(__name__)
log.info(f"Log level set to {LOGLEVEL}")


def parse_args() -> Settings:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=3014, help="port to listen on")
    parser.add_argument("--host", type=str, default="::", help="host to listen on")
    parser.add_argument(
        "--webhook-secret", type=str, required=True, help="github webhook secret path"
    )
    parser.add_argument(
        "--bot-name", type=str, default="NixOS/nixpkgs-merge-bot", help="bot name"
    )
    parser.add_argument(
        "--restricted-authors",
        type=str,
        default="",
        help="comma separated list of PR authors that can be merged",
    )
    parser.add_argument(
        "--github-app-login",
        type=str,
        required=True,
        help="the organization or user that owns the github app",
    )
    parser.add_argument(
        "--github-app-id", type=int, required=True, help="github app id"
    )
    parser.add_argument(
        "--github-app-private-key",
        type=str,
        required=True,
        help="Path to github app private key",
    )
    parser.add_argument(
        "--repo-path",
        type=str,
        default="nixpkgs",
        help="Path where the nixpkg repo is stored. Default to nixpkgs",
    )
    parser.add_argument(
        "--database-folder",
        type=str,
        default="/tmp",
        help="Path where the nixpkgs-merge-bot database will be stored. Default to /tmp",
    )
    parser.add_argument(
        "--max-file-size-mb",
        type=int,
        default="2",
        help="Maximum allowed file size in megabytes (MB). Default is 2 MB.",
    )
    parser.add_argument("--debug", action="store_true", help="enable debug logging")
    args = parser.parse_args()
    return Settings(
        bot_name=args.bot_name,
        webhook_secret=Path(args.webhook_secret),
        host=args.host,
        port=args.port,
        github_app_login=args.github_app_login,
        github_app_id=args.github_app_id,
        github_app_private_key=args.github_app_private_key,
        restricted_authors=args.restricted_authors.split(" "),
        database_path=args.database_folder,
        repo_path=args.repo_path,
        max_file_size_mb=args.max_file_size_mb,
    )


def main() -> None:
    settings = parse_args()
    con = sqlite3.connect(f"{settings.database_path}/nixpkgs_merge_bot.db")
    cur = con.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS prs_to_merge(repo_owner,repo_name,user_github_id,issue_number,sha)"
    )
    con.close()

    start_server(settings)


if __name__ == "__main__":
    main()
