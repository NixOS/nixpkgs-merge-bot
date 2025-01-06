from pathlib import Path

from .settings import Settings


class Database:
    def __init__(self, settings: Settings) -> None:
        self.db_store_path = Path(settings.database_path)
        self.db_store_path.mkdir(parents=True, exist_ok=True)

    def add(self, key: str, value: str) -> None:
        path = self.db_store_path / key
        path.mkdir(parents=True, exist_ok=True)
        (path / value).touch()

    def delete(self, key: str, value: str) -> None:
        path = self.db_store_path / key / value
        if path.exists():
            path.unlink()

    def get(self, key: str) -> list[str]:
        path = self.db_store_path / key
        values: list[str] = []
        if not path.exists():
            return values
        values.extend(child.name for child in path.iterdir())
        return values
