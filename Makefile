NAME=samtranslator27
PYTHON_VERSION=2.7.14
CODE_COVERAGE=95
PYENV := $(shell command -v pyenv 2> /dev/null)

target:
	$(info ${HELP_MESSAGE})
	@exit 0

# Make sure that pyenv is configured properly and that we can use it in our setup target.
validation:
ifndef PYENV
    $(error "make sure pyenv is accessible in your path, (usually by adding to PATH variable in bash_profile, zshrc, or other locations based on your platform) See: https://github.com/pyenv/pyenv#installation for the installation insructions.")
endif
ifndef PYENV_SHELL
	$(error "Add 'pyenv init' to your shell to enable shims and autocompletion, (usually by adding to your bash_profile, zshrc, or other locations based on your platform)")
endif
ifndef PYENV_VIRTUALENV_INIT
	$(error "Add 'pyenv virtualenv-init' to your shell to enable shims and autocompletion, (usually by adding to your bash_profile, zshrc, or other locations based on your platform)")
endif

install:
	$(info [*] Install pyenv using https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer...)
	@curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer 2> /dev/null | bash

setup: validation
	$(info [*] Download and install python $(PYTHON_VERSION)...)
	@pyenv install $(PYTHON_VERSION)
	@pyenv local $(PYTHON_VERSION) 
	$(info [*] Create virtualenv $(NAME) using python $(PYTHON_VERSION)...)
	@pyenv virtualenv $(PYTHON_VERSION) $(NAME)
	@$(MAKE) activate
	
activate:
	$(info [*] Activate virtualenv $(NAME)...)
	$(shell eval "$$(pyenv init -)" && eval "$$(pyenv virtualenv-init -)" && pyenv activate $(NAME) && pyenv local $(NAME))
	
init:
	$(info [*] Install requirements...)
	@pip install -r requirements/dev.txt -r requirements/base.txt

test:
	$(info [*] Run the unit test with minimum code coverage of $(CODE_COVERAGE)%...)
	@pytest --cov samtranslator --cov-report term-missing --cov-fail-under $(CODE_COVERAGE) tests

build-docs:
	$(info [*] Build documentation...)
	@pip install -r docs/website/requirements.txt
	@$(MAKE) -C docs/website html

# Command to run everytime you make changes to verify everything works
dev: test

# Verifications to run before sending a pull request
pr: init dev

define HELP_MESSAGE

Usage: $ make [TARGETS]

TARGETS
	install     Install pyenv using the pyenv-installer.
	setup       Download, install and activate a virtualenv for this project.
	activate    Activate the virtual environment for this project.
	init        Initialize and install the requirements and dev-requirements for this project.
	test        Run the Unit tests.
	dev         Run all development tests after a change.
	build-docs  Generate the documentation.
	pr          Perform all checks before submitting a Pull Request.

endef