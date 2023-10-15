import argparse

from .server import Settings, start_server


def parse_args() -> Settings:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=3014)
    parser.add_argument("--host", type=str, default="::")
    parser.add_argument("--webhook-secret", type=str, required=True)
    args = parser.parse_args()
    return Settings(webhook_secret=args.webhook_secret, host=args.host, port=args.port)


def main() -> None:
    settings = parse_args()
    start_server(settings)


if __name__ == "__main__":
    main()
