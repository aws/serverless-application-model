import pydantic

from samtranslator.schema.common import LenientBaseModel

constr = pydantic.constr

# Match anything not containing Serverless
class Resource(LenientBaseModel):
    Type: constr(regex=r"^((?!::Serverless::).)*$")  # type: ignore
