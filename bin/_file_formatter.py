"""Formatter base class for JSONFormatter and YamlFormatter."""
import argparse
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Type


class FileFormatter(ABC):
    args: argparse.Namespace

    scanned_file_found: int
    unformatted_file_count: int

    arg_parser: argparse.ArgumentParser

    def __init__(self, args: argparse.Namespace) -> None:
        self.args = args

        self.scanned_file_found = 0
        self.unformatted_file_count = 0

    @staticmethod
    @abstractmethod
    def description() -> str:
        """Return the description of the formatter."""
        return "JSON file formatter"

    @abstractmethod
    def format_str(self, input_str: str) -> str:
        """Format method to formatted file content."""

    @staticmethod
    @abstractmethod
    def decode_exception() -> Type[Exception]:
        """Return the exception class when the file content cannot be decoded."""

    @staticmethod
    @abstractmethod
    def file_extension() -> str:
        """Return file extension of files to format."""

    @classmethod
    def config_additional_args(cls) -> None:  # noqa: empty-method-without-abstract-decorator
        """Optionally configure additional args to arg parser."""

    def process_file(self, file_path: Path) -> None:
        file_str = file_path.read_text(encoding="utf-8")
        try:
            formatted_file_str = self.format_str(file_str)
        except self.decode_exception() as error:
            raise ValueError(f"{file_path}: Cannot decode the file content") from error
        except Exception as error:
            raise ValueError(f"{file_path}: Fail to process") from error
        if file_str != formatted_file_str:
            if self.args.write:
                Path(file_path).write_text(formatted_file_str, encoding="utf-8")
                print(f"reformatted {file_path}")
            if self.args.check:
                print(f"would reformat {file_path}")
            self.unformatted_file_count += 1
        self.scanned_file_found += 1

    def process_directory(self, directory_path: Path) -> None:
        for root, _dirs, files in os.walk(directory_path):
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix != self.file_extension():
                    continue
                self.process_file(file_path)

    def output_summary(self) -> None:
        print(f"{self.scanned_file_found} file(s) scanned.")
        if self.args.write:
            print(f"{self.unformatted_file_count} file(s) reformatted.")
        if self.args.check:
            print(f"{self.unformatted_file_count} file(s) need reformat.")
            if self.unformatted_file_count:
                sys.exit(-1)
        print("\033[1mAll done! ✨ 🍰 ✨\033[0m")  # using bold font

    @classmethod
    def main(cls) -> None:
        cls.arg_parser = argparse.ArgumentParser(description=cls.description())
        cls.arg_parser.add_argument(
            "paths",
            metavar="file|dir",
            type=str,
            nargs="+",
            help="file to format or directory containing files to format",
        )
        group = cls.arg_parser.add_mutually_exclusive_group()
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

        cls.config_additional_args()

        args = cls.arg_parser.parse_args()
        formatter = cls(args)

        for _path in args.paths:
            path = Path(_path)
            if not path.exists():
                raise ValueError(f"{path}: No such file or directory")
            if path.is_file():
                if path.suffix != cls.file_extension():
                    raise ValueError(f"{path}: Not a format-able file")
                formatter.process_file(path)
            elif path.is_dir():
                formatter.process_directory(path)
            else:
                raise ValueError(f"{path}: Unsupported path")

        formatter.output_summary()
