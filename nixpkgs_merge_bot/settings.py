from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Settings:
    webhook_secret: Path
    github_app_login: str  # the organization or user that owns the github app
    github_app_id: int
    github_app_private_key: Path
    restricted_authors: list[str] = field(default_factory=list)
    bot_name: str = "NixOS/nixpkgs-merge-bot"
    port: int = 3014
    host: str = "[::]"
    repo: str = "https://github.com/nixos/nixpkgs"
    repo_path: Path = Path("nixpkgs")
    database_path: str = "/tmp/"
    max_file_size_mb: int = 2
    committer_team_slug: str = "nixpkgs-committers"

    @property
    def max_file_size_bytes(self) -> int:
        """Return the maximum file size in bytes."""
        return self.max_file_size_mb * 1024 * 1024
