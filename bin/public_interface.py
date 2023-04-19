#!/usr/bin/env python
"""
Extract/compare public interfaces.

aws-sam-translator library hasn't documented public interfaces,
so we assume anything public by convention unless it is prefixed with "_".
(see https://peps.python.org/pep-0008/#descriptive-naming-styles)
This CLI tool helps automate the detection of compatibility-breaking changes.
"""
import argparse
import ast
import importlib
import inspect
import json
import os.path
import pkgutil
import string
import sys
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Set, Union

_ARGUMENT_SELF = {"kind": "POSITIONAL_OR_KEYWORD", "name": "self"}
_PRINTABLE_CHARS = set(string.printable)


class InterfaceScanner:
    def __init__(self, skipped_modules: Optional[List[str]] = None) -> None:
        self.signatures: Dict[str, Union[inspect.Signature]] = {}
        self.variables: Set[str] = set()
        self.skipped_modules: Set[str] = set(skipped_modules or [])

    def scan_interfaces_recursively(self, module_name: str) -> None:
        if module_name in self.skipped_modules:
            return
        self._scan_interfaces_in_module(module_name)
        for submodule in pkgutil.iter_modules([module_name.replace(".", os.path.sep)]):
            submodule_name = module_name + "." + submodule.name
            self.scan_interfaces_recursively(submodule_name)

    def _scan_interfaces_in_module(self, module_name: str) -> None:
        self._scan_functions_in_module(module_name)
        self._scan_classes_in_module(module_name)
        self._scan_variables_in_module(module_name)

    def _scan_functions_in_module(self, module_name: str) -> None:
        for function_name, function in inspect.getmembers(
            importlib.import_module(module_name), lambda obj: inspect.ismethod(obj) or inspect.isfunction(obj)
        ):
            # Skip imported functions and ones starting with "_"
            if function.__module__ != module_name or function_name.startswith("_"):
                continue
            full_path = f"{module_name}.{function_name}"
            self.signatures[full_path] = inspect.signature(function)

    def _scan_variables_in_module(self, module_name: str) -> None:
        """
        Use ast to find all assignments at the module level to find constants.
        Note: Class (and other types) should be treated as a variable too
        """
        module_path = Path(module_name.replace(".", os.path.sep))
        if module_path.is_dir():
            module_path /= "__init__.py"
        else:
            module_path = module_path.with_suffix(".py")
        tree = ast.parse("".join([char for char in module_path.read_text() if char in _PRINTABLE_CHARS]))
        assignments: List[ast.Assign] = [node for node in ast.iter_child_nodes(tree) if isinstance(node, ast.Assign)]
        for assignment in assignments:
            for target in assignment.targets:
                if not isinstance(target, ast.Name):
                    continue
                if target.id.startswith("_"):
                    continue
                full_path = f"{module_name}.{target.id}"
                self.variables.add(full_path)

        for class_name, _class in inspect.getmembers(importlib.import_module(module_name), inspect.isclass):
            # Skip imported and ones starting with "_"
            if _class.__module__ != module_name or class_name.startswith("_"):
                continue
            full_path = f"{module_name}.{class_name}"
            self.variables.add(full_path)

    def _scan_classes_in_module(self, module_name: str) -> None:
        for class_name, _class in inspect.getmembers(importlib.import_module(module_name), inspect.isclass):
            # Skip imported and ones starting with "_"
            if _class.__module__ != module_name or class_name.startswith("_"):
                continue
            self._scan_methods_in_class(class_name, _class)

    def _scan_methods_in_class(self, class_name: str, _class: Any) -> None:
        for method_name, method in inspect.getmembers(
            _class, lambda obj: inspect.ismethod(obj) or inspect.isfunction(obj)
        ):
            if method_name.startswith("_"):
                continue
            full_path = f"{_class.__module__}.{class_name}.{method_name}"
            self.signatures[full_path] = inspect.signature(method)


def _print(signature: Dict[str, inspect.Signature], variables: Set[str]) -> None:
    result: Dict[str, Any] = {"routines": {}, "variables": sorted(variables)}
    for key, value in signature.items():
        result["routines"][key] = [
            {
                "name": parameter.name,
                "kind": parameter.kind.name,
                "default": parameter.default,
            }
            if parameter.default != inspect.Parameter.empty
            else {"name": parameter.name, "kind": parameter.kind.name}
            for parameter in value.parameters.values()
        ]
    print(json.dumps(result, indent=2, sort_keys=True))


