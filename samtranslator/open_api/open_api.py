import copy
import re
from six import string_types

from samtranslator.model.intrinsics import ref
from samtranslator.model.intrinsics import make_conditional
from samtranslator.model.intrinsics import is_intrinsic
from samtranslator.model.exceptions import InvalidDocumentException, InvalidTemplateException
import json


class OpenApiEditor(object):
    """
    Wrapper class capable of parsing and generating OpenApi JSON.  This implements OpenApi spec just enough that SAM
    cares about. It is built to handle "partial Swagger" ie. Swagger that is incomplete and won't
    pass the Swagger spec. But this is necessary for SAM because it iteratively builds the Swagger starting from an
    empty skeleton.
    """

    _X_APIGW_INTEGRATION = "x-amazon-apigateway-integration"
    _X_APIGW_TAG_VALUE = "x-amazon-apigateway-tag-value"
    _X_APIGW_CORS = "x-amazon-apigateway-cors"
    _CONDITIONAL_IF = "Fn::If"
    _X_ANY_METHOD = "x-amazon-apigateway-any-method"
    _ALL_HTTP_METHODS = ["OPTIONS", "GET", "HEAD", "POST", "PUT", "DELETE", "PATCH"]
    _DEFAULT_PATH = "$default"

    def __init__(self, doc):
        """
        Initialize the class with a swagger dictionary. This class creates a copy of the Swagger and performs all
        modifications on this copy.

        :param dict doc: OpenApi document as a dictionary
        :raises ValueError: If the input OpenApi document does not meet the basic OpenApi requirements.
        """
        if not OpenApiEditor.is_valid(doc):
            raise ValueError(
                "Invalid OpenApi document. "
                "Invalid values or missing keys for 'openapi' or 'paths' in 'DefinitionBody'."
            )

        self._doc = copy.deepcopy(doc)
        self.paths = self._doc["paths"]
        self.security_schemes = self._doc.get("components", {}).get("securitySchemes", {})
        self.definitions = self._doc.get("definitions", {})
        self.tags = self._doc.get("tags", [])

    def get_path(self, path):
        """
        Returns the contents of a path, extracting them out of a condition if necessary
        :param path: path name
        """
        path_dict = self.paths.get(path)
        if isinstance(path_dict, dict) and self._CONDITIONAL_IF in path_dict:
            path_dict = path_dict[self._CONDITIONAL_IF][1]
        return path_dict

    def has_path(self, path, method=None):
        """
        Returns True if this OpenApi has the given path and optional method

        :param string path: Path name
        :param string method: HTTP method
        :return: True, if this path/method is present in the document
        """
        method = self._normalize_method_name(method)

        path_dict = self.get_path(path)
        path_dict_exists = path_dict is not None
        if method:
            return path_dict_exists and method in path_dict
        return path_dict_exists

    def get_integration_function_logical_id(self, path_name, method_name):
        """
        Retrieves the function logical id in a lambda integration if it exists
        If it doesn't exist, returns false
        :param path_name: name of the path
        :param method_name: name of the method
        """
        if not self.has_integration(path_name, method_name):
            return False
        method_name = self._normalize_method_name(method_name)
        # Get the path
        path = self.get_path(path_name)
        # Get the method contents
        # We only want the first one in case there are multiple (in a conditional)
        method = self.get_method_contents(path[method_name])[0]
        integration = method.get(self._X_APIGW_INTEGRATION, {})

        # Extract the integration uri out of a conditional if necessary
        uri = integration.get("uri")
        if not isinstance(uri, dict):
            return ""
        if self._CONDITIONAL_IF in uri:
            arn = uri[self._CONDITIONAL_IF][1].get("Fn::Sub")
        else:
            arn = uri.get("Fn::Sub", "")

        # Extract lambda integration (${LambdaName.Arn}) and split ".Arn" off from it
        regex = "([A-Za-z0-9]+\.Arn)"
        match = re.findall(regex, arn)[0].split(".Arn")[0]
        return match

    def method_has_integration(self, method):
        """
        Returns true if the given method contains a valid method definition.
        This uses the get_method_contents function to handle conditionals.

        :param dict method: method dictionary
        :return: true if method has one or multiple integrations
        """
        for method_definition in self.get_method_contents(method):
            if self.method_definition_has_integration(method_definition):
                return True
        return False

    def method_definition_has_integration(self, method_definition):
        """
        Checks a method definition to make sure it has an apigw integration

        :param dict method_defintion: method definition dictionary
        :return: True if an integration exists
        """
        if method_definition.get(self._X_APIGW_INTEGRATION):
            return True
        return False

    def get_method_contents(self, method):
        """
        Returns the swagger contents of the given method. This checks to see if a conditional block
        has been used inside of the method, and, if so, returns the method contents that are
        inside of the conditional.

        :param dict method: method dictionary
        :return: list of swagger component dictionaries for the method
        """
        if self._CONDITIONAL_IF in method:
            return method[self._CONDITIONAL_IF][1:]
        return [method]

    def has_integration(self, path, method):
        """
        Checks if an API Gateway integration is already present at the given path/method

        :param string path: Path name
        :param string method: HTTP method
        :return: True, if an API Gateway integration is already present
        """
        method = self._normalize_method_name(method)

        path_dict = self.get_path(path)
        return (
            self.has_path(path, method)
            and isinstance(path_dict[method], dict)
            and self.method_has_integration(path_dict[method])
        )  # Integration present and non-empty

    def add_path(self, path, method=None):
        """
        Adds the path/method combination to the Swagger, if not already present

        :param string path: Path name
        :param string method: HTTP method
        :raises ValueError: If the value of `path` in Swagger is not a dictionary
        """
        method = self._normalize_method_name(method)

        path_dict = self.paths.setdefault(path, {})

        if not isinstance(path_dict, dict):
            # Either customers has provided us an invalid Swagger, or this class has messed it somehow
            raise InvalidDocumentException(
                [
                    InvalidTemplateException(
                        "Value of '{}' path must be a dictionary according to Swagger spec.".format(path)
                    )
                ]
            )

        if self._CONDITIONAL_IF in path_dict:
            path_dict = path_dict[self._CONDITIONAL_IF][1]

        path_dict.setdefault(method, {})

    def add_lambda_integration(
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

        path_dict = self.get_path(path)
        path_dict[method][self._X_APIGW_INTEGRATION] = {
            "type": "aws_proxy",
            "httpMethod": "POST",
            "payloadFormatVersion": "2.0",
            "uri": integration_uri,
        }

        if path == self._DEFAULT_PATH and method == self._X_ANY_METHOD:
            path_dict[method]["isDefaultRoute"] = True

        # If 'responses' key is *not* present, add it with an empty dict as value
        path_dict[method].setdefault("responses", {})

        # If a condition is present, wrap all method contents up into the condition
        if condition:
            path_dict[method] = make_conditional(condition, path_dict[method])

    def make_path_conditional(self, path, condition):
        """
        Wrap entire API path definition in a CloudFormation if condition.
        :param path: path name
        :param condition: condition name
        """
        self.paths[path] = make_conditional(condition, self.paths[path])

    def iter_on_path(self):
        """
        Yields all the paths available in the Swagger. As a caller, if you add new paths to Swagger while iterating,
        they will not show up in this iterator

        :yields string: Path name
        """

        for path, value in self.paths.items():
            yield path

    def add_timeout_to_method(self, api, path, method_name, timeout):
        """
        Adds a timeout to this path/method.
        
        :param dict api: Reference to the related Api's properties as defined in the template.
        :param string path: Path name
        :param string method_name: Method name
        :param int timeout: Timeout amount, in milliseconds
        """
        normalized_method_name = self._normalize_method_name(method_name)
        for method_definition in self.get_method_contents(self.get_path(path)[normalized_method_name]):
            if self.method_definition_has_integration(method_definition):
                method_definition[self._X_APIGW_INTEGRATION]["timeoutInMillis"] = timeout

    def add_path_parameters_to_method(self, api, path, method_name, path_parameters):
        """
        Adds path parameters to this path + method
        
        :param dict api: Reference to the related Api's properties as defined in the template.
        :param string path: Path name
        :param string method_name: Method name
        :param list path_parameters: list of strings of path parameters
        """
        normalized_method_name = self._normalize_method_name(method_name)
        for method_definition in self.get_method_contents(self.get_path(path)[normalized_method_name]):
            # create path parameter list
            # add it here if it doesn't exist, merge with existing otherwise.
            method_definition.setdefault("parameters", [])
            for param in path_parameters:
                # find an existing parameter with this name if it exists
                existing_parameter = next(
                    (
                        existing_parameter
                        for existing_parameter in method_definition.get("parameters", [])
                        if existing_parameter.get("name") == param
                    ),
                    None,
                )
                if existing_parameter:
                    # overwrite parameter values for existing path parameter
                    existing_parameter["in"] = "path"
                    existing_parameter["required"] = True
                else:
                    parameter = {"name": param, "in": "path", "required": True}
                    method_definition.get("parameters").append(parameter)

    def add_payload_format_version_to_method(self, api, path, method_name, payload_format_version="2.0"):
        """
        Adds a payload format version to this path/method.

        :param dict api: Reference to the related Api's properties as defined in the template.
        :param string path: Path name
        :param string method_name: Method name
        :param string payload_format_version: payload format version sent to the integration
        """
        normalized_method_name = self._normalize_method_name(method_name)
        for method_definition in self.get_method_contents(self.get_path(path)[normalized_method_name]):
            if self.method_definition_has_integration(method_definition):
                method_definition[self._X_APIGW_INTEGRATION]["payloadFormatVersion"] = payload_format_version

    def add_authorizers_security_definitions(self, authorizers):
        """
        Add Authorizer definitions to the securityDefinitions part of Swagger.

        :param list authorizers: List of Authorizer configurations which get translated to securityDefinitions.
        """
        self.security_schemes = self.security_schemes or {}

        for authorizer_name, authorizer in authorizers.items():
            self.security_schemes[authorizer_name] = authorizer.generate_openapi()

    def set_path_default_authorizer(self, path, default_authorizer, authorizers, api_authorizers):
        """
        Adds the default_authorizer to the security block for each method on this path unless an Authorizer
        was defined at the Function/Path/Method level. This is intended to be used to set the
        authorizer security restriction for all api methods based upon the default configured in the
        Serverless API.

        :param string path: Path name
        :param string default_authorizer: Name of the authorizer to use as the default. Must be a key in the
            authorizers param.
        :param list authorizers: List of Authorizer configurations defined on the related Api.
        """
        for method_name, method in self.get_path(path).items():
            normalized_method_name = self._normalize_method_name(method_name)
            # Excluding parameters section
            if normalized_method_name == "parameters":
                continue
            if normalized_method_name != "options":
                normalized_method_name = self._normalize_method_name(method_name)
                # It is possible that the method could have two definitions in a Fn::If block.
                for method_definition in self.get_method_contents(self.get_path(path)[normalized_method_name]):
                    # If no integration given, then we don't need to process this definition (could be AWS::NoValue)
                    if not self.method_definition_has_integration(method_definition):
                        continue
                    existing_security = method_definition.get("security", [])
                    if existing_security:
                        return
                    authorizer_list = []
                    if authorizers:
                        authorizer_list.extend(authorizers.keys())
                    security_dict = dict()
                    security_dict[default_authorizer] = self._get_authorization_scopes(
                        api_authorizers, default_authorizer
                    )
                    authorizer_security = [security_dict]

                    security = authorizer_security

                    if security:
                        method_definition["security"] = security

    def add_auth_to_method(self, path, method_name, auth, api):
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
            self._set_method_authorizer(path, method_name, method_authorizer, authorizers, authorization_scopes)

    def _set_method_authorizer(self, path, method_name, authorizer_name, authorizers, authorization_scopes=[]):
        """
        Adds the authorizer_name to the security block for each method on this path.
        This is used to configure the authorizer for individual functions.

        :param string path: Path name
        :param string method_name: Method name
        :param string authorizer_name: Name of the authorizer to use. Must be a key in the
            authorizers param.
        :param list authorization_scopes: list of strings that are the auth scopes for this method
        """
        normalized_method_name = self._normalize_method_name(method_name)
        # It is possible that the method could have two definitions in a Fn::If block.
        for method_definition in self.get_method_contents(self.get_path(path)[normalized_method_name]):

            # If no integration given, then we don't need to process this definition (could be AWS::NoValue)
            if not self.method_definition_has_integration(method_definition):
                continue

            existing_security = method_definition.get("security", [])

            security_dict = dict()
            security_dict[authorizer_name] = []

            if authorizer_name != "NONE":
                method_authorization_scopes = authorizers[authorizer_name].get("AuthorizationScopes")
                if authorization_scopes:
                    method_authorization_scopes = authorization_scopes
                if authorizers[authorizer_name] and method_authorization_scopes:
                    security_dict[authorizer_name] = method_authorization_scopes

            authorizer_security = [security_dict]

            # This assumes there are no authorizers already configured in the existing security block
            security = existing_security + authorizer_security
            if security:
                method_definition["security"] = security

    def add_tags(self, tags):
        """
        Adds tags to the OpenApi definition using an ApiGateway extension for tag values.

        :param dict tags: dictionary of tagName:tagValue pairs.
        """
        for name, value in tags.items():
            # find an existing tag with this name if it exists
            existing_tag = next((existing_tag for existing_tag in self.tags if existing_tag.get("name") == name), None)
            if existing_tag:
                # overwrite tag value for an existing tag
                existing_tag[self._X_APIGW_TAG_VALUE] = value
            else:
                tag = {"name": name, self._X_APIGW_TAG_VALUE: value}
                self.tags.append(tag)

    def add_cors(
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
        cors_configuration = self._doc.get(self._X_APIGW_CORS, dict())

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

    def has_api_gateway_cors(self):
        if self._doc.get(self._X_APIGW_CORS):
            return True
        return False

    @property
    def openapi(self):
        """
        Returns a **copy** of the OpenApi specification as a dictionary.

        :return dict: Dictionary containing the OpenApi specification
        """

        # Make sure any changes to the paths are reflected back in output
        self._doc["paths"] = self.paths

        if self.tags:
            self._doc["tags"] = self.tags

        if self.security_schemes:
            self._doc.setdefault("components", {})
            self._doc["components"]["securitySchemes"] = self.security_schemes

        return copy.deepcopy(self._doc)

    @staticmethod
    def is_valid(data):
        """
        Checks if the input data is a OpenApi document

        :param dict data: Data to be validated
        :return: True, if data is valid OpenApi
        """

        if bool(data) and isinstance(data, dict) and isinstance(data.get("paths"), dict):
            if bool(data.get("openapi")):
                return OpenApiEditor.safe_compare_regex_with_string(
                    OpenApiEditor.get_openapi_version_3_regex(), data["openapi"]
                )
        return False

    @staticmethod
    def gen_skeleton():
        """
        Method to make an empty swagger file, with just some basic structure. Just enough to pass validator.

        :return dict: Dictionary of a skeleton swagger document
        """
        return {"openapi": "3.0.1", "info": {"version": "1.0", "title": ref("AWS::StackName")}, "paths": {}}

    @staticmethod
    def _get_authorization_scopes(authorizers, default_authorizer):
        """
        Returns auth scopes for an authorizer if present
        :param authorizers: authorizer definitions
        :param default_authorizer: name of the default authorizer
        """
        if authorizers is not None:
            if (
                authorizers[default_authorizer]
                and authorizers[default_authorizer].get("AuthorizationScopes") is not None
            ):
                return authorizers[default_authorizer].get("AuthorizationScopes")
        return []

    @staticmethod
    def _normalize_method_name(method):
        """
        Returns a lower case, normalized version of HTTP Method. It also know how to handle API Gateway specific methods
        like "ANY"

        NOTE: Always normalize before using the `method` value passed in as input

        :param string method: Name of the HTTP Method
        :return string: Normalized method name
        """
        if not method or not isinstance(method, string_types):
            return method

        method = method.lower()
        if method == "any":
            return OpenApiEditor._X_ANY_METHOD
        else:
            return method

    @staticmethod
    def get_openapi_version_3_regex():
        openapi_version_3_regex = r"\A3(\.\d)(\.\d)?$"
        return openapi_version_3_regex

    @staticmethod
    def safe_compare_regex_with_string(regex, data):
        return re.match(regex, str(data)) is not None

    @staticmethod
    def get_path_without_trailing_slash(path):
        return re.sub(r"{([a-zA-Z0-9._-]+|proxy\+)}", "*", path)
