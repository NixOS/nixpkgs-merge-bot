from pathlib import Path

from .settings import Settings


class Database:
    def __init__(self, settings: Settings) -> None:
        self.datbase_store_path = Path(settings.database_path)
        self.datbase_store_path.mkdir(parents=True, exist_ok=True)

    def add(self, key: str, value: str) -> None:
        path = self.datbase_store_path / key
        path.mkdir(parents=True, exist_ok=True)
        (path / value).touch()

    def delete(self, key: str, value: str) -> None:
        if value is None:
            path = self.datbase_store_path / key
            if path.exists:
                path.rmdir()
        else:
            path = self.datbase_store_path / key / value
            if path.exists():
                path.unlink()

    def get(self, key: str) -> list[str]:
        path = self.datbase_store_path / key
        values = []
        for child in path.iterdir():
            values.append(child.name)
        return values
