#!/usr/bin/env bash
set -euxo pipefail

make schema
#find integration/resources -name '*.yaml' | grep -v connector | while read -r template; do
echo integration/resources/templates/combination/connector_bucket_to_function_write.yaml | while read -r template; do
    jsonschema -i <(cfn-flip --json "${template}") samtranslator/schema/schema.json
done
