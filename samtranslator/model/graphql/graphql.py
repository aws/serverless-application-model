from typing import Optional

from samtranslator.internal.schema_source.aws_serverless_graphqlapi import (
    Function,
    Properties,
    Resolver,
)


class Defaults:
    """Wrapper for defaults.

    Stores separately defaults for Resolvers and Functions.
    """

    def __init__(
        self,
        resolver: Optional[Resolver] = None,
        function: Optional[Function] = None,
    ):
        self.resolver = resolver
        self.function = function

    @classmethod
    def from_sam_graphql(cls, model: Properties) -> "Defaults":
        """Create Defaults from SAM GraphQLApi model.

        SAM GraphQLApi object has optional Defaults property which allows to set defaults for all
        Functions, Resolvers, or some properties like Runtime for both Functions and Resolvers.
        This constructor method parses SAM GraphQLApi Defaults and merges common default properties
        into both Resolvers and Functions defaults before storing them separately.

        Parameters
        ----------
        model
            SAM GraphQLApi model.

        Returns
        -------
            Defaults instance.
        """
        if model.Defaults:
            resolver_and_function_defaults = model.Defaults.dict(exclude={"Resolvers", "Functions"})

            resolver_defaults = {
                **resolver_and_function_defaults,
                **model.Defaults.dict(exclude_none=True).get("Resolvers", {}),
            }

            function_defaults = {
                **resolver_and_function_defaults,
                **model.Defaults.dict(exclude_none=True).get("Functions", {}),
            }

            return cls(
                resolver=Resolver.parse_obj(resolver_defaults),
                function=Function.parse_obj(function_defaults),
            )

        return cls()
