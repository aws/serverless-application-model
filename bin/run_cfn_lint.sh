#!/bin/sh
set -eux

VENV=.venv_cfn_lint

# Install to separate venv to avoid circular dependency; cfn-lint depends on samtranslator
# See https://github.com/aws/serverless-application-model/issues/1042
if [ ! -d "${VENV}" ]; then
    python3 -m venv "${VENV}"
fi

"${VENV}/bin/python" -m pip install cfn-lint --upgrade --quiet
# update cfn schema with retry logic (can fail due to network issues)
MAX_RETRIES=3
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if "${VENV}/bin/cfn-lint" -u; then
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
"${VENV}/bin/cfn-lint" --format parseable
