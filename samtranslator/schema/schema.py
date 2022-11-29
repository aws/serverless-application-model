from __future__ import annotations

import json

from typing import Dict, Optional, Union


from samtranslator.schema.common import BaseModel, LenientBaseModel
from samtranslator.schema import (
    aws_serverless_simpletable,
    aws_serverless_application,
    aws_serverless_connector,
    aws_serverless_function,
    aws_serverless_statemachine,
    aws_serverless_layerversion,
    aws_serverless_api,
    aws_serverless_httpapi,
    any_cfn_resource,
)


class Globals(BaseModel):
    Function: Optional[aws_serverless_function.Globals]
    Api: Optional[aws_serverless_api.Globals]
    HttpApi: Optional[aws_serverless_httpapi.Globals]
    SimpleTable: Optional[aws_serverless_simpletable.Globals]


class Model(LenientBaseModel):
    Globals: Optional[Globals]
    Resources: Dict[
        str,
        Union[
            aws_serverless_connector.Resource,
            aws_serverless_function.Resource,
            aws_serverless_simpletable.Resource,
            aws_serverless_statemachine.Resource,
            aws_serverless_layerversion.Resource,
            aws_serverless_api.Resource,
            aws_serverless_httpapi.Resource,
            aws_serverless_application.Resource,
            any_cfn_resource.Resource,
        ],
    ]


def main() -> None:
    obj = Model.schema()

    # http://json-schema.org/understanding-json-schema/reference/schema.html#schema
    # https://github.com/pydantic/pydantic/issues/1478
    # Validated in https://github.com/aws/serverless-application-model/blob/5c82f5d2ae95adabc9827398fba8ccfc3dbe101a/tests/schema/test_validate_schema.py#L91
    obj["$schema"] = "http://json-schema.org/draft-04/schema#"

    print(json.dumps(obj, indent=2))


if __name__ == "__main__":
    main()
