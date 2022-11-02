"""Formatter base class for JSONFormatter and YamlFormatter."""
import argparse
import os
import sys
from abc import ABC, abstractmethod
from typing import Type


class FileFormatter(ABC):
    check: bool
    write: bool

    scanned_file_found: int
    unformatted_file_count: int

    def __init__(self, check: bool, write: bool) -> None:
        self.check = check
        self.write = write

        self.scanned_file_found = 0
        self.unformatted_file_count = 0

    @staticmethod
    @abstractmethod
    def description() -> str:
        """Return the description of the formatter."""
        return "JSON file formatter"

    @staticmethod
    @abstractmethod
    def format(input_str: str) -> str:
        """Format method to formatted file content."""

    @staticmethod
    @abstractmethod
    def decode_exception() -> Type[Exception]:
        """Return the exception class when the file content cannot be decoded."""

    @staticmethod
    @abstractmethod
    def file_extension() -> str:
        """Return file extension of files to format."""

    def process_file(self, file_path: str) -> None:
        with open(file_path, "r", encoding="utf-8") as f:
            file_str = f.read()
            try:
                formatted_file_str = self.format(file_str)
            except self.decode_exception() as error:
                raise ValueError(f"{file_path}: Cannot decode the file content") from error
        if file_str != formatted_file_str:
            if self.write:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(formatted_file_str)
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
                if extension != self.file_extension():
                    continue
                self.process_file(file_path)

    def output_summary(self) -> None:
        print(f"{self.scanned_file_found} file(s) scanned.")
        if self.write:
            print(f"{self.unformatted_file_count} file(s) reformatted.")
        if self.check:
            print(f"{self.unformatted_file_count} file(s) need reformat.")
            if self.unformatted_file_count:
                sys.exit(-1)
        print("\033[1mAll done! ✨ 🍰 ✨\033[0m")  # using bold font

    @classmethod
    def main(cls) -> None:
        parser = argparse.ArgumentParser(description=cls.description())
        parser.add_argument(
            "paths",
            metavar="file|dir",
            type=str,
            nargs="+",
            help="file to format or directory containing files to format",
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
        formatter = cls(args.check, args.write)

        for path in args.paths:
            if not os.path.exists(path):
                raise ValueError(f"{path}: No such file or directory")
            if os.path.isfile(path):
                _, extension = os.path.splitext(path)
                if extension != cls.file_extension():
                    raise ValueError(f"{path}: Not a format-able file")
                formatter.process_file(path)
            elif os.path.isdir(path):
                formatter.process_directory(path)
            else:
                raise ValueError(f"{path}: Unsupported path")

        formatter.output_summary()
