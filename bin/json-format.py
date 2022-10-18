#!/usr/bin/env python
"""JSON file formatter (without prettier)."""
import argparse
import json
import os.path
import sys


def format_json(json_str: str) -> str:
    """Opinionated format JSON file."""
    obj = json.loads(json_str)
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


class JSONFormatter:
    check: bool
    write: bool

    scanned_file_found: int
    unformatted_file_count: int

    def __init__(self, check: bool, write: bool) -> None:
        self.check = check
        self.write = write

        self.scanned_file_found = 0
        self.unformatted_file_count = 0

    def process_file(self, file_path: str) -> None:
        with open(file_path, "r", encoding="utf-8") as f:
            json_str = f.read()
            try:
                formatted_json_str = format_json(json_str)
            except json.JSONDecodeError as error:
                raise ValueError(f"{file_path}: Invalid JSON") from error
        if json_str != formatted_json_str:
            if self.write:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(formatted_json_str)
                print(f"reformatted {file_path}")
            if self.check:
                print(f"would reformat {file_path}")
            self.unformatted_file_count += 1
        self.scanned_file_found += 1

    def process_directory(self, directory_path: str) -> None:
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                _, extension = os.path.splitext(file_path)
                if extension != ".json":
                    continue
                self.process_file(file_path)

    def output_summary(self):
        print(f"{self.scanned_file_found} file(s) scanned.")
        if self.write:
            print(f"{self.unformatted_file_count} file(s) reformatted.")
        if self.check:
            print(f"{self.unformatted_file_count} file(s) need reformat.")
            if self.unformatted_file_count:
                sys.exit(-1)


def main() -> None:
    parser = argparse.ArgumentParser(description="JSON file formatter.")
    parser.add_argument(
        "paths", metavar="file|dir", type=str, nargs="+", help="JSON file or directory containing JSON files"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-c",
        "--check",
        action="store_true",
        help="Check if the given files are formatted, "
        "print a human-friendly summary message and paths to un-formatted files",
    )
    group.add_argument(
        "-w",
        "--write",
        action="store_true",
        help="Edit files in-place. (Beware!)",
    )

    args = parser.parse_args()
    formatter = JSONFormatter(args.check, args.write)

    for path in args.paths:
        if not os.path.exists(path):
            raise ValueError(f"{path}: No such file or directory")
        if os.path.isfile(path):
            _, extension = os.path.splitext(path)
            if extension != ".json":
                raise ValueError(f"{path}: Not a JSON file")
            formatter.process_file(path)
        elif os.path.isdir(path):
            formatter.process_directory(path)
        else:
            raise ValueError(f"{path}: Unsupported path")

    formatter.output_summary()


if __name__ == "__main__":
    main()
