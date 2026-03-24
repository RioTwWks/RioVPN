"""Alembic script runner."""

from alembic import command
from alembic.config import Config
from alembic.runtime import migration
from alembic.util.exc import CommandError

import os
import sys


def run_alembic_cmd(alembic_cmd: str, *args, **kwargs) -> None:
    """
    Run Alembic command.

    Args:
        alembic_cmd: Alembic command to run
        *args: Command arguments
        **kwargs: Command keyword arguments
    """
    config = Config("alembic.ini")
    getattr(command, alembic_cmd)(config, *args, **kwargs)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m migrations <command> [args]")
        print("Commands: upgrade, downgrade, revision, current, history, stamp")
        sys.exit(1)

    cmd = sys.argv[1]
    args = sys.argv[2:]

    try:
        if cmd == "upgrade":
            run_alembic_cmd("upgrade", args[0] if args else "head")
        elif cmd == "downgrade":
            run_alembic_cmd("downgrade", args[0] if args else "-1")
        elif cmd == "revision":
            run_alembic_cmd("revision", *args)
        elif cmd == "current":
            run_alembic_cmd("current")
        elif cmd == "history":
            run_alembic_cmd("history")
        elif cmd == "stamp":
            run_alembic_cmd("stamp", args[0] if args else "head")
        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)
    except CommandError as e:
        print(f"Error: {e}")
        sys.exit(1)
