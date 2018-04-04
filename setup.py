#!/usr/bin/env python

from setuptools import setup, find_packages


with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='aws-sam-translator',
    version='1.4.0',
    description='AWS SAM Translator is a library that transform SAM templates into AWS CloudFormation templates',
    long_description=readme,
    author='Amazon Web Services',
    author_email='aws-sam-developers@amazon.com',
    url='https://github.com/awslabs/serverless-application-model',
    license=license,
    # Exclude all but the code folders
    packages=find_packages(exclude=('tests', 'docs', 'examples', 'versions')),
    keywords="AWS SAM Serverless Application Model",
)

