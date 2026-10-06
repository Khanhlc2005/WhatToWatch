#!/usr/bin/env python3
"""Adapt the supplied movies_data.sql to the current Movie entity schema."""

import argparse
from pathlib import Path
import re


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.output.resolve():
        parser.error("source and output must be different files")

    source = args.source.read_text(encoding="utf-8")
    converted, insert_count = re.subn(
        r"INSERT INTO movie \(\s*",
        "INSERT INTO movie (\n            id, created_at, updated_at,\n            ",
        source,
    )
    converted, values_count = re.subn(
        r"\) VALUES \(\s*",
        ") VALUES (\n            UUID(), NOW(6), NOW(6),\n            ",
        converted,
    )
    if insert_count == 0 or insert_count != values_count:
        parser.error("unexpected SQL format; no output was written")
    args.output.write_text(converted, encoding="utf-8")
    print(f"Prepared {insert_count} movie INSERT statements in {args.output}")


if __name__ == "__main__":
    main()
