#!/usr/bin/env bash
set -euxo pipefail

#find integration/resources -name '*.yaml' | while read -r template; do
echo integration/resources/templates/single/basic_state_machine_with_tags.yaml | while read -r template; do
    jsonschema -i <(cfn-flip --json "${template}") schema.json
done
