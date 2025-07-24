import socket
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from http.client import HTTPConnection
from typing import Protocol, TypeVar

import pytest

T = TypeVar("T")


class WebhookHandler(Protocol[T]):
    """Protocol for webhook handlers that accept socket, address, and settings."""

    def __call__(
        self, conn: socket.socket, addr: tuple[str, int], settings: T
    ) -> None: ...


@contextmanager
def socket_pair() -> Iterator[tuple[socket.socket, socket.socket]]:
    fds = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        yield fds
    finally:
        for fd in fds:
            fd.close()


@dataclass
class WebhookTestServer:
    client_sock: socket.socket
    server_sock: socket.socket
    addr: tuple[str, int] = ("localhost", 8080)
    server_thread: threading.Thread | None = None

    def get_client(self) -> HTTPConnection:
        conn = HTTPConnection(*self.addr)
        conn.sock = self.client_sock
        return conn

    def start_handler(
        self, handler_class: type[WebhookHandler[T]], settings: T
    ) -> None:
        """Start the GithubWebHook handler in a separate thread"""
        self.server_thread = threading.Thread(
            target=handler_class, args=(self.server_sock, self.addr, settings)
        )
        self.server_thread.start()
        # Give the server a moment to start
        threading.Event().wait(0.1)

    def wait_for_handler(self, timeout: float = 5.0) -> None:
        """Wait for the handler thread to complete"""
        if self.server_thread:
            self.server_thread.join(timeout=timeout)


@pytest.fixture
def server() -> Iterator[WebhookTestServer]:
    with socket_pair() as (client_sock, server_sock):
        yield WebhookTestServer(client_sock, server_sock)
