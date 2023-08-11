from samtranslator.compat import pydantic
from samtranslator.internal.schema_source.common import LenientBaseModel

constr = pydantic.constr


# Anything goes if has string Type but is not AWS::Serverless::*
class Resource(LenientBaseModel):
    Type: constr(regex=r"^(?!AWS::Serverless::).+$")  # type: ignore
