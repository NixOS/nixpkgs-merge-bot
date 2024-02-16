import argparse
import logging
import os
from pathlib import Path

from .server import Settings, start_server

LOGLEVEL = os.environ.get("LOGLEVEL", "WARNING").upper()
logging.basicConfig(level=LOGLEVEL)


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
        repo_path=args.repo_path,
    )


def main() -> None:
    settings = parse_args()
    start_server(settings)


if __name__ == "__main__":
    main()
