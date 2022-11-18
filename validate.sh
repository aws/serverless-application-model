#!/usr/bin/env bash
set -euxo pipefail

find integration/resources -name '*.yaml' | while read -r template; do
    jsonschema -i <(cfn-flip --json "${template}") samtranslator/schema/schema.json
done
