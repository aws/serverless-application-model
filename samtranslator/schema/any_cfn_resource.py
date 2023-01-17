import pydantic

from samtranslator.schema.common import LenientBaseModel

constr = pydantic.constr

# Anything goes if has string Type but is not AWS::Serverless::*
class Resource(LenientBaseModel):
    Type: constr(regex=r"^(?!AWS::Serverless::).+$")  # type: ignore
