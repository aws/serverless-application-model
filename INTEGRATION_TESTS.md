# AWS SAM integration tests

These tests run SAM against AWS services by translating SAM templates, deploying them to Cloud Formation and verifying the resulting objects.

They must run successfully under Python 3.

## Run the tests

### Prerequisites

#### User and rights

An Internet connection and an active AWS account are required to run the tests as they will interact with AWS services (most notably Cloud Formation) to create and update objects (Stacks, APIs, ...).

AWS credentials must be configured either through a [credentials file](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) or [environment variables](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html)

The user running the tests must have the following roles:

```
AmazonSQSFullAccess
AmazonSNSFullAccess
AmazonAPIGatewayAdministrator
AWSKeyManagementServiceFullAccess
AWSStepFunctionsFullAccess
```

If you plan on running the full tests suite, ensure that the user credentials you are running the tests with have a timeout of at least 30 minutes as the full suite can take more than 20 minutes to execute.

#### Initialize the development environment

If you haven't done so already, run the following command in a terminal at the root of the repository to initialize the development environment:

```
make init
```

### Setting up a companion stack

To run the tests, a companion stack first needs to be created. This stack houses some resources that are required by the tests, such as an S3 bucket.

```
make prepare-companion-stack
```

### Running all the tests

From the root of the repository, run:

```
make integ-test
```

### Running a specific test file

From the command line, run:

```
pytest --no-cov path/to/the/test_file.py
```

For example, from the root of the project:

```sh
pytest --no-cov integration/single/test_basic_api.py
```

### Running a specific test

From the command line, run:

```
pytest --no-cov path/to/the/test_file.py::test_class::test_method
```

For example, from the root of the project:

```sh
pytest --no-cov integration/single/test_basic_api.py::TestBasicApi::test_basic_api
```

*We don't measure coverage for integration tests.*

## Write a test

1. Add your test templates to the `integration/resources/templates` single or combination folder.
2. Write an expected json file for all the expected resources and add it to the `integration/resources/expected`.
3. (Optional) Add the resource files (zip, json, etc.) to `integration/resources/code` and update the dictionaries in `integration/helpers/file_resources.py`.
4. Write and add your python test code to the `integration` single or combination folder.
5. Run it!

## Skip tests for a specific service in a region

1. Add the service you want to skip to the `integration/config/region_service_exclusion.yaml` under the region
2. Add the @skipIf decorator to the test with the service name, take 'XRay' for example:
```@skipIf(current_region_does_not_support('XRay'), 'XRay is not supported in this testing region')```

## Directory structure

### Helpers

Common classes and tools used by tests.

```
+-- helpers/
|   +-- deployer           Tools to deploy to Cloud Formation
|   +-- base_test.py       Common class from which all test classes inherit
|   +-- file_resources.py  Files to upload to S3
|   +-- resource.py        Helper functions to manipulate resources
|   +-- template.py        Helper functions to translate the template
```

`base_test.py` contains `setUpClass` and `tearDownClass` methods to respectively upload and clean the `file_resources.py` resources (upload the files to a new S3 bucket, empty and delete this bucket).

### Resources

File resources used by tests.

```
+-- resources
|   +-- code               Files to upload to S3
|   +-- expected           Files describing the expected created resources
|   +-- templates          Source SAM templates to translate and deploy
```

The matching *expected* and *template* files should have the same name.

For example, the `test_basic_api` test in the class `tests_integ/single/test_basic_api.py` takes `templates/single/basic_api.yaml` SAM template as input and verifies its result against `expected/single/basic_api.json`.

### Single

Basic tests which interact with only one service should be put here.

### Combination

Tests which interact with multiple services should be put there.

### Tmp

This directory is created on the first run and contains temporary and intermediary files used by the tests: sam templates with substituted variable values, translated temporary cloud formation templates, ...
