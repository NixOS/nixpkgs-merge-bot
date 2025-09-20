import http.client
import json
import shutil
from pathlib import Path
from typing import Any


class HttpResponse:
    def __init__(self, raw: http.client.HTTPResponse) -> None:
        self.raw = raw

    def json(self) -> Any:
        return json.load(self.raw)

    def save(self, path: str) -> None:
        with Path(path).open("wb") as f:
            shutil.copyfileobj(self.raw, f)

    def headers(self) -> http.client.HTTPMessage:
        return self.raw.headers
