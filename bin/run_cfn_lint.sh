#!/bin/sh
set -eux

VENV=.venv_cfn_lint

# cfn-lint requires Python >= 3.10, which this project also requires (see python_requires in setup.py).
# Fail loudly rather than skipping: a silent "exit 0" here would turn the lint gate into a no-op on a
# misconfigured interpreter and report success without checking a single template.
PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
if [ "$PYTHON_MINOR" -lt 10 ]; then
    echo "ERROR: cfn-lint requires Python >= 3.10, but python3 is 3.${PYTHON_MINOR}. Use a supported interpreter." >&2
    exit 1
fi

# Install to separate venv to avoid circular dependency; cfn-lint depends on samtranslator
# See https://github.com/aws/serverless-application-model/issues/1042
# pinning 1.55.0 for now because there are some issues with 1.56.0
if command -v uv >/dev/null 2>&1; then
    [ -d "${VENV}" ] || uv venv --quiet "${VENV}"
    uv pip install --quiet --python "${VENV}/bin/python" cfn-lint==1.55.0
else
    [ -d "${VENV}" ] || python3 -m venv "${VENV}"
    "${VENV}/bin/python" -m pip install cfn-lint==1.55.0 --upgrade --quiet
fi
# update cfn schema with retry logic (can fail due to network issues)
# --regions us-east-1 avoids a cfn-lint bug where updating all regions causes a
# multiprocessing pickle error. See https://github.com/aws-cloudformation/cfn-lint/issues/4379
MAX_RETRIES=3
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if "${VENV}/bin/cfn-lint" -u --regions us-east-1; then
        echo "Successfully updated cfn-lint schema"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            echo "cfn-lint schema update failed, retrying... (attempt $RETRY_COUNT of $MAX_RETRIES)"
            sleep 2
        else
            echo "cfn-lint schema update failed after $MAX_RETRIES attempts"
            exit 1
        fi
    fi
done

# Lint the templates of .cfnlintrc.yaml in parallel, linting them in one process takes over a minute
TEMPLATES=$(mktemp)
trap 'rm -f "${TEMPLATES}"' EXIT
"${VENV}/bin/python" bin/list_cfn_lint_templates.py > "${TEMPLATES}"
# One batch per CPU, since every cfn-lint process loads the CloudFormation schemas again
CPUS=$(getconf _NPROCESSORS_ONLN)
BATCH_SIZE=$(( ($(wc -l < "${TEMPLATES}") + CPUS - 1) / CPUS ))
xargs -P "${CPUS}" -n "${BATCH_SIZE}" "${VENV}/bin/cfn-lint" --format parseable < "${TEMPLATES}"
