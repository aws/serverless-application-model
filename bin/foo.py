import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", help="CloudFormation resource specification", required=True, type=Path)
    args = parser.parse_args()

    spec = json.loads(args.spec.read_text())

    m = {}

    for s in ["PropertyTypes", "ResourceTypes"]:
        for k, v in spec[s].items():
            if k in m:
                raise Exception(f"{k} already exists")
            m[k] = v["Documentation"]

    print(json.dumps(m, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
