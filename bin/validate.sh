#!/usr/bin/env bash
set -euxo pipefail

# TODO: Enable the valid templates
# TODO: Switch to way-faster Python script
find tests/translator/input -type f -name '*.yaml' | grep -v error_ | grep -v unsupported_resources | grep -v resource_with_invalid_type | shuf | while read -r template; do
    jsonschema -i <(cfn-flip --json "${template}") samtranslator/schema/schema.json
done
