from samtranslator.internal.schema_source.aws_serverless_graphqlapi import Properties
from samtranslator.model.graphql.graphql import Defaults


def test_no_defaults():
    model = Properties.parse_obj({"Auth": {"Type": "AWS_IAM"}})
    defaults = Defaults.from_sam_graphql(model)
    assert defaults.resolver is None
    assert defaults.function is None


def test_common_only():
    model = Properties.parse_obj(
        {
            "Auth": {"Type": "AWS_IAM"},
            "Defaults": {"Runtime": {"Name": "CommonRuntime", "Version": "1"}},
        }
    )
    defaults = Defaults.from_sam_graphql(model)

    assert defaults.resolver is not None
    assert (
        defaults.resolver.Runtime is not None
        and defaults.resolver.Runtime.Name == "CommonRuntime"
        and defaults.resolver.Runtime.Version == "1"
    )

    assert defaults.function is not None
    assert (
        defaults.function.Runtime is not None
        and defaults.function.Runtime.Name == "CommonRuntime"
        and defaults.function.Runtime.Version == "1"
    )


def test_common_and_individual():
    model = Properties.parse_obj(
        {
            "Auth": {"Type": "AWS_IAM"},
            "Defaults": {
                "Runtime": {"Name": "CommonRuntime", "Version": "1"},
                "Resolvers": {"InlineCode": "super code"},
                "Functions": {"DataSourceName": "SomeAppSyncDataSource"},
            },
        }
    )
    defaults = Defaults.from_sam_graphql(model)

    assert defaults.resolver is not None
    assert (
        defaults.resolver.Runtime is not None
        and defaults.resolver.Runtime.Name == "CommonRuntime"
        and defaults.resolver.Runtime.Version == "1"
    )
    assert defaults.resolver.InlineCode == "super code"

    assert defaults.function is not None
    assert (
        defaults.function.Runtime is not None
        and defaults.function.Runtime.Name == "CommonRuntime"
        and defaults.function.Runtime.Version == "1"
    )
    assert defaults.function.DataSourceName == "SomeAppSyncDataSource"
