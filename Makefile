PYTHON = python3
VENV = .venv
BIN = $(VENV)/bin

target:
	$(info ${HELP_MESSAGE})
	@exit 0

init:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install -e '.[dev]'

test:
	AWS_DEFAULT_REGION=us-east-1 $(BIN)/pytest --cov samtranslator --cov-report term-missing --cov-fail-under 95 -n auto tests/*

test-fast:
	$(BIN)/pytest -x --cov samtranslator --cov-report term-missing --cov-fail-under 95 -n auto tests/*

test-cov-report:
	$(BIN)/pytest --cov samtranslator --cov-report term-missing --cov-report html --cov-fail-under 95 tests/*

integ-test:
	$(BIN)/pytest --no-cov integration/*

black:
	$(BIN)/black setup.py samtranslator/* tests/* integration/* bin/*.py

black-check:
	$(BIN)/black --check setup.py samtranslator/* tests/* integration/* bin/*.py

lint:
	# Linter performs static analysis to catch latent bugs
	$(BIN)/pylint --rcfile .pylintrc samtranslator
	# mypy performs type check
	$(BIN)/mypy samtranslator

prepare-companion-stack:
	$(BIN)/pytest -v --no-cov integration/setup -m setup

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
