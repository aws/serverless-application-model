import os
import pkgutil
import subprocess
import sys
from pathlib import Path
from typing import List
from unittest import TestCase

from parameterized import parameterized

_PROJECT_ROOT = Path(__file__).parent.parent


def scan_modules_recursively(module_name: str = "samtranslator") -> List[str]:
    all_modules: List[str] = [module_name]
    for submodule in pkgutil.iter_modules([os.path.join(_PROJECT_ROOT, module_name.replace(".", os.path.sep))]):
        submodule_name = module_name + "." + submodule.name
        all_modules += scan_modules_recursively(submodule_name)
    return all_modules


class TestImport(TestCase):
    @parameterized.expand([(module_path,) for module_path in scan_modules_recursively()])
    def test_import(self, module_path: str):
        pipe = subprocess.Popen([sys.executable, "-c", f"import {module_path}"], stderr=subprocess.PIPE)
        _, stderr = pipe.communicate()
        self.assertEqual(pipe.returncode, 0, stderr.decode("utf-8"))