class _BreakingChanges(NamedTuple):
    deleted_variables: List[str]
    deleted_routines: List[str]
    incompatible_routines: List[str]

    def is_empty(self) -> bool:
        return not any([self.deleted_variables, self.deleted_routines, self.incompatible_routines])

    @staticmethod
    def _argument_to_str(argument: Dict[str, Any]) -> str:
        if "default" in argument:
            return f'{argument["name"]}={argument["default"]}'
        return str(argument["name"])

    def print_markdown(
        self,
        original_routines: Dict[str, List[Dict[str, Any]]],
        routines: Dict[str, List[Dict[str, Any]]],
    ) -> None:
        """Print all breaking changes in markdown."""
        print("\n# Compatibility breaking changes:")
        print("**These changes are considered breaking changes and may break packages consuming")
        print("the PyPI package [aws-sam-translator](https://pypi.org/project/aws-sam-translator/).")
        print("Please consider revisiting these changes to make sure they are intentional:**")
        if self.deleted_variables:
            print("\n## Deleted module level variables")
            for name in self.deleted_variables:
                print(f"- {name}")
        if self.deleted_routines:
            print("\n## Deleted routines")
            for name in self.deleted_routines:
                print(f"- {name}")
        if self.incompatible_routines:
            print("\n## Incompatible routines")
            for name in self.incompatible_routines:
                before = f"({', '.join(self._argument_to_str(arg) for arg in original_routines[name])})"
                after = f"({', '.join(self._argument_to_str(arg) for arg in routines[name])})"
                print(f"- {name}: `{before}` -> `{after}`")


def _only_new_optional_arguments_or_existing_arguments_optionalized_or_var_arguments(
    original_arguments: List[Dict[str, Any]], arguments: List[Dict[str, Any]]
) -> bool:
    if len(original_arguments) > len(arguments):
        return False
    for i, original_argument in enumerate(original_arguments):
        if original_argument == arguments[i]:
            continue
        if (
            original_argument["name"] == arguments[i]["name"]
            and original_argument["kind"] == arguments[i]["kind"]
            and "default" not in original_argument
            and "default" in arguments[i]
        ):
            continue
        return False
    # it is an optional argument when it has a default value:
    return all(
        "default" in argument or argument["kind"] in ("VAR_KEYWORD", "VAR_POSITIONAL")
        for argument in arguments[len(original_arguments) :]
    )


def _is_compatible(original_arguments: List[Dict[str, Any]], arguments: List[Dict[str, Any]]) -> bool:
    """
    If there is an argument change, it is compatible only when
    - new optional arguments are added or existing arguments become optional.
    - var arguments (*args, **kwargs) are added
    - self is removed (method -> staticmethod).
    - combination of above
    """
    if (
        original_arguments == arguments
        or _only_new_optional_arguments_or_existing_arguments_optionalized_or_var_arguments(
            original_arguments, arguments
        )
    ):
        return True
    if original_arguments and original_arguments[0] == _ARGUMENT_SELF:
        original_arguments_without_self = original_arguments[1:]
        if _is_compatible(original_arguments_without_self, arguments):
            return True
    return False


def _detect_breaking_changes(
    original_routines: Dict[str, List[Dict[str, Any]]],
    original_variables: Set[str],
    routines: Dict[str, List[Dict[str, Any]]],
    variables: Set[str],
) -> _BreakingChanges:
    deleted_routines: List[str] = []
    incompatible_routines: List[str] = []
    for routine_path, arguments in original_routines.items():
        if routine_path not in routines:
            deleted_routines.append(routine_path)
        elif not _is_compatible(arguments, routines[routine_path]):
            incompatible_routines.append(routine_path)
    return _BreakingChanges(
        sorted(set(original_variables) - set(variables)), sorted(deleted_routines), sorted(incompatible_routines)
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)

    subparsers = parser.add_subparsers(dest="command")
    extract = subparsers.add_parser("extract", help="Extract public interfaces")
    extract.add_argument("--module", help="The module to extract public interfaces", type=str, default="samtranslator")
    extract.add_argument(
        "--skipped-module",
        help="The modules that should be skipped",
        type=str,
        nargs="*",
        default=["samtranslator.internal"],
    )
    check = subparsers.add_parser("check", help="Check public interface changes")
    check.add_argument("original_json", help="The original public interface JSON file", type=Path)
    check.add_argument("new_json", help="The new public interface JSON file", type=Path)
    args = parser.parse_args()

    if args.command == "extract":
        scanner = InterfaceScanner(skipped_modules=args.skipped_module)
        scanner.scan_interfaces_recursively(args.module)
        _print(scanner.signatures, scanner.variables)
    elif args.command == "check":
        original_json = json.loads(args.original_json.read_text())
        new_json = json.loads(args.new_json.read_text())
        breaking_changes = _detect_breaking_changes(
            original_json["routines"], original_json["variables"], new_json["routines"], new_json["variables"]
        )
        if breaking_changes.is_empty():
            sys.stderr.write("No compatibility breaking changes detected.\n")
        else:
            sys.stderr.write("Compatibility breaking changes detected!!!\n")
            breaking_changes.print_markdown(original_json["routines"], new_json["routines"])
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
