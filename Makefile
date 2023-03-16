target:
	$(info ${HELP_MESSAGE})
	@exit 0

init:
	pip install -e '.[dev]'

test:
	AWS_DEFAULT_REGION=us-east-1 pytest --cov samtranslator --cov-report term-missing --cov-fail-under 95 -n auto tests/

test-fast:
	pytest -x --cov samtranslator --cov-report term-missing --cov-fail-under 95 -n auto tests/

test-cov-report:
	pytest --cov samtranslator --cov-report term-missing --cov-report html --cov-fail-under 95 -n auto tests/
	open htmlcov/index.html &> /dev/null || true

integ-test:
	pytest --no-cov integration/

format:
	black setup.py samtranslator tests integration bin schema_source
	bin/transform-test-error-json-format.py --write tests/translator/output/error_*.json
	bin/json-format.py --write tests integration samtranslator/policy_templates_data
	bin/yaml-format.py --write tests
	bin/yaml-format.py --write integration --add-test-metadata

black:
	$(warning `make black` is deprecated, please use `make format`)
	# sleep for 5 seconds so the message can be seen.
	sleep 5
	make format

format-check:
	# Checking latest schema was generated (run `make schema` if this fails)
	mkdir -p .tmp
	python -m samtranslator.internal.schema_source.schema --sam-schema .tmp/sam.schema.json --cfn-schema schema_source/cloudformation.schema.json --unified-schema .tmp/schema.json
	diff -u schema_source/sam.schema.json .tmp/sam.schema.json
	diff -u samtranslator/schema/schema.json .tmp/schema.json
	black --check setup.py samtranslator tests integration bin schema_source
	bin/transform-test-error-json-format.py --check tests/translator/output/error_*.json
	bin/json-format.py --check tests integration samtranslator/policy_templates_data
	bin/yaml-format.py --check tests
	bin/yaml-format.py --check integration --add-test-metadata

black-check:
	$(warning `make black-check` is deprecated, please use `make format-check`)
	# sleep for 5 seconds so the message can be seen.
	sleep 5
	make format-check

lint:
	ruff samtranslator bin schema_source integration tests
	# mypy performs type check
	mypy --strict samtranslator bin schema_source
	# cfn-lint to make sure generated CloudFormation makes sense
	bin/run_cfn_lint.sh

lint-fix:
	ruff --fix samtranslator bin schema_source integration tests

prepare-companion-stack:
	pytest -v --no-cov integration/setup -m setup

fetch-schema-data:
	mkdir -p .tmp

	rm -rf .tmp/aws-sam-developer-guide
	git clone --depth 1 https://github.com/awsdocs/aws-sam-developer-guide.git .tmp/aws-sam-developer-guide

	rm -rf .tmp/aws-cloudformation-user-guide
	git clone --depth 1 https://github.com/awsdocs/aws-cloudformation-user-guide.git .tmp/aws-cloudformation-user-guide

	curl -o .tmp/cloudformation.schema.json https://raw.githubusercontent.com/awslabs/goformation/master/schema/cloudformation.schema.json

update-schema-data:
	# Parse docs
	bin/parse_docs.py .tmp/aws-sam-developer-guide/doc_source > samtranslator/internal/schema_source/sam-docs.json
	bin/parse_docs.py --cfn .tmp/aws-cloudformation-user-guide/doc_source > schema_source/cloudformation-docs.json

	# Add CloudFormation docs to CloudFormation schema
	python bin/add_docs_cfn_schema.py --schema .tmp/cloudformation.schema.json --docs schema_source/cloudformation-docs.json > schema_source/cloudformation.schema.json

schema:
	python -m samtranslator.internal.schema_source.schema --sam-schema schema_source/sam.schema.json --cfn-schema schema_source/cloudformation.schema.json --unified-schema samtranslator/schema/schema.json

# Update all schema data and schemas
schema-all: fetch-schema-data update-schema-data schema

# Command to run everytime you make changes to verify everything works
dev: test

# Verifications to run before sending a pull request
pr: format-check lint init dev

clean:
	rm -rf .tmp

define HELP_MESSAGE

Usage: $ make [TARGETS]

TARGETS
	init        Initialize and install the requirements and dev-requirements for this project.
	test        Run the Unit tests.
	integ-test  Run the Integration tests.
	dev         Run all development tests after a change.
	pr          Perform all checks before submitting a Pull Request.
	prepare-companion-stack    Create or update the companion stack for running integration tests.

endef
