# AWS SAM integration tests

These integration tests test SAM against AWS services by translating SAM templates, deploying them to Cloud Formation and verifying the resulting objects.

They must run under Python 2 and 3.

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
AWSKeyManagementServicePowerUser
AWSStepFunctionsFullAccess
```

#### Initialize the development environment

If you haven't done so already, run the following command in a terminal at the root of the repository to initialize the development environment:

```
make init
```

### Running all the tests

From the root of the repository, run:

```
make test-integ
```

This can take multiple minutes to execute.

### Running a specific test file

From the command line, run:

```
pytest --no-cov path/to/the/test_file.py
```

Example:

```sh
pytest --no-cov tests_integ/single/test_basic_api.py
```

*We don't measure coverage for integration tests.*

## Architecture

### Helpers

Common classes and tools used by tests.

```
+-- helpers/
|   +-- deployer           Tools to deploy to Cloud Formation
|   +-- base_test.py       Common class from which all test classes inherit
|   +-- file_resources.py  Files to upload to S3
|   +-- helpers.py         Miscellaneous helpers
```

`base_test.py` runs setup methods before all tests in a class to upload the `file_resources.py` resources to an S3 bucket and after all tests to empty and delete this bucket.

### Resources

File resources used by tests

```
+-- resources
|   +-- code               Files to upload to S3
|   +-- expected           Files describing the expected created resources
|   +-- templates          Source SAM templates to translate and deploy
```

The matching *expected* and *template* files should have the same name.

Example: `single/test_basic_api.py` takes the `templates/single/basic_api.yaml` file as input SAM template and tests it against the `expected/single/basic_api.json` file.

### Single

Simple tests

### Tmp

This directory will be created on the first run and will contain temporary and intermediary files used by the tests: sam templates with substituted variable values, translated temporary cloud formation templates, ...
