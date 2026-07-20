#!/usr/bin/env python3
"""Deterministic daily GenLens email job.

This is meant for Hermes cron. It avoids agent-side skill selection by running
the composer and Resend sender scripts directly.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
SCRIPT_DIR = BASE_DIR / "scripts"
STATE_DIR = BASE_DIR / "state"
def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, capture_output=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lens", choices=["genny", "marti", "unified"], default="genny")
    parser.add_argument("--mode", choices=["active", "expanded"], default="expanded")
    args = parser.parse_args()
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    today = dt.datetime.now().date().isoformat()
    edition = {"genny": "GenLens", "marti": "Marti", "unified": "Marti-Genny"}[args.lens]

    ops = run([
        str(SCRIPT_DIR / "genlens_editorial_ops.py"),
        "--mode",
        args.mode,
        "--lens",
        args.lens,
        "--per-vertical",
        "5",
        "--rss-limit",
        "12",
        "--send",
        "--to",
        os.environ.get("GENLENS_EMAIL_TO", "jj@damnjj.wtf"),
        "--subject",
        f"{edition} daily briefing - {today}",
    ])

    output = ops.stdout.strip()
    print(f"{edition} daily email job completed for {today}.")
    if output:
        print(output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except subprocess.CalledProcessError as exc:
        print("Intelligence daily email job failed.", file=sys.stderr)
        if exc.stdout:
            print(exc.stdout, file=sys.stderr)
        if exc.stderr:
            print(exc.stderr, file=sys.stderr)
        raise SystemExit(exc.returncode)
