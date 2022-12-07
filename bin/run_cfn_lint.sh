#!/bin/sh
set -eux

VENV=.venv_cfn_lint

if [ ! -d "${VENV}" ]; then
    python3 -m venv "${VENV}"
    "${VENV}/bin/python" -m pip install cfn-lint==0.72.2
fi

"${VENV}/bin/cfn-lint"
