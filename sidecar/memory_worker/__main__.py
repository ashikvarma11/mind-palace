import argparse
import sys
from .protocol import serve
from .vault import Vault


def main():
    parser = argparse.ArgumentParser(description="Mind Palace private storage foundation")
    parser.add_argument("--mode", choices=["ui"], required=True)
    parser.add_argument("--vault", required=True)
    parser.add_argument("--create-vault", action="store_true")
    args = parser.parse_args()
    try:
        vault = Vault(args.vault, args.create_vault)
    except Exception:
        print("Vault could not be opened safely.", file=sys.stderr)
        return 2
    return serve(vault, sys.stdin.buffer, sys.stdout.buffer)


if __name__ == "__main__":
    raise SystemExit(main())
