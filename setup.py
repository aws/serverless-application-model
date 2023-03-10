# -*- coding: utf-8 -*-
#
# setup.py
#
# Copyright 2018 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""
AWS SAM Serverless Application Model
"""
import io
import os
import re

from setuptools import setup, find_packages


def read(*filenames, **kwargs):
    encoding = kwargs.get("encoding", "utf-8")
    sep = kwargs.get("sep", os.linesep)
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)


def read_version():
    content = read(os.path.join(os.path.dirname(__file__), "samtranslator", "__init__.py"))
    return re.search(r"__version__ = \"([^']+)\"", content).group(1)


def read_requirements(req="base.txt"):
    content = read(os.path.join("requirements", req))
    return [line for line in content.split(os.linesep) if not line.strip().startswith("#")]


setup(
    name="aws-sam-translator",
    version=read_version(),
    description="AWS SAM Translator is a library that transform SAM templates into AWS CloudFormation templates",
    long_description=read("README.md"),
    long_description_content_type="text/markdown",
    author="Amazon Web Services",
    author_email="aws-sam-developers@amazon.com",
    url="https://github.com/awslabs/serverless-application-model",
    license="Apache License 2.0",
    # Exclude all but the code folders
    packages=find_packages(
        exclude=(
            "bin",
            "bin.*",
            "docs",
            "examples",
            "integration",
            "integration.*",
            "schema_source",
            "schema_source.*",
            "tests",
            "tests.*",
            "versions",
        )
    ),
    license_files=(
        "LICENSE",
        "NOTICE",
        "THIRD_PARTY_LICENSES",
    ),
    python_requires=">=3.7, <=4.0, !=4.0",
    install_requires=read_requirements("base.txt"),
    include_package_data=True,
    extras_require={"dev": read_requirements("dev.txt")},
    keywords="AWS SAM Serverless Application Model",
    classifiers=[
        # https://pypi.org/classifiers/
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Environment :: Other Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Utilities",
    ],
)
