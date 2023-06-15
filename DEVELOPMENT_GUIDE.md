Development Guide
=================

**Welcome hacker!**

This document will make your life easier by helping you setup a
development environment, IDEs, tests, coding practices, or anything that
will help you be more productive. If you found something is missing or
inaccurate, update this guide and send a Pull Request.

**Note**: `pyenv` currently only supports macOS and Linux. If you are a
Windows users, consider using [pipenv](https://docs.pipenv.org/).

1-click ready-to-hack IDE
-------------------------
For setting up a local development environment, we recommend using Gitpod - a service that allows you to spin up an in-browser Visual Studio Code-compatible editor, with everything set up and ready to go for development on this project. Just click the button below to create your private workspace:

[![Open in Gitpod](https://gitpod.io/button/open-in-gitpod.svg)](https://gitpod.io/#https://github.com/aws/serverless-application-model.git)

This will start a new Gitpod workspace, and immediately kick off a build of the code. Once it's done, you can start working.

Gitpod is free for 50 hours per month - make sure to stop your workspace when you're done (you can always resume it later, and it won't need to run the build again).


Environment setup
-----------------
### 1. Install Python versions

Our officially supported Python versions are 3.7, 3.8, 3.9 and 3.10. 
Our CI/CD pipeline is setup to run unit tests against Python 3 versions. Make sure you test it before sending a Pull Request.
See [Unit testing with multiple Python versions](#unit-testing-with-multiple-python-versions).

[pyenv](https://github.com/pyenv/pyenv) is a great tool to
easily setup multiple Python versions. For 

> Note: For Windows, type
> `export PATH="/c/Users/<user>/.pyenv/libexec:$PATH"` to add pyenv to
> your path.

1.  Install PyEnv -
    `curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash`
1. Restart shell so the path changes take effect - `exec $SHELL`
1.  `pyenv install 3.7.16`
1.  `pyenv install 3.8.16`
1.  `pyenv install 3.9.16`
1.  `pyenv install 3.10.9`
3.  Make Python versions available in the project:
    `pyenv local 3.7.16 3.8.16 3.9.16 3.10.9`

Note: also make sure the following lines were written into your `.bashrc` (or `.zshrc`, depending on which shell you are using):
```
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

### 2. Install additional tooling
#### Black
We format our code using [Black](https://github.com/python/black) and verify the source code is black compliant
during PR checks. Black will be installed automatically with `make init`.

After installing, you can run our formatting through our Makefile by `make format` or integrating Black directly in your favorite IDE (instructions
can be found [here](https://black.readthedocs.io/en/stable/editor_integration.html))
 
##### (Workaround) Integrating Black directly in your favorite IDE
Since black is installed in virtualenv, when you follow [this instruction](https://black.readthedocs.io/en/stable/editor_integration.html), `which black` might give you this

```bash
(sam37) $ where black
/Users/<username>/.pyenv/shims/black
```

However, IDEs such PyChaim (using FileWatcher) will have a hard time invoking `/Users/<username>/.pyenv/shims/black` 
and this will happen:

```
pyenv: black: command not found

The `black' command exists in these Python versions:
  3.7.9/envs/sam37
  sam37
``` 

A simple workaround is to use `/Users/<username>/.pyenv/versions/sam37/bin/black` 
instead of `/Users/<username>/.pyenv/shims/black`.

#### Pre-commit
If you don't wish to manually run black on each pr or install black manually, we have integrated black into git hooks through [pre-commit](https://pre-commit.com/).
After installing pre-commit, run `pre-commit install` in the root of the project. This will install black for you and run the black formatting on
commit.

### 3. Activate virtualenv

Virtualenv allows you to install required libraries outside of the
Python installation. A good practice is to setup a different virtualenv
for each project. [pyenv](https://github.com/pyenv/pyenv) comes with a
handy plugin that can create virtualenv.

Depending on the python version, the following commands would change to
be the appropriate python version.

1.  Create Virtualenv `sam37` for Python3.7: `pyenv virtualenv 3.7.9 sam37`
1.  Activate Virtualenv: `pyenv activate sam37`

### 4. Install dev version of SAM transform

We will install a development version of SAM transform from source into the
virtualenv.

1.  Activate Virtualenv: `pyenv activate sam37`
1.  Install dev version of SAM transform: `make init`

Running tests
-------------

### Unit testing with one Python version

If you're trying to do a quick run, it's ok to use the current python version.
Run `make test` or `make test-fast`. Once all tests pass make sure to run
`make pr` before sending out your PR.

### Unit testing with multiple Python versions

Currently, our officially supported Python versions are 3.7, 3.8, 3.9 and 3.10. For the most
part, code that works in Python3.7 will work in Pythons 3.8, 3.9 and 3.10. You only run into problems if you are
trying to use features released in a higher version (for example features introduced into Python3.10
will not work in Python3.9). If you want to test in many versions, you can create a virtualenv for
each version and flip between them (sourcing the activate script). Typically, we run all tests in
one python version locally and then have our ci (appveyor) run all supported versions.

### Transform tests

#### Successful transforms

Transform tests ensure a SAM template transforms into the expected CloudFormation template.

When adding new transform tests, we have provided a script to help generate the transform test input 
and output files in the correct directory given a `template.yaml` file.
```bash
python3 bin/add_transform_test.py --template-file template.yaml
```

This script will automatically generate the input and output files. It will guarantee that the output
files have the correct AWS partition (e.g. aws-cn, aws-us-gov). 

For `AWS::ApiGateway::RestApi`, the script will automatically append `REGIONAL` `EndpointConfiguration`.
To disable this feature, run the following command instead.
```bash
python3 bin/add_transform_test.py --template-file template.yaml --disable-api-configuration
```

The script automatically updates hardcoded ARN partitions to match the output partition. To disable this, use:
```bash
python3 bin/add_transform_test.py --template-file template.yaml --disable-update-partition
```

Please always check the generated output is as expected. This tool does not guarantee correct output.

#### Transform failures

To test a SAM template results in a specific transform error, add the SAM template under [`tests/translator/input`](https://github.com/aws/serverless-application-model/tree/develop/tests/translator/input), and a JSON file with the expected `errorMessage` as a top-level value under [`tests/translator/output`](https://github.com/aws/serverless-application-model/tree/develop/tests/translator/output). Both files must have the same basename and be prefixed with `error_` (e.g. `error_my_cool_template.yaml` for input, and `error_my_cool_template.json` for the expected error).

See https://github.com/aws/serverless-application-model/pull/2993 for an example.

### Integration tests

Integration tests are covered in detail in the [INTEGRATION_TESTS.md file](INTEGRATION_TESTS.md) of this repository.

## Development guidelines

1. **Do not resolve [intrinsic functions](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference.html).** Adding [`AWS::LanguageExtensions`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-languageextension-transform.html) before the `AWS::Serverless-2016-10-31` transform resolves most of them (see https://github.com/aws/serverless-application-model/issues/2533).
2. **Do not break backward compatibility.** A specific SAM template should always transform into the same CloudFormation template. A template that has previously deployed successfully should continue to do so. Do not change logical IDs. Add opt-in properties for breaking changes. There are some exceptions, such as changes that do not impact resources (e.g. [`Metadata`](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/metadata-section-structure.html)) or abstractions that can by design change over time.
3. **Stick as close as possible to the underlying CloudFormation properties.** This includes both property names and values. This ensures we can pass values to CloudFormation and let it handle any intrinsic functions. In some cases, it also allows us to pass all properties as-is to a resource, which means customers can always use the newest properties, and we don’t spend effort maintaining a duplicate set of properties.
4. **Only validate what’s necessary.** Do not validate properties if they’re passed directly to the underlying CloudFormation resource.
5. **Add [type hints](https://peps.python.org/pep-0484/) to new code.** Strict typing was enabled in https://github.com/aws/serverless-application-model/pull/2558 by sprinkling [`# type: ignore`](https://peps.python.org/pep-0484/#compatibility-with-other-uses-of-function-annotations) across the existing code. Don't do that for new code. Avoid `# type: ignore`s at all cost. Instead, add types to new functions, and ideally add types to existing code it uses as well.
6. **Do not use [`PropertyType`](https://github.com/aws/serverless-application-model/blob/c39c2807bbf327255de8abed8b8150b18c60f053/samtranslator/model/__init__.py#L13-L33) for new [`Resource`](https://github.com/aws/serverless-application-model/blob/13604cd2d9671cd6e774e5bfd610a03d82a08d76/samtranslator/model/__init__.py#L68) properties.**

   For new properties of SAM resources, use [`Property`](https://github.com/aws/serverless-application-model/blob/c5830b63857f52e540fec13b29f029458edc539a/samtranslator/model/__init__.py#L36-L45) or [`PassThroughProperty`](https://github.com/aws/serverless-application-model/blob/dd79f535500158baa8e367f081d6a12113497e45/samtranslator/model/__init__.py#L48-L56) instead of [`PropertyType`](https://github.com/aws/serverless-application-model/blob/c39c2807bbf327255de8abed8b8150b18c60f053/samtranslator/model/__init__.py#L13-L33). This avoids [sneaky bugs](https://github.com/aws/serverless-application-model/pull/2495#discussion_r976715242) and ensures valid templates do not cause transform failures.

   For new properties of CloudFormation resources, use [`GeneratedProperty`](https://github.com/aws/serverless-application-model/blob/79452f69bc1fcf918b8625c2f9005c74ab874801/samtranslator/model/__init__.py#L74-L82). It performs no runtime validation, reducing the risk of valid values causing transform failures.
7. **Write all new code under [`samtranslator/internal`](https://github.com/aws/serverless-application-model/tree/develop/samtranslator/internal) if possible.**  This ensures we don't increase our "public" library interface and cause unnecessary breakages to consumers. While Python doesn't have private access modifiers, we assume anything [by convention private](https://peps.python.org/pep-0008/#descriptive-naming-styles) or under `internal` to be internal code, not bound by typical expectations of backward compatibility.

Code conventions
----------------

Please follow these code conventions when making your changes. This will
align your code to the same conventions used in rest of the package and
make it easier for others to read/understand your code. Some of these
conventions are best practices that we have learnt over time.

-   Don\'t write any code in `__init__.py` file unless there is a really strong reason.
-   Module-level logger variable must be named as `LOG`
-   If your method wants to report a failure, it *must* raise a custom
    exception. Built-in Python exceptions like `TypeError`, `KeyError`
    are raised by Python interpreter and usually signify a bug in your
    code. Your method must not explicitly raise these exceptions because
    the caller has no way of knowing whether it came from a bug or not.
    Custom exceptions convey are must better at conveying the intent and
    can be handled appropriately by the caller. In HTTP lingo, custom
    exceptions are equivalent to 4xx (user\'s fault) and built-in
    exceptions are equivalent to 5xx (Service Fault)
-   Don't use `*args` or `**kwargs` unless there is a really strong
    reason to do so. You must explain the reason in great detail in
    docstrings if you were to use them.
-   Do not catch the broader `Exception`, unless you have a really
    strong reason to do. You must explain the reason in great detail in
    comments.

## Making schema changes

The AWS SAM specification includes a JSON schema (see https://github.com/aws/serverless-application-model/discussions/2645). All test templates must validate against it.

To add new properties, do the following:

1. Add the property to the relevant resource schema under [`samtranslator/internal/schema_source`](https://github.com/aws/serverless-application-model/tree/develop/samtranslator/internal/schema_source) (e.g. [`samtranslator/internal/schema_source/aws_serverless_function.py`](https://github.com/aws/serverless-application-model/blob/develop/samtranslator/internal/schema_source/aws_serverless_function.py) for `AWS::Serverless::Function`).
2. You can leave out the assignement part; it adds documentation to the schema properties. The team will take care of documentation updates once code changes are merged. Typically we update documentation by running `make update-schema-data`.
3. Run `make schema`.

Profiling
---------

Install snakeviz: `pip install snakeviz`

```bash
python -m cProfile -o sam_profile_results bin/sam-translate.py translate --template-file=tests/translator/input/alexa_skill.yaml --output-template=cfn-template.json
snakeviz sam_profile_results
```

Verifying transforms
--------------------

If you make changes to the transformer and want to verify the resulting CloudFormation template works as expected, you can transform your SAM template into a CloudFormation template using the following process:

```bash
# Optional: You only need to run the package command in certain cases; e.g. when your CodeUri specifies a local path
# Replace MY_TEMPLATE_PATH with the path to your template and MY_S3_BUCKET with an existing S3 bucket
aws cloudformation package --template-file MY_TEMPLATE_PATH/template.yaml --output-template-file output-template.yaml --s3-bucket MY_S3_BUCKET

# Transform your SAM template into a CloudFormation template
# Replace "output-template.yaml" if you didn't run the package command above or specified a different path for --output-template-file
bin/sam-translate.py --template-file=output-template.yaml

# Deploy your transformed CloudFormation template
# Replace MY_STACK_NAME with a unique name each time you deploy
aws cloudformation deploy --template-file cfn-template.json --capabilities CAPABILITY_NAMED_IAM --stack-name MY_STACK_NAME
```
