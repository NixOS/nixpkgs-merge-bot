from dataclasses import dataclass


@dataclass
class HttpResponse:
    code: int
    headers: dict[str, str]
    body: bytes
