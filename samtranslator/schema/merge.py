import argparse
import json
from pathlib import Path
from typing import Any, Dict


def extend_with_cfn_schema(sam_schema: Dict[str, Any], cfn_schema: Dict[str, Any]) -> None:
    # TODO: Ensure not overwriting
    sam_schema["definitions"].update(cfn_schema["definitions"])

    cfn_props = cfn_schema["properties"]
    sam_schema["properties"]["Resources"]["additionalProperties"]["anyOf"].extend(
        cfn_props["Resources"]["patternProperties"]["^[a-zA-Z0-9]+$"]["anyOf"]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sam_schema", type=Path)
    parser.add_argument("cfn_schema", type=Path)
    args = parser.parse_args()

    sam_schema = json.loads(args.sam_schema.read_bytes())
    cfn_schema = json.loads(args.cfn_schema.read_bytes())

    extend_with_cfn_schema(sam_schema, cfn_schema)

    print(json.dumps(sam_schema, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
