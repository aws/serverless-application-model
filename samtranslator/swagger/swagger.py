import copy
import json
import re
from six import string_types

from samtranslator.model.intrinsics import ref, is_intrinsic_no_value
from samtranslator.model.intrinsics import make_conditional, fnSub, is_intrinsic_if
from samtranslator.model.exceptions import InvalidDocumentException, InvalidTemplateException


class SwaggerEditor(object):
    """
    Wrapper class capable of parsing and generating Swagger JSON.  This implements Swagger spec just enough that SAM
    cares about. It is built to handle "partial Swagger" ie. Swagger that is incomplete and won't
    pass the Swagger spec. But this is necessary for SAM because it iteratively builds the Swagger starting from an
    empty skeleton.
    """

    _OPTIONS_METHOD = "options"
    _X_APIGW_INTEGRATION = "x-amazon-apigateway-integration"
    _X_APIGW_BINARY_MEDIA_TYPES = "x-amazon-apigateway-binary-media-types"
    _CONDITIONAL_IF = "Fn::If"
    _X_APIGW_GATEWAY_RESPONSES = "x-amazon-apigateway-gateway-responses"
    _X_APIGW_POLICY = "x-amazon-apigateway-policy"
    _X_ANY_METHOD = "x-amazon-apigateway-any-method"
    _CACHE_KEY_PARAMETERS = "cacheKeyParameters"
    # https://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html
    _ALL_HTTP_METHODS = ["OPTIONS", "GET", "HEAD", "POST", "PUT", "DELETE", "PATCH"]
    _POLICY_TYPE_IAM = "Iam"
    _POLICY_TYPE_IP = "Ip"
    _POLICY_TYPE_VPC = "Vpc"

    def __init__(self, doc):
        """
        Initialize the class with a swagger dictionary. This class creates a copy of the Swagger and performs all
        modifications on this copy.

        :param dict doc: Swagger document as a dictionary
        :raises ValueError: If the input Swagger document does not meet the basic Swagger requirements.
        """

        if not SwaggerEditor.is_valid(doc):
            raise ValueError("Invalid Swagger document")

        self._doc = copy.deepcopy(doc)
        self.paths = self._doc["paths"]
        self.security_definitions = self._doc.get("securityDefinitions", {})
        self.gateway_responses = self._doc.get(self._X_APIGW_GATEWAY_RESPONSES, {})
        self.resource_policy = self._doc.get(self._X_APIGW_POLICY, {})
        self.definitions = self._doc.get("definitions", {})

    def get_path(self, path):
        path_dict = self.paths.get(path)
        if isinstance(path_dict, dict) and self._CONDITIONAL_IF in path_dict:
            path_dict = path_dict[self._CONDITIONAL_IF][1]
        return path_dict

    def has_path(self, path, method=None):
        """
        Returns True if this Swagger has the given path and optional method

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

        :param dict method_definition: method definition dictionary
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
            raise ValueError("Lambda integration already exists on Path={}, Method={}".format(path, method))

        self.add_path(path, method)

        # Wrap the integration_uri in a Condition if one exists on that function
        # This is necessary so CFN doesn't try to resolve the integration reference.
        if condition:
            integration_uri = make_conditional(condition, integration_uri)

        path_dict = self.get_path(path)
        path_dict[method][self._X_APIGW_INTEGRATION] = {
            "type": "aws_proxy",
            "httpMethod": "POST",
            "uri": integration_uri,
        }

        method_auth_config = method_auth_config or {}
        api_auth_config = api_auth_config or {}
        if (
            method_auth_config.get("Authorizer") == "AWS_IAM"
            or api_auth_config.get("DefaultAuthorizer") == "AWS_IAM"
            and not method_auth_config
        ):
            method_invoke_role = method_auth_config.get("InvokeRole")
            if not method_invoke_role and "InvokeRole" in method_auth_config:
                method_invoke_role = "NONE"
            api_invoke_role = api_auth_config.get("InvokeRole")
            if not api_invoke_role and "InvokeRole" in api_auth_config:
                api_invoke_role = "NONE"
            credentials = self._generate_integration_credentials(
                method_invoke_role=method_invoke_role, api_invoke_role=api_invoke_role
            )
            if credentials and credentials != "NONE":
                self.paths[path][method][self._X_APIGW_INTEGRATION]["credentials"] = credentials

        # If 'responses' key is *not* present, add it with an empty dict as value
        path_dict[method].setdefault("responses", {})

        # If a condition is present, wrap all method contents up into the condition
        if condition:
            path_dict[method] = make_conditional(condition, path_dict[method])

    def make_path_conditional(self, path, condition):
        """
        Wrap entire API path definition in a CloudFormation if condition.
        """
        self.paths[path] = make_conditional(condition, self.paths[path])

    def _generate_integration_credentials(self, method_invoke_role=None, api_invoke_role=None):
        return self._get_invoke_role(method_invoke_role or api_invoke_role)

    def _get_invoke_role(self, invoke_role):
        CALLER_CREDENTIALS_ARN = "arn:aws:iam::*:user/*"
        return invoke_role if invoke_role and invoke_role != "CALLER_CREDENTIALS" else CALLER_CREDENTIALS_ARN

    def iter_on_path(self):
        """
        Yields all the paths available in the Swagger. As a caller, if you add new paths to Swagger while iterating,
        they will not show up in this iterator

        :yields string: Path name
        """

        for path, value in self.paths.items():
            yield path

    def add_cors(
        self, path, allowed_origins, allowed_headers=None, allowed_methods=None, max_age=None, allow_credentials=None
    ):
        """
        Add CORS configuration to this path. Specifically, we will add a OPTIONS response config to the Swagger that
        will return headers required for CORS. Since SAM uses aws_proxy integration, we cannot inject the headers
        into the actual response returned from Lambda function. This is something customers have to implement
        themselves.

        If OPTIONS method is already present for the Path, we will skip adding CORS configuration

        Following this guide:
        https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-cors.html#enable-cors-for-resource-using-swagger-importer-tool

        :param string path: Path to add the CORS configuration to.
        :param string/dict allowed_origins: Comma separate list of allowed origins.
            Value can also be an intrinsic function dict.
        :param string/dict allowed_headers: Comma separated list of allowed headers.
            Value can also be an intrinsic function dict.
        :param string/dict allowed_methods: Comma separated list of allowed methods.
            Value can also be an intrinsic function dict.
        :param integer/dict max_age: Maximum duration to cache the CORS Preflight request. Value is set on
            Access-Control-Max-Age header. Value can also be an intrinsic function dict.
        :param bool/None allow_credentials: Flags whether request is allowed to contain credentials.
        :raises ValueError: When values for one of the allowed_* variables is empty
        """

        # Skip if Options is already present
        if self.has_path(path, self._OPTIONS_METHOD):
            return

        if not allowed_origins:
            raise ValueError("Invalid input. Value for AllowedOrigins is required")

        if not allowed_methods:
            # AllowMethods is not given. Let's try to generate the list from the given Swagger.
            allowed_methods = self._make_cors_allowed_methods_for_path(path)

            # APIGW expects the value to be a "string expression". Hence wrap in another quote. Ex: "'GET,POST,DELETE'"
            allowed_methods = "'{}'".format(allowed_methods)

        if allow_credentials is not True:
            allow_credentials = False

        # Add the Options method and the CORS response
        self.add_path(path, self._OPTIONS_METHOD)
        self.get_path(path)[self._OPTIONS_METHOD] = self._options_method_response_for_cors(
            allowed_origins, allowed_headers, allowed_methods, max_age, allow_credentials
        )

    def add_binary_media_types(self, binary_media_types):
        bmt = json.loads(json.dumps(binary_media_types).replace("~1", "/"))
        self._doc[self._X_APIGW_BINARY_MEDIA_TYPES] = bmt

    def _options_method_response_for_cors(
        self, allowed_origins, allowed_headers=None, allowed_methods=None, max_age=None, allow_credentials=None
    ):
        """
        Returns a Swagger snippet containing configuration for OPTIONS HTTP Method to configure CORS.

        This snippet is taken from public documentation:
        https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-cors.html#enable-cors-for-resource-using-swagger-importer-tool

        :param string/dict allowed_origins: Comma separate list of allowed origins.
            Value can also be an intrinsic function dict.
        :param string/dict allowed_headers: Comma separated list of allowed headers.
            Value can also be an intrinsic function dict.
        :param string/dict allowed_methods: Comma separated list of allowed methods.
            Value can also be an intrinsic function dict.
        :param integer/dict max_age: Maximum duration to cache the CORS Preflight request. Value is set on
            Access-Control-Max-Age header. Value can also be an intrinsic function dict.
        :param bool allow_credentials: Flags whether request is allowed to contain credentials.

        :return dict: Dictionary containing Options method configuration for CORS
        """

        ALLOW_ORIGIN = "Access-Control-Allow-Origin"
        ALLOW_HEADERS = "Access-Control-Allow-Headers"
        ALLOW_METHODS = "Access-Control-Allow-Methods"
        MAX_AGE = "Access-Control-Max-Age"
        ALLOW_CREDENTIALS = "Access-Control-Allow-Credentials"
        HEADER_RESPONSE = lambda x: "method.response.header." + x

        response_parameters = {
            # AllowedOrigin is always required
            HEADER_RESPONSE(ALLOW_ORIGIN): allowed_origins
        }

        response_headers = {
            # Allow Origin is always required
            ALLOW_ORIGIN: {"type": "string"}
        }

        # Optional values. Skip the header if value is empty
        #
        # The values must not be empty string or null. Also, value of '*' is a very recent addition (2017) and
        # not supported in all the browsers. So it is important to skip the header if value is not given
        #    https://fetch.spec.whatwg.org/#http-new-header-syntax
        #
        if allowed_headers:
            response_parameters[HEADER_RESPONSE(ALLOW_HEADERS)] = allowed_headers
            response_headers[ALLOW_HEADERS] = {"type": "string"}
        if allowed_methods:
            response_parameters[HEADER_RESPONSE(ALLOW_METHODS)] = allowed_methods
            response_headers[ALLOW_METHODS] = {"type": "string"}
        if max_age is not None:
            # MaxAge can be set to 0, which is a valid value. So explicitly check against None
            response_parameters[HEADER_RESPONSE(MAX_AGE)] = max_age
            response_headers[MAX_AGE] = {"type": "integer"}
        if allow_credentials is True:
            # Allow-Credentials only has a valid value of true, it should be omitted otherwise.
            # https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Access-Control-Allow-Credentials
            response_parameters[HEADER_RESPONSE(ALLOW_CREDENTIALS)] = "'true'"
            response_headers[ALLOW_CREDENTIALS] = {"type": "string"}

        return {
            "summary": "CORS support",
            "consumes": ["application/json"],
            "produces": ["application/json"],
            self._X_APIGW_INTEGRATION: {
                "type": "mock",
                "requestTemplates": {"application/json": '{\n  "statusCode" : 200\n}\n'},
                "responses": {
                    "default": {
                        "statusCode": "200",
                        "responseParameters": response_parameters,
                        "responseTemplates": {"application/json": "{}\n"},
                    }
                },
            },
            "responses": {"200": {"description": "Default response for CORS method", "headers": response_headers}},
        }

    def _make_cors_allowed_methods_for_path(self, path):
        """
        Creates the value for Access-Control-Allow-Methods header for given path. All HTTP methods defined for this
        path will be included in the result. If the path contains "ANY" method, then *all available* HTTP methods will
        be returned as result.

        :param string path: Path to generate AllowMethods value for
        :return string: String containing the value of AllowMethods, if the path contains any methods.
                        Empty string, otherwise
        """

        if not self.has_path(path):
            return ""

        # At this point, value of Swagger path should be a dictionary with method names being the keys
        methods = list(self.get_path(path).keys())

        if self._X_ANY_METHOD in methods:
            # API Gateway's ANY method is not a real HTTP method but a wildcard representing all HTTP methods
            allow_methods = self._ALL_HTTP_METHODS
        else:
            allow_methods = methods
            allow_methods.append("options")  # Always add Options to the CORS methods response

        # Clean up the result:
        #
        # - HTTP Methods **must** be upper case and they are case sensitive.
        #   (https://tools.ietf.org/html/rfc7231#section-4.1)
        # - Convert to set to remove any duplicates
        # - Sort to keep this list stable because it could be constructed from dictionary keys which are *not* ordered.
        #   Therefore we might get back a different list each time the code runs. To prevent any unnecessary
        #   regression, we sort the list so the returned value is stable.
        allow_methods = list({m.upper() for m in allow_methods})
        allow_methods.sort()

        # Allow-Methods is comma separated string
        return ",".join(allow_methods)

    def add_authorizers_security_definitions(self, authorizers):
        """
        Add Authorizer definitions to the securityDefinitions part of Swagger.

        :param list authorizers: List of Authorizer configurations which get translated to securityDefinitions.
        """
        self.security_definitions = self.security_definitions or {}

        for authorizer_name, authorizer in authorizers.items():
            self.security_definitions[authorizer_name] = authorizer.generate_swagger()

    def add_awsiam_security_definition(self):
        """
        Adds AWS_IAM definition to the securityDefinitions part of Swagger.
        Note: this method is idempotent
        """

        aws_iam_security_definition = {
            "AWS_IAM": {
                "x-amazon-apigateway-authtype": "awsSigv4",
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
            }
        }

        self.security_definitions = self.security_definitions or {}

        # Only add the security definition if it doesn't exist.  This helps ensure
        # that we minimize changes to the swagger in the case of user defined swagger
        if "AWS_IAM" not in self.security_definitions:
            self.security_definitions.update(aws_iam_security_definition)

    def add_apikey_security_definition(self):
        """
        Adds api_key definition to the securityDefinitions part of Swagger.
        Note: this method is idempotent
        """

        api_key_security_definition = {"api_key": {"type": "apiKey", "name": "x-api-key", "in": "header"}}

        self.security_definitions = self.security_definitions or {}

        # Only add the security definition if it doesn't exist.  This helps ensure
        # that we minimize changes to the swagger in the case of user defined swagger
        if "api_key" not in self.security_definitions:
            self.security_definitions.update(api_key_security_definition)

    def set_path_default_authorizer(
        self, path, default_authorizer, authorizers, add_default_auth_to_preflight=True, api_authorizers=None
    ):
        """
        Adds the default_authorizer to the security block for each method on this path unless an Authorizer
        was defined at the Function/Path/Method level. This is intended to be used to set the
        authorizer security restriction for all api methods based upon the default configured in the
        Serverless API.

        :param string path: Path name
        :param string default_authorizer: Name of the authorizer to use as the default. Must be a key in the
            authorizers param.
        :param list authorizers: List of Authorizer configurations defined on the related Api.
        :param bool add_default_auth_to_preflight: Bool of whether to add the default
            authorizer to OPTIONS preflight requests.
        """

        for method_name, method in self.get_path(path).items():
            normalized_method_name = self._normalize_method_name(method_name)

            # Excluding parameters section
            if normalized_method_name == "parameters":
                continue
            if add_default_auth_to_preflight or normalized_method_name != "options":
                normalized_method_name = self._normalize_method_name(method_name)
                # It is possible that the method could have two definitions in a Fn::If block.
                for method_definition in self.get_method_contents(self.get_path(path)[normalized_method_name]):

                    # If no integration given, then we don't need to process this definition (could be AWS::NoValue)
                    if not self.method_definition_has_integration(method_definition):
                        continue
                    existing_security = method_definition.get("security", [])
                    authorizer_list = ["AWS_IAM"]
                    if authorizers:
                        authorizer_list.extend(authorizers.keys())
                    authorizer_names = set(authorizer_list)
                    existing_non_authorizer_security = []
                    existing_authorizer_security = []

                    # Split existing security into Authorizers and everything else
                    # (e.g. sigv4 (AWS_IAM), api_key (API Key/Usage Plans), NONE (marker for ignoring default))
                    # We want to ensure only a single Authorizer security entry exists while keeping everything else
                    for security in existing_security:
                        if authorizer_names.isdisjoint(security.keys()):
                            existing_non_authorizer_security.append(security)
                        else:
                            existing_authorizer_security.append(security)

                    none_idx = -1
                    authorizer_security = []

                    # Check for an existing Authorizer before applying the default. It would be simpler
                    # if instead we applied the DefaultAuthorizer first and then simply
                    # overwrote it if necessary, however, the order in which things get
                    # applied (Function Api Events first; then Api Resource) complicates it.
                    # Check if Function/Path/Method specified 'NONE' for Authorizer
                    for idx, security in enumerate(existing_non_authorizer_security):
                        is_none = any(key == "NONE" for key in security.keys())

                        if is_none:
                            none_idx = idx
                            break

                    # NONE was found; remove it and don't add the DefaultAuthorizer
                    if none_idx > -1:
                        del existing_non_authorizer_security[none_idx]

                    # Existing Authorizer found (defined at Function/Path/Method); use that instead of default
                    elif existing_authorizer_security:
                        authorizer_security = existing_authorizer_security

                    # No existing Authorizer found; use default
                    else:
                        security_dict = {}
                        security_dict[default_authorizer] = self._get_authorization_scopes(
                            api_authorizers, default_authorizer
                        )
                        authorizer_security = [security_dict]

                    security = existing_non_authorizer_security + authorizer_security

                    if security:
                        method_definition["security"] = security

                        # The first element of the method_definition['security'] should be AWS_IAM
                        # because authorizer_list = ['AWS_IAM'] is hardcoded above
                        if "AWS_IAM" in method_definition["security"][0]:
                            self.add_awsiam_security_definition()

    def set_path_default_apikey_required(self, path):
        """
        Add the ApiKey security as required for each method on this path unless ApiKeyRequired
        was defined at the Function/Path/Method level. This is intended to be used to set the
        apikey security restriction for all api methods based upon the default configured in the
        Serverless API.

        :param string path: Path name
        """

        for method_name, _ in self.get_path(path).items():
            # Excluding parameters section
            if method_name == "parameters":
                continue

            normalized_method_name = self._normalize_method_name(method_name)
            # It is possible that the method could have two definitions in a Fn::If block.
            for method_definition in self.get_method_contents(self.get_path(path)[normalized_method_name]):

                # If no integration given, then we don't need to process this definition (could be AWS::NoValue)
                if not self.method_definition_has_integration(method_definition):
                    continue

                existing_security = method_definition.get("security", [])
                apikey_security_names = set(["api_key", "api_key_false"])
                existing_non_apikey_security = []
                existing_apikey_security = []
                apikey_security = []

                # Split existing security into ApiKey and everything else
                # (e.g. sigv4 (AWS_IAM), authorizers, NONE (marker for ignoring default authorizer))
                # We want to ensure only a single ApiKey security entry exists while keeping everything else
                for security in existing_security:
                    if apikey_security_names.isdisjoint(security.keys()):
                        existing_non_apikey_security.append(security)
                    else:
                        existing_apikey_security.append(security)

                # Check for an existing method level ApiKey setting before applying the default. It would be simpler
                # if instead we applied the default first and then simply
                # overwrote it if necessary, however, the order in which things get
                # applied (Function Api Events first; then Api Resource) complicates it.
                # Check if Function/Path/Method specified 'False' for ApiKeyRequired
                apikeyfalse_idx = -1
                for idx, security in enumerate(existing_apikey_security):
                    is_none = any(key == "api_key_false" for key in security.keys())

                    if is_none:
                        apikeyfalse_idx = idx
                        break

                # api_key_false was found; remove it and don't add default api_key security setting
                if apikeyfalse_idx > -1:
                    del existing_apikey_security[apikeyfalse_idx]

                # No existing ApiKey setting found or it's already set to the default
                else:
                    security_dict = {}
                    security_dict["api_key"] = []
                    apikey_security = [security_dict]

                security = existing_non_apikey_security + apikey_security

                if security != existing_security:
                    method_definition["security"] = security

    def add_auth_to_method(self, path, method_name, auth, api):
        """
        Adds auth settings for this path/method. Auth settings currently consist of Authorizers and ApiKeyRequired
        but this method will eventually include setting other auth settings such as Resource Policy, etc.
        This is used to configure the security for individual functions.

        :param string path: Path name
        :param string method_name: Method name
        :param dict auth: Auth configuration such as Authorizers, ApiKeyRequired, ResourcePolicy
        :param dict api: Reference to the related Api's properties as defined in the template.
        """
        method_authorizer = auth and auth.get("Authorizer")
        method_scopes = auth and auth.get("AuthorizationScopes")
        api_auth = api and api.get("Auth")
        authorizers = api_auth and api_auth.get("Authorizers")
        if method_authorizer:
            self._set_method_authorizer(path, method_name, method_authorizer, authorizers, method_scopes)

        method_apikey_required = auth and auth.get("ApiKeyRequired")
        if method_apikey_required is not None:
            self._set_method_apikey_handling(path, method_name, method_apikey_required)

    def _set_method_authorizer(self, path, method_name, authorizer_name, authorizers={}, method_scopes=None):
        """
        Adds the authorizer_name to the security block for each method on this path.
        This is used to configure the authorizer for individual functions.

        :param string path: Path name
        :param string method_name: Method name
        :param string authorizer_name: Name of the authorizer to use. Must be a key in the
            authorizers param.
        """
        normalized_method_name = self._normalize_method_name(method_name)
        # It is possible that the method could have two definitions in a Fn::If block.
        for method_definition in self.get_method_contents(self.get_path(path)[normalized_method_name]):

            # If no integration given, then we don't need to process this definition (could be AWS::NoValue)
            if not self.method_definition_has_integration(method_definition):
                continue

            existing_security = method_definition.get("security", [])

            security_dict = {}
            security_dict[authorizer_name] = []
            authorizer_security = [security_dict]

            # This assumes there are no autorizers already configured in the existing security block
            security = existing_security + authorizer_security

            if authorizer_name != "NONE" and authorizers:
                method_auth_scopes = authorizers.get(authorizer_name, {}).get("AuthorizationScopes")
                if method_scopes is not None:
                    method_auth_scopes = method_scopes
                if authorizers.get(authorizer_name) is not None and method_auth_scopes is not None:
                    security_dict[authorizer_name] = method_auth_scopes

            if security:
                method_definition["security"] = security

                # The first element of the method_definition['security'] should be AWS_IAM
                # because authorizer_list = ['AWS_IAM'] is hardcoded above
                if "AWS_IAM" in method_definition["security"][0]:
                    self.add_awsiam_security_definition()

    def _set_method_apikey_handling(self, path, method_name, apikey_required):
        """
        Adds the apikey setting to the security block for each method on this path.
        This is used to configure the authorizer for individual functions.

        :param string path: Path name
        :param string method_name: Method name
        :param bool apikey_required: Whether the apikey security is required
        """
        normalized_method_name = self._normalize_method_name(method_name)
        # It is possible that the method could have two definitions in a Fn::If block.
        for method_definition in self.get_method_contents(self.get_path(path)[normalized_method_name]):

            # If no integration given, then we don't need to process this definition (could be AWS::NoValue)
            if not self.method_definition_has_integration(method_definition):
                continue

            existing_security = method_definition.get("security", [])

            if apikey_required:
                # We want to enable apikey required security
                security_dict = {}
                security_dict["api_key"] = []
                apikey_security = [security_dict]
                self.add_apikey_security_definition()
            else:
                # The method explicitly does NOT require apikey and there is an API default
                # so let's add a marker 'api_key_false' so that we don't incorrectly override
                # with the api default
                security_dict = {}
                security_dict["api_key_false"] = []
                apikey_security = [security_dict]

            # This assumes there are no autorizers already configured in the existing security block
            security = existing_security + apikey_security

            if security != existing_security:
                method_definition["security"] = security

    def add_request_model_to_method(self, path, method_name, request_model):
        """
        Adds request model body parameter for this path/method.

        :param string path: Path name
        :param string method_name: Method name
        :param dict request_model: Model name
        """
        model_name = request_model and request_model.get("Model").lower()
        model_required = request_model and request_model.get("Required")

        normalized_method_name = self._normalize_method_name(method_name)
        # It is possible that the method could have two definitions in a Fn::If block.
        for method_definition in self.get_method_contents(self.get_path(path)[normalized_method_name]):

            # If no integration given, then we don't need to process this definition (could be AWS::NoValue)
            if not self.method_definition_has_integration(method_definition):
                continue

            if self._doc.get("swagger") is not None:

                existing_parameters = method_definition.get("parameters", [])

                parameter = {
                    "in": "body",
                    "name": model_name,
                    "schema": {"$ref": "#/definitions/{}".format(model_name)},
                }

                if model_required is not None:
                    parameter["required"] = model_required

                existing_parameters.append(parameter)

                method_definition["parameters"] = existing_parameters

            elif self._doc.get("openapi") and SwaggerEditor.safe_compare_regex_with_string(
                SwaggerEditor.get_openapi_version_3_regex(), self._doc["openapi"]
            ):
                method_definition["requestBody"] = {
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/{}".format(model_name)}}}
                }

                if model_required is not None:
                    method_definition["requestBody"]["required"] = model_required

    def add_gateway_responses(self, gateway_responses):
        """
        Add Gateway Response definitions to Swagger.

        :param dict gateway_responses: Dictionary of GatewayResponse configuration which gets translated.
        """
        self.gateway_responses = self.gateway_responses or {}

        for response_type, response in gateway_responses.items():
            self.gateway_responses[response_type] = response.generate_swagger()

    def add_models(self, models):
        """
        Add Model definitions to Swagger.

        :param dict models: Dictionary of Model schemas which gets translated
        :return:
        """

        self.definitions = self.definitions or {}

        for model_name, schema in models.items():

            model_type = schema.get("type")
            model_properties = schema.get("properties")

            if not model_type:
                raise ValueError("Invalid input. Value for type is required")

            if not model_properties:
                raise ValueError("Invalid input. Value for properties is required")

            self.definitions[model_name.lower()] = schema

    def add_resource_policy(self, resource_policy, path, api_id, stage):
        """
        Add resource policy definition to Swagger.

        :param dict resource_policy: Dictionary of resource_policy statements which gets translated
        :return:
        """
        if resource_policy is None:
            return

        aws_account_whitelist = resource_policy.get("AwsAccountWhitelist")
        aws_account_blacklist = resource_policy.get("AwsAccountBlacklist")
        ip_range_whitelist = resource_policy.get("IpRangeWhitelist")
        ip_range_blacklist = resource_policy.get("IpRangeBlacklist")
        source_vpc_whitelist = resource_policy.get("SourceVpcWhitelist")
        source_vpc_blacklist = resource_policy.get("SourceVpcBlacklist")

        if aws_account_whitelist is not None:
            resource_list = self._get_method_path_uri_list(path, api_id, stage)
            self._add_iam_resource_policy_for_method(aws_account_whitelist, "Allow", resource_list)

        if aws_account_blacklist is not None:
            resource_list = self._get_method_path_uri_list(path, api_id, stage)
            self._add_iam_resource_policy_for_method(aws_account_blacklist, "Deny", resource_list)

        if ip_range_whitelist is not None:
            resource_list = self._get_method_path_uri_list(path, api_id, stage)
            self._add_ip_resource_policy_for_method(ip_range_whitelist, "NotIpAddress", resource_list)

        if ip_range_blacklist is not None:
            resource_list = self._get_method_path_uri_list(path, api_id, stage)
            self._add_ip_resource_policy_for_method(ip_range_blacklist, "IpAddress", resource_list)

        if source_vpc_whitelist is not None:
            resource_list = self._get_method_path_uri_list(path, api_id, stage)
            self._add_vpc_resource_policy_for_method(source_vpc_whitelist, "StringNotEquals", resource_list)

        if source_vpc_blacklist is not None:
            resource_list = self._get_method_path_uri_list(path, api_id, stage)
            self._add_vpc_resource_policy_for_method(source_vpc_blacklist, "StringEquals", resource_list)

        self._doc[self._X_APIGW_POLICY] = self.resource_policy

    def add_custom_statements(self, custom_statements):
        self._add_custom_statement(custom_statements)

        self._doc[self._X_APIGW_POLICY] = self.resource_policy

    def _add_iam_resource_policy_for_method(self, policy_list, effect, resource_list):
        """
        This method generates a policy statement to grant/deny specific IAM users access to the API method and
        appends it to the swagger under `x-amazon-apigateway-policy`
        :raises ValueError: If the effect passed in does not match the allowed values.
        """
        if not policy_list:
            return

        if effect not in ["Allow", "Deny"]:
            raise ValueError("Effect must be one of {}".format(["Allow", "Deny"]))

        if not isinstance(policy_list, (dict, list)):
            raise InvalidDocumentException(
                [InvalidTemplateException("Type of '{}' must be a list or dictionary".format(policy_list))]
            )

        if not isinstance(policy_list, list):
            policy_list = [policy_list]

        self.resource_policy["Version"] = "2012-10-17"
        policy_statement = {}
        policy_statement["Effect"] = effect
        policy_statement["Action"] = "execute-api:Invoke"
        policy_statement["Resource"] = resource_list
        policy_statement["Principal"] = {"AWS": policy_list}

        if self.resource_policy.get("Statement") is None:
            self.resource_policy["Statement"] = policy_statement
        else:
            statement = self.resource_policy["Statement"]
            if not isinstance(statement, list):
                statement = [statement]
            statement.extend([policy_statement])
            self.resource_policy["Statement"] = statement

    def _get_method_path_uri_list(self, path, api_id, stage):
        """
        It turns out that APIGW doesn't like trailing slashes in paths (#665)
        and removes as a part of their behavior, but this isn't documented.
        The regex removes the trailing slash to ensure the permission works as intended
        """
        methods = list(self.get_path(path).keys())

        uri_list = []
        path = SwaggerEditor.get_path_without_trailing_slash(path)

        for m in methods:
            method = "*" if (m.lower() == self._X_ANY_METHOD or m.lower() == "any") else m.upper()
            resource = "execute-api:/${__Stage__}/" + method + path
            resource = fnSub(resource, {"__Stage__": stage})
            uri_list.extend([resource])
        return uri_list

    def _add_ip_resource_policy_for_method(self, ip_list, conditional, resource_list):
        """
        This method generates a policy statement to grant/deny specific IP address ranges access to the API method and
        appends it to the swagger under `x-amazon-apigateway-policy`
        :raises ValueError: If the conditional passed in does not match the allowed values.
        """
        if not ip_list:
            return

        if not isinstance(ip_list, list):
            ip_list = [ip_list]

        if conditional not in ["IpAddress", "NotIpAddress"]:
            raise ValueError("Conditional must be one of {}".format(["IpAddress", "NotIpAddress"]))

        self.resource_policy["Version"] = "2012-10-17"
        allow_statement = {}
        allow_statement["Effect"] = "Allow"
        allow_statement["Action"] = "execute-api:Invoke"
        allow_statement["Resource"] = resource_list
        allow_statement["Principal"] = "*"

        deny_statement = {}
        deny_statement["Effect"] = "Deny"
        deny_statement["Action"] = "execute-api:Invoke"
        deny_statement["Resource"] = resource_list
        deny_statement["Principal"] = "*"
        deny_statement["Condition"] = {conditional: {"aws:SourceIp": ip_list}}

        if self.resource_policy.get("Statement") is None:
            self.resource_policy["Statement"] = [allow_statement, deny_statement]
        else:
            statement = self.resource_policy["Statement"]
            if not isinstance(statement, list):
                statement = [statement]
            if allow_statement not in statement:
                statement.extend([allow_statement])
            if deny_statement not in statement:
                statement.extend([deny_statement])
            self.resource_policy["Statement"] = statement

    def _add_vpc_resource_policy_for_method(self, endpoint_list, conditional, resource_list):
        """
        This method generates a policy statement to grant/deny specific VPC/VPCE access to the API method and
        appends it to the swagger under `x-amazon-apigateway-policy`
        :raises ValueError: If the conditional passed in does not match the allowed values.
        """
        if not endpoint_list:
            return

        if conditional not in ["StringNotEquals", "StringEquals"]:
            raise ValueError("Conditional must be one of {}".format(["StringNotEquals", "StringEquals"]))

        vpce_regex = r"^vpce-"
        vpc_regex = r"^vpc-"
        vpc_list = []
        vpce_list = []
        for endpoint in endpoint_list:
            if re.match(vpce_regex, endpoint):
                vpce_list.append(endpoint)
            if re.match(vpc_regex, endpoint):
                vpc_list.append(endpoint)

        condition = {}
        if vpc_list:
            condition["aws:SourceVpc"] = vpc_list
        if vpce_list:
            condition["aws:SourceVpce"] = vpce_list
        self.resource_policy["Version"] = "2012-10-17"
        allow_statement = {}
        allow_statement["Effect"] = "Allow"
        allow_statement["Action"] = "execute-api:Invoke"
        allow_statement["Resource"] = resource_list
        allow_statement["Principal"] = "*"

        deny_statement = {}
        deny_statement["Effect"] = "Deny"
        deny_statement["Action"] = "execute-api:Invoke"
        deny_statement["Resource"] = resource_list
        deny_statement["Principal"] = "*"
        deny_statement["Condition"] = {conditional: condition}

        if self.resource_policy.get("Statement") is None:
            self.resource_policy["Statement"] = [allow_statement, deny_statement]
        else:
            statement = self.resource_policy["Statement"]
            if not isinstance(statement, list):
                statement = [statement]
            if allow_statement not in statement:
                statement.extend([allow_statement])
            if deny_statement not in statement:
                statement.extend([deny_statement])
            self.resource_policy["Statement"] = statement

    def _add_custom_statement(self, custom_statements):
        if custom_statements is None:
            return

        self.resource_policy["Version"] = "2012-10-17"
        if self.resource_policy.get("Statement") is None:
            self.resource_policy["Statement"] = custom_statements
        else:
            if not isinstance(custom_statements, list):
                custom_statements = [custom_statements]

            statement = self.resource_policy["Statement"]
            if not isinstance(statement, list):
                statement = [statement]

            for s in custom_statements:
                if s not in statement:
                    statement.append(s)
            self.resource_policy["Statement"] = statement

    def add_request_parameters_to_method(self, path, method_name, request_parameters):
        """
        Add Parameters to Swagger.

        :param string path: Path name
        :param string method_name: Method name
        :param list request_parameters: Dictionary of Parameters
        :return:
        """

        normalized_method_name = self._normalize_method_name(method_name)
        # It is possible that the method could have two definitions in a Fn::If block.
        for method_definition in self.get_method_contents(self.get_path(path)[normalized_method_name]):

            # If no integration given, then we don't need to process this definition (could be AWS::NoValue)
            if not self.method_definition_has_integration(method_definition):
                continue

            existing_parameters = method_definition.get("parameters", [])

            for request_parameter in request_parameters:

                parameter_name = request_parameter["Name"]
                location_name = parameter_name.replace("method.request.", "")
                location, name = location_name.split(".")

                if location == "querystring":
                    location = "query"

                parameter = {"in": location, "name": name, "required": request_parameter["Required"], "type": "string"}

                existing_parameters.append(parameter)

                if request_parameter["Caching"]:

                    integration = method_definition[self._X_APIGW_INTEGRATION]
                    cache_parameters = integration.get(self._CACHE_KEY_PARAMETERS, [])
                    cache_parameters.append(parameter_name)
                    integration[self._CACHE_KEY_PARAMETERS] = cache_parameters

            method_definition["parameters"] = existing_parameters

    @property
    def swagger(self):
        """
        Returns a **copy** of the Swagger document as a dictionary.

        :return dict: Dictionary containing the Swagger document
        """

        # Make sure any changes to the paths are reflected back in output
        self._doc["paths"] = self.paths

        if self.security_definitions:
            self._doc["securityDefinitions"] = self.security_definitions
        if self.gateway_responses:
            self._doc[self._X_APIGW_GATEWAY_RESPONSES] = self.gateway_responses
        if self.definitions:
            self._doc["definitions"] = self.definitions

        return copy.deepcopy(self._doc)

    @staticmethod
    def is_valid(data):
        """
        Checks if the input data is a Swagger document

        :param dict data: Data to be validated
        :return: True, if data is a Swagger
        """

        if bool(data) and isinstance(data, dict) and isinstance(data.get("paths"), dict):
            if bool(data.get("swagger")):
                return True
            elif bool(data.get("openapi")):
                return SwaggerEditor.safe_compare_regex_with_string(
                    SwaggerEditor.get_openapi_version_3_regex(), data["openapi"]
                )
        return False

    @staticmethod
    def gen_skeleton():
        """
        Method to make an empty swagger file, with just some basic structure. Just enough to pass validator.

        :return dict: Dictionary of a skeleton swagger document
        """
        return {"swagger": "2.0", "info": {"version": "1.0", "title": ref("AWS::StackName")}, "paths": {}}

    @staticmethod
    def _get_authorization_scopes(authorizers, default_authorizer):
        """
        Returns auth scopes for an authorizer if present
        :param authorizers: authorizer definitions
        :param default_authorizer: name of the default authorizer
        """
        if authorizers is not None:
            if (
                authorizers.get(default_authorizer)
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
            return SwaggerEditor._X_ANY_METHOD
        else:
            return method

    @staticmethod
    def get_openapi_versions_supported_regex():
        openapi_version_supported_regex = r"\A[2-3](\.\d)(\.\d)?$"
        return openapi_version_supported_regex

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
