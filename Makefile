setup:
	curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
	pyenv install '2.7.14'
	pyenv local 2.7.14
	pyenv virtualenv 2.7.14 samtranslator27
	pyenv activate samtranslator27
	pyenv local samtranslator27

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
