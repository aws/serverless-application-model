NAME=samtranslator27
PYTHON_VERSION=2.7.14
PYENV := $(shell command -v pyenv 2> /dev/null)

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

# Setup the pyenv environment
setup: validation
	pyenv install $(PYTHON_VERSION)
	pyenv local $(PYTHON_VERSION) 
	pyenv virtualenv $(PYTHON_VERSION) $(NAME)
	make activate
	
# Activate the environment
activate:
	$(shell eval "$$(pyenv init -)" && eval "$$(pyenv virtualenv-init -)" && pyenv activate $(NAME) && pyenv local $(NAME))
	
# Clean the environment
clean:
	@find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf
	@test -f .coverage && rm .coverage || true
	@test -f .python-version && rm .python-version || true
	@rm -r ~/.pyenv/versions/*

init:
	pip install -r requirements-dev.txt -r requirements.txt

test:
	# Run unit tests
	# Fail if coverage falls below 96%
	pytest --cov samtranslator --cov-report term-missing --cov-fail-under 95 tests

build-docs:
	pip install -r docs/website/requirements.txt
	make -C docs/website html

# Command to run everytime you make changes to verify everything works
dev: test

# Verifications to run before sending a pull request
pr: init dev
