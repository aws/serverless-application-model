import copy
import json
import re
from typing import Any, Callable, Dict, Optional, TypeVar

from samtranslator.metrics.method_decorator import cw_timer
from samtranslator.model.apigatewayv2 import ApiGatewayV2Authorizer
from samtranslator.model.exceptions import InvalidDocumentException, InvalidTemplateException
from samtranslator.model.intrinsics import is_intrinsic, make_conditional, ref
from samtranslator.open_api.base_editor import BaseEditor
from samtranslator.utils.py27hash_fix import Py27Dict, Py27UniStr
from samtranslator.utils.types import Intrinsicable
from samtranslator.utils.utils import InvalidValueType, dict_deep_get

T = TypeVar("T")


# Wrap around copy.deepcopy to isolate time cost to deepcopy the doc.
_deepcopy: Callable[[T], T] = cw_timer(prefix="OpenApiEditor")(copy.deepcopy)


class OpenApiEditor(BaseEditor):
    """
    Wrapper class capable of parsing and generating OpenApi JSON.  This implements OpenApi spec just enough that SAM
    cares about. It is built to handle "partial Swagger" ie. Swagger that is incomplete and won't
    pass the Swagger spec. But this is necessary for SAM because it iteratively builds the Swagger starting from an
    empty skeleton.

    NOTE (hawflau): To ensure the same logical ID will be generated in Py3 as in Py2 for AWS::Serverless::HttpApi resource,
    we have to apply py27hash_fix. For any dictionary that is created within the swagger body, we need to initiate it
    with Py27Dict() instead of {}. We also need to add keys into the Py27Dict instance one by one, so that the input
    order could be preserved. This is a must for the purpose of preserving the dict key iteration order, which is
    essential for generating the same logical ID.
    """

    _X_APIGW_TAG_VALUE = "x-amazon-apigateway-tag-value"
    _X_APIGW_CORS = "x-amazon-apigateway-cors"
    _X_APIGW_ENDPOINT_CONFIG = "x-amazon-apigateway-endpoint-configuration"
    _DEFAULT_PATH = "$default"
    _DEFAULT_OPENAPI_TITLE = ref("AWS::StackName")

    # Attributes:
    _doc: Dict[str, Any]

    def __init__(self, doc: Optional[Dict[str, Any]]) -> None:
        """
        Initialize the class with a swagger dictionary. This class creates a copy of the Swagger and performs all
        modifications on this copy.

        :param dict doc: OpenApi document as a dictionary
        :raises InvalidDocumentException: If the input OpenApi document does not meet the basic OpenApi requirements.
        """
        if not doc or not OpenApiEditor.is_valid(doc):
            raise InvalidDocumentException(
                [
                    InvalidTemplateException(
                        "Invalid OpenApi document. Invalid values or missing keys for 'openapi' or 'paths' in 'DefinitionBody'."
                    )
                ]
            )

        self._doc = _deepcopy(doc)
        self.paths = self._doc["paths"]
        try:
            self.security_schemes = dict_deep_get(self._doc, "components.securitySchemes") or Py27Dict()
            self.definitions = dict_deep_get(self._doc, "definitions") or Py27Dict()
            self.tags = dict_deep_get(self._doc, "tags") or []
            self.info = dict_deep_get(self._doc, "info") or Py27Dict()
        except InvalidValueType as ex:
            raise InvalidDocumentException([InvalidTemplateException(f"Invalid OpenApi document: {ex!s}")]) from ex

    def is_integration_function_logical_id_match(self, path_name, method_name, logical_id):  # type: ignore[no-untyped-def]
        """
        Returns True if the function logical id in a lambda integration matches the passed
        in logical_id.
        If there are conditionals (paths, methods, uri), returns True only
        if they all match the passed in logical_id. False otherwise.
        If the integration doesn't exist, returns False
        :param path_name: name of the path
        :param method_name: name of the method
        :param logical_id: logical id to compare against
        """
        if not self.has_integration(path_name, method_name):
            return False
        method_name = self._normalize_method_name(method_name)

        for method_definition in self.iter_on_method_definitions_for_path_at_method(path_name, method_name, False):
            integration = method_definition.get(self._X_APIGW_INTEGRATION, Py27Dict())
            if not isinstance(integration, dict):
                raise InvalidDocumentException(
                    [
                        InvalidTemplateException(
                            f"Value of '{self._X_APIGW_INTEGRATION}' must be a dictionary according to Swagger spec."
                        )
                    ]
                )
            # Extract the integration uri out of a conditional if necessary
            uri = integration.get("uri")
            if not isinstance(uri, dict):
                return False
            for uri_content in self.get_conditional_contents(uri):
                arn = uri_content.get("Fn::Sub", "")

                # Extract lambda integration (${LambdaName.Arn}) and split ".Arn" off from it
                regex = r"([A-Za-z0-9]+\.Arn)"
                matches = re.findall(regex, arn)
                # Prevent IndexError when integration URI doesn't contain .Arn (e.g. a Function with
                # AutoPublishAlias translates to AWS::Lambda::Alias, which make_shorthand represents
                # as LogicalId instead of LogicalId.Arn).
                # TODO: Consistent handling of Functions with and without AutoPublishAlias (see #1901)
                if not matches or matches[0].split(".Arn")[0] != logical_id:
                    return False

        return True

    def add_lambda_integration(  # type: ignore[no-untyped-def] # noqa: PLR0913
        self, path, method, integration_uri, method_auth_config=None, api_auth_config=None, condition=None
    ):
        """
        Adds aws_proxy APIGW integration to the given path+method.

        :param string path: Path name
        :param string method: HTTP Method
        :param string integration_uri: URI for the integration.
        """

        method = self._normalize_method_name(method)
        if self.has_integration(path, method):
            # Not throwing an error- we will add lambda integrations to existing swagger if not present
            return

        self.add_path(path, method)

        # Wrap the integration_uri in a Condition if one exists on that function
        # This is necessary so CFN doesn't try to resolve the integration reference.
        if condition:
            integration_uri = make_conditional(condition, integration_uri)

        for path_item in self.get_conditional_contents(self.paths.get(path)):
            BaseEditor.validate_path_item_is_dict(path_item, path)
            # create as Py27Dict and insert key one by one to preserve input order
            if path_item[method] is None:
                path_item[method] = Py27Dict()
            path_item[method][self._X_APIGW_INTEGRATION] = Py27Dict()
            path_item[method][self._X_APIGW_INTEGRATION]["type"] = "aws_proxy"
            path_item[method][self._X_APIGW_INTEGRATION]["httpMethod"] = "POST"
            path_item[method][self._X_APIGW_INTEGRATION]["payloadFormatVersion"] = "2.0"
            path_item[method][self._X_APIGW_INTEGRATION]["uri"] = integration_uri

            if path == self._DEFAULT_PATH and method == self._X_ANY_METHOD:
                path_item[method]["isDefaultRoute"] = True

            # If 'responses' key is *not* present, add it with an empty dict as value
            path_item[method].setdefault("responses", Py27Dict())

            # If a condition is present, wrap all method contents up into the condition
            if condition:
                path_item[method] = make_conditional(condition, path_item[method])

    def iter_on_all_methods_for_path(self, path_name, skip_methods_without_apigw_integration=True):  # type: ignore[no-untyped-def]
        """
        Yields all the (method name, method definition) tuples for the path, including those inside conditionals.

        :param path_name: path name
        :param skip_methods_without_apigw_integration: if True, skips method definitions without apigw integration
        :yields list of (method name, method definition) tuples
        """
        for path_item in self.get_conditional_contents(self.paths.get(path_name)):
            BaseEditor.validate_path_item_is_dict(path_item, path_name)
            for method_name, method in path_item.items():
                for method_definition in self.get_conditional_contents(method):
                    BaseEditor.validate_method_definition_is_dict(method_definition, path_name, method_name)
                    if skip_methods_without_apigw_integration and not self.method_definition_has_integration(
                        method_definition
                    ):
                        continue
                    normalized_method_name = self._normalize_method_name(method_name)
                    yield normalized_method_name, method_definition

    def add_path_parameters_to_method(self, api, path, method_name, path_parameters):  # type: ignore[no-untyped-def]
        """
        Adds path parameters to this path + method

        :param dict api: Reference to the related Api's properties as defined in the template.
        :param string path: Path name
        :param string method_name: Method name
        :param list path_parameters: list of strings of path parameters
        """
        for method_definition in self.iter_on_method_definitions_for_path_at_method(path, method_name):
            # create path parameter list
            # add it here if it doesn't exist, merge with existing otherwise.
            parameters = method_definition.setdefault("parameters", [])
            for param in path_parameters:
                # find an existing parameter with this name if it exists
                existing_parameter = next(
                    (
                        existing_parameter
                        for existing_parameter in parameters
                        if existing_parameter.get("name") == param
                    ),
                    None,
                )
                if existing_parameter:
                    # overwrite parameter values for existing path parameter
                    existing_parameter["in"] = "path"
                    existing_parameter["required"] = True
                else:
                    # create as Py27Dict and insert keys one by one to preserve input order
                    parameter = Py27Dict()
                    parameter["name"] = Py27UniStr(param) if isinstance(param, str) else param
                    parameter["in"] = "path"
                    parameter["required"] = True
                    parameters.append(parameter)

    def add_payload_format_version_to_method(self, api, path, method_name, payload_format_version="2.0"):  # type: ignore[no-untyped-def]
        """
        Adds a payload format version to this path/method.

        :param dict api: Reference to the related Api's properties as defined in the template.
        :param string path: Path name
        :param string method_name: Method name
        :param string payload_format_version: payload format version sent to the integration
        """
        for method_definition in self.iter_on_method_definitions_for_path_at_method(path, method_name):
            method_definition[self._X_APIGW_INTEGRATION]["payloadFormatVersion"] = payload_format_version

    def add_authorizers_security_definitions(self, authorizers: Dict[str, ApiGatewayV2Authorizer]) -> None:
        """
        Add Authorizer definitions to the securityDefinitions part of Swagger.

        :param list authorizers: List of Authorizer configurations which get translated to securityDefinitions.
        """
        self.security_schemes = self.security_schemes or Py27Dict()

        for authorizer_name, authorizer in authorizers.items():
            self.security_schemes[authorizer_name] = authorizer.generate_openapi()

    def set_path_default_authorizer(
        self,
        path: str,
        default_authorizer: str,
        authorizers: Dict[str, ApiGatewayV2Authorizer],
    ) -> None:
        """
        Adds the default_authorizer to the security block for each method on this path unless an Authorizer
        was defined at the Function/Path/Method level. This is intended to be used to set the
        authorizer security restriction for all api methods based upon the default configured in the
        Serverless API.

        :param string path: Path name
        :param string default_authorizer: Name of the authorizer to use as the default. Must be a key in the
            authorizers param.
        :param dict authorizers: Dict of Authorizer configurations defined on the related Api.
        """
        for path_item in self.get_conditional_contents(self.paths.get(path)):
            BaseEditor.validate_path_item_is_dict(path_item, path)
            for method_name, method in path_item.items():
                normalized_method_name = self._normalize_method_name(method_name)
                # Excluding parameters section
                if normalized_method_name == "parameters":
                    continue
                if normalized_method_name != "options":
                    normalized_method_name = self._normalize_method_name(method_name)
                    # It is possible that the method could have two definitions in a Fn::If block.
                    if normalized_method_name not in path_item:
                        raise InvalidDocumentException(
                            [
                                InvalidTemplateException(
                                    f"Could not find {normalized_method_name} in {path} within DefinitionBody."
                                )
                            ]
                        )
                    for method_definition in self.get_conditional_contents(method):
                        # If no integration given, then we don't need to process this definition (could be AWS::NoValue)
                        BaseEditor.validate_method_definition_is_dict(method_definition, path, method_name)
                        if not self.method_definition_has_integration(method_definition):
                            continue
                        existing_security = method_definition.get("security")
                        if existing_security:
                            continue

                        security_dict = {}
                        security_dict[default_authorizer] = self._get_authorization_scopes(
                            authorizers, default_authorizer
                        )
                        authorizer_security = [security_dict]

                        security = authorizer_security

                        if security:
                            method_definition["security"] = security

    def add_auth_to_method(self, path, method_name, auth, api):  # type: ignore[no-untyped-def]
        """
        Adds auth settings for this path/method. Auth settings currently consist of Authorizers
        but this method will eventually include setting other auth settings such as Resource Policy, etc.
        This is used to configure the security for individual functions.

        :param string path: Path name
        :param string method_name: Method name
        :param dict auth: Auth configuration such as Authorizers
        :param dict api: Reference to the related Api's properties as defined in the template.
        """
        method_authorizer = auth and auth.get("Authorizer")
        authorization_scopes = auth.get("AuthorizationScopes", [])
        api_auth = api and api.get("Auth")
        authorizers = api_auth and api_auth.get("Authorizers")
        if method_authorizer:
            self._set_method_authorizer(path, method_name, method_authorizer, authorizers, authorization_scopes)  # type: ignore[no-untyped-call]

    def _set_method_authorizer(self, path, method_name, authorizer_name, authorizers, authorization_scopes=None):  # type: ignore[no-untyped-def]
        """
        Adds the authorizer_name to the security block for each method on this path.
        This is used to configure the authorizer for individual functions.

        :param string path: Path name
        :param string method_name: Method name
        :param string authorizer_name: Name of the authorizer to use. Must be a key in the
            authorizers param.
        :param list authorization_scopes: list of strings that are the auth scopes for this method
        """
        if authorization_scopes is None:
            authorization_scopes = []

        for method_definition in self.iter_on_method_definitions_for_path_at_method(path, method_name):
            security_dict = {}  # type: ignore[var-annotated]
            security_dict[authorizer_name] = []

            # Neither the NONE nor the AWS_IAM built-in authorizers support authorization scopes.
            if authorizer_name not in ["NONE", "AWS_IAM"]:
                authorizer = authorizers.get(authorizer_name, Py27Dict())
                if not isinstance(authorizer, dict):
                    raise InvalidDocumentException(
                        [InvalidTemplateException(f"Type of authorizer '{authorizer_name}' must be a dictionary")]
                    )
                method_authorization_scopes = authorizer.get("AuthorizationScopes")
                if authorization_scopes:
                    method_authorization_scopes = authorization_scopes
                if authorizers[authorizer_name] and method_authorization_scopes:
                    security_dict[authorizer_name] = method_authorization_scopes

            authorizer_security = [security_dict]

            existing_security = method_definition.get("security", [])
            if not isinstance(existing_security, list):
                raise InvalidDocumentException(
                    [InvalidTemplateException(f"Type of security for path {path} method {method_name} must be a list")]
                )
            # This assumes there are no authorizers already configured in the existing security block
            security = existing_security + authorizer_security
            if security:
                method_definition["security"] = security

    def add_tags(self, tags: Dict[str, Intrinsicable[str]]) -> None:
        """
        Adds tags to the OpenApi definition using an ApiGateway extension for tag values.

        :param dict tags: dictionary of tagName:tagValue pairs.
        """
        for name, value in tags.items():
            # verify the tags definition is in the right format
            if not isinstance(self.tags, list):
                raise InvalidDocumentException(
                    [
                        InvalidTemplateException(
                            f"Tags in OpenApi DefinitionBody needs to be a list. {self.tags} is a {type(self.tags).__name__} not a list."
                        )
                    ]
                )
            # find an existing tag with this name if it exists
            existing_tag = next((existing_tag for existing_tag in self.tags if existing_tag.get("name") == name), None)
            if existing_tag:
                # overwrite tag value for an existing tag
                existing_tag[self._X_APIGW_TAG_VALUE] = value
            else:
                # create as Py27Dict and insert key one by one to preserve input order
                tag = Py27Dict()
                tag["name"] = name
                tag[self._X_APIGW_TAG_VALUE] = value
                self.tags.append(tag)

    def add_endpoint_config(self, disable_execute_api_endpoint: Optional[Intrinsicable[bool]]) -> None:
        """Add endpoint configuration to _X_APIGW_ENDPOINT_CONFIG header in open api definition

        Following this guide:
        https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-swagger-extensions-endpoint-configuration.html
        https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-apigatewayv2-api.html#cfn-apigatewayv2-api-disableexecuteapiendpoint

        :param boolean disable_execute_api_endpoint: Specifies whether clients can invoke your API by using the default execute-api endpoint.

        """

        DISABLE_EXECUTE_API_ENDPOINT = "disableExecuteApiEndpoint"

        servers_configurations = self._doc.get(self._SERVERS, [Py27Dict()])
        for config in servers_configurations:
            if not isinstance(config, dict):
                raise InvalidDocumentException(
                    [
                        InvalidTemplateException(
                            f"Value of '{self._SERVERS}' item must be a dictionary according to Swagger spec."
                        )
                    ]
                )
            endpoint_configuration = config.get(self._X_APIGW_ENDPOINT_CONFIG, {})
            endpoint_configuration[DISABLE_EXECUTE_API_ENDPOINT] = disable_execute_api_endpoint
            config[self._X_APIGW_ENDPOINT_CONFIG] = endpoint_configuration

        self._doc[self._SERVERS] = servers_configurations

    def add_cors(  # type: ignore[no-untyped-def] # noqa: PLR0913
        self,
        allow_origins,
        allow_headers=None,
        allow_methods=None,
        expose_headers=None,
        max_age=None,
        allow_credentials=None,
    ):
        """
        Add CORS configuration to this Api to _X_APIGW_CORS header in open api definition

        Following this guide:
        https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-cors.html
        https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-apigatewayv2-api-cors.html

        :param list/dict allowed_origins: Comma separate list of allowed origins.
            Value can also be an intrinsic function dict.
        :param list/dict allowed_headers: Comma separated list of allowed headers.
            Value can also be an intrinsic function dict.
        :param list/dict allowed_methods: Comma separated list of allowed methods.
            Value can also be an intrinsic function dict.
        :param list/dict expose_headers: Comma separated list of allowed methods.
            Value can also be an intrinsic function dict.
        :param integer/dict max_age: Maximum duration to cache the CORS Preflight request. Value is set on
            Access-Control-Max-Age header. Value can also be an intrinsic function dict.
        :param bool/None allowed_credentials: Flags whether request is allowed to contain credentials.
        """
        ALLOW_ORIGINS = "allowOrigins"
        ALLOW_HEADERS = "allowHeaders"
        ALLOW_METHODS = "allowMethods"
        EXPOSE_HEADERS = "exposeHeaders"
        MAX_AGE = "maxAge"
        ALLOW_CREDENTIALS = "allowCredentials"
        cors_headers = [ALLOW_ORIGINS, ALLOW_HEADERS, ALLOW_METHODS, EXPOSE_HEADERS, MAX_AGE, ALLOW_CREDENTIALS]
        cors_configuration = self._doc.get(self._X_APIGW_CORS, {})
        if not isinstance(cors_configuration, dict):
            raise InvalidDocumentException(
                [
                    InvalidTemplateException(
                        f"Value of '{self._X_APIGW_CORS}' must be a dictionary according to Swagger spec."
                    )
                ]
            )

        # intrinsics will not work if cors configuration is defined in open api and as a property to the HttpApi
        if allow_origins and is_intrinsic(allow_origins):
            cors_configuration_string = json.dumps(allow_origins)
            for header in cors_headers:
                # example: allowOrigins to AllowOrigins
                keyword = header[0].upper() + header[1:]
                cors_configuration_string = cors_configuration_string.replace(keyword, header)
            cors_configuration_dict = json.loads(cors_configuration_string)
            cors_configuration.update(cors_configuration_dict)

        else:
            if allow_origins:
                cors_configuration[ALLOW_ORIGINS] = allow_origins
            if allow_headers:
                cors_configuration[ALLOW_HEADERS] = allow_headers
            if allow_methods:
                cors_configuration[ALLOW_METHODS] = allow_methods
            if expose_headers:
                cors_configuration[EXPOSE_HEADERS] = expose_headers
            if max_age is not None:
                cors_configuration[MAX_AGE] = max_age
            if allow_credentials is True:
                cors_configuration[ALLOW_CREDENTIALS] = allow_credentials

        self._doc[self._X_APIGW_CORS] = cors_configuration

    def add_description(self, description: Intrinsicable[str]) -> None:
        """Add description in open api definition, if it is not already defined

        :param string description: Description of the API
        """
        if self.info.get("description"):
            return
        self.info["description"] = description

    def add_title(self, title: Intrinsicable[str]) -> None:
        """Add title in open api definition, if it is not already defined

        :param string description: Description of the API
        """
        if self.info.get("title") != OpenApiEditor._DEFAULT_OPENAPI_TITLE:
            return
        self.info["title"] = title

    def has_api_gateway_cors(self) -> bool:
        if self._doc.get(self._X_APIGW_CORS):
            return True
        return False

    @property
    def openapi(self) -> Dict[str, Any]:
        """
        Returns a **copy** of the OpenApi specification as a dictionary.

        :return dict: Dictionary containing the OpenApi specification
        """

        # Make sure any changes to the paths are reflected back in output
        self._doc["paths"] = self.paths

        if self.tags:
            self._doc["tags"] = self.tags

        if self.security_schemes:
            self._doc.setdefault("components", Py27Dict())
            if not self._doc["components"]:
                # explicitly set to dict to account for scenario where
                # 'components' is explicitly set to None
                self._doc["components"] = Py27Dict()
            self._doc["components"]["securitySchemes"] = self.security_schemes

        if self.info:
            self._doc["info"] = self.info

        return _deepcopy(self._doc)

    @staticmethod
    def is_valid(data: Any) -> bool:
        """
        Checks if the input data is a OpenApi document

        :param dict data: Data to be validated
        :return: True, if data is valid OpenApi
        """

        if bool(data) and isinstance(data, dict) and isinstance(data.get("paths"), dict) and bool(data.get("openapi")):
            return OpenApiEditor.safe_compare_regex_with_string(OpenApiEditor._OPENAPI_VERSION_3_REGEX, data["openapi"])
        return False

    @staticmethod
    def gen_skeleton() -> Py27Dict:
        """
        Method to make an empty swagger file, with just some basic structure. Just enough to pass validator.

        :return dict: Dictionary of a skeleton swagger document
        """
        # create as Py27Dict and insert key one by one to preserve input order
        skeleton = Py27Dict()
        skeleton["openapi"] = "3.0.1"
        skeleton["info"] = Py27Dict()
        skeleton["info"]["version"] = "1.0"
        skeleton["info"]["title"] = OpenApiEditor._DEFAULT_OPENAPI_TITLE
        skeleton["paths"] = Py27Dict()
        return skeleton

    @staticmethod
    def get_path_without_trailing_slash(path):  # type: ignore[no-untyped-def]
        sub = re.sub(r"{([a-zA-Z0-9._-]+|proxy\+)}", "*", path)
        if isinstance(path, Py27UniStr):
            return Py27UniStr(sub)
        return sub
