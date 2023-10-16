from dataclasses import dataclass


@dataclass
class Settings:
    webhook_secret: str
    github_app_login: str  # the organization or user that owns the github app
    github_app_id: int
    github_app_private_key: str
    bot_name: str = "nixpkgs-merge-bot"
    port: int = 3014
    host: str = "[::]"
