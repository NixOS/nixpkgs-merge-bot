import socket
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from http.client import HTTPConnection

import pytest


@contextmanager
def socket_pair() -> Iterator[tuple[socket.socket, socket.socket]]:
    fds = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        yield fds
    finally:
        for fd in fds:
            fd.close()


@dataclass
class WebhookClient:
    client_sock: socket.socket
    server_sock: socket.socket
    addr: tuple[str, int] = ("localhost", 8080)

    def http_connect(self) -> HTTPConnection:
        conn = HTTPConnection(*self.addr)
        conn.sock = self.client_sock
        return conn


@pytest.fixture
def webhook_client() -> Iterator[WebhookClient]:
    with socket_pair() as (client_sock, server_sock):
        yield WebhookClient(client_sock, server_sock)
