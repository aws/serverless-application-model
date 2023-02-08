#!/usr/bin/env python
"""
Extract/compare public interfaces.

aws-sam-translator library hasn't documented public interfaces,
so we assume anything public by convention unless it is prefixed with "_".
(see https://peps.python.org/pep-0008/#descriptive-naming-styles)
This CLI tool helps automate the detection of compatibility-breaking changes.
"""
import argparse
import importlib
import inspect
import json
import os.path
import pkgutil
from typing import Any, Dict, Set, Union


class InterfaceScanner:
    def __init__(self) -> None:
        self.signatures: Dict[str, Union[inspect.Signature]] = {}
        self.variables: Set[str] = set()

    def scan_interfaces_recursively(self, module_name: str) -> None:
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
        There is no method to verify if a module attribute is a constant,
        After some experiment, here we assume if an attribute is a value
        (without `__module__`) and not a module itself is a constant.
        """
        for constant_name, _ in inspect.getmembers(
            importlib.import_module(module_name),
            lambda obj: not hasattr(obj, "__module__") and not inspect.ismodule(obj),
        ):
            if constant_name.startswith("_"):
                continue
            full_path = f"{module_name}.{constant_name}"
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
        for parameter in value.parameters.values():
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


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)

    subparsers = parser.add_subparsers(dest="command")
    extract = subparsers.add_parser("extract", help="Extract public interfaces")
    extract.add_argument("--module", help="The module to extract public interfaces", type=str, default="samtranslator")
    args = parser.parse_args()

    if args.command == "extract":
        scanner = InterfaceScanner()
        scanner.scan_interfaces_recursively(args.module)
        _print(scanner.signatures, scanner.variables)
    # TODO: handle compare
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
