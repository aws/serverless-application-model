import os

_thisdir = os.path.dirname(os.path.abspath(__file__))

# ./schema.json
SCHEMA_FILE = os.path.join(_thisdir, "schema.json")

# ./policy_templates.json
POLICY_TEMPLATES_FILE = os.path.join(_thisdir, "policy_templates.json")
