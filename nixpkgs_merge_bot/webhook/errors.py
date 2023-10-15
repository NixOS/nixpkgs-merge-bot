from dataclasses import dataclass


@dataclass
class HttpError(Exception):
    code: int
    message: str
