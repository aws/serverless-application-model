target:
	$(info ${HELP_MESSAGE})
	@exit 0

init:
	pip install -e '.[dev]'

test:
	AWS_DEFAULT_REGION=us-east-1 pytest --cov samtranslator --cov-report term-missing --cov-fail-under 95 -n auto tests/*

test-fast:
	pytest -x --cov samtranslator --cov-report term-missing --cov-fail-under 95 -n auto tests/*

test-cov-report:
	pytest --cov samtranslator --cov-report term-missing --cov-report html --cov-fail-under 95 tests/*

integ-test:
	pytest --no-cov integration/*

black:
	black setup.py samtranslator/* tests/* integration/* bin/*.py
	bin/json-format.py --write tests

black-check:
	black --check setup.py samtranslator/* tests/* integration/* bin/*.py
	bin/json-format.py --check tests

lint:
	# Linter performs static analysis to catch latent bugs
	pylint --rcfile .pylintrc samtranslator
	# mypy performs type check
	mypy --strict samtranslator bin

prepare-companion-stack:
	pytest -v --no-cov integration/setup -m setup

# Command to run everytime you make changes to verify everything works
dev: test

# Verifications to run before sending a pull request
pr: black-check lint init dev

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
