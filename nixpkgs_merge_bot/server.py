import os
import socket
from dataclasses import dataclass

from .webhook.handler import GithubWebHook


@dataclass
class Settings:
    webhook_secret: str
    port: int = 3014
    host: str = "[::]"


def start_server(settings: Settings) -> None:
    nfds = os.environ.get("LISTEN_FDS", None)
    if nfds is not None:
        fds = range(3, 3 + int(nfds))
        for fd in fds:
            sock = socket.fromfd(fd, socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0)

            try:
                while True:
                    GithubWebHook(*sock.accept(), settings.webhook_secret)
            except BlockingIOError:
                # no more connections
                pass
    else:
        serversocket = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        try:
            serversocket.bind((settings.host, settings.port))
            serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            print(f"listen on {settings.host}:{settings.port}")
            serversocket.listen()
            while True:
                conn, addr = serversocket.accept()
                GithubWebHook(conn, addr, settings.webhook_secret)
        finally:
            serversocket.shutdown(socket.SHUT_RDWR)
            serversocket.close()
