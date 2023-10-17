from dataclasses import dataclass
from pathlib import Path


@dataclass
class Settings:
    webhook_secret: Path
    github_app_login: str  # the organization or user that owns the github app
    github_app_id: int
    github_app_private_key: Path
    bot_name: str = "nixpkgs-merge-bot"
    port: int = 3014
    host: str = "[::]"
