#! /bin/bash


PROJECT_DIR=$(realpath $0)
PYTHONPATH=${PROJECT_DIR}

coverage run -m unittest discover --quiet --start-directory tests
coverage report -m pycom/*.py bin/terminal
flake8 pycom/*.py bin/terminal
mypy --no-error-summary pycom
pylint pycom/*.py bin/terminal
bandit -qr pycom
