from pathlib import Path

_thisdir = Path(__file__).absolute().parent

# ./schema.json
SCHEMA_FILE = _thisdir / "schema.json"

# ./policy_templates.json
POLICY_TEMPLATES_FILE = _thisdir / "policy_templates.json"
