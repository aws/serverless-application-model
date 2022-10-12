import copy
import re

from samtranslator.model.intrinsics import ref, make_conditional, fnSub, is_intrinsic_no_value
from samtranslator.model.exceptions import InvalidDocumentException, InvalidTemplateException
from samtranslator.utils.py27hash_fix import Py27Dict, Py27UniStr


class SwaggerEditor(object):
    """
    Wrapper class capable of parsing and generating Swagger JSON.  This implements Swagger spec just enough that SAM
    cares about. It is built to handle "partial Swagger" ie. Swagger that is incomplete and won't
    pass the Swagger spec. But this is necessary for SAM because it iteratively builds the Swagger starting from an
    empty skeleton.

    NOTE (hawflau): To ensure the same logical ID will be generate in Py3 as in Py2 for AWS::Serverless::Api resource,
    we have to apply py27hash_fix. For any dictionary that is created within the swagger body, we need to initiate it
    with Py27Dict() instead of {}. We also need to add keys into the Py27Dict instance one by one, so that the input
    order could be preserved. This is a must for the purpose of preserving the dict key iteration order, which is
    essential for generating the same logical ID.
    """

    _OPTIONS_METHOD = "options"
    _X_APIGW_INTEGRATION = "x-amazon-apigateway-integration"
    _X_APIGW_BINARY_MEDIA_TYPES = "x-amazon-apigateway-binary-media-types"
    _CONDITIONAL_IF = "Fn::If"
    _X_APIGW_GATEWAY_RESPONSES = "x-amazon-apigateway-gateway-responses"
    _X_APIGW_POLICY = "x-amazon-apigateway-policy"
    _X_ANY_METHOD = "x-amazon-apigateway-any-method"
    _X_APIGW_REQUEST_VALIDATORS = "x-amazon-apigateway-request-validators"
    _X_APIGW_REQUEST_VALIDATOR = "x-amazon-apigateway-request-validator"
    _X_ENDPOINT_CONFIG = "x-amazon-apigateway-endpoint-configuration"
    _CACHE_KEY_PARAMETERS = "cacheKeyParameters"
    # https://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html
    _ALL_HTTP_METHODS = ["OPTIONS", "GET", "HEAD", "POST", "PUT", "DELETE", "PATCH"]
    _EXCLUDED_PATHS_FIELDS = ["summary", "description", "parameters"]
    _POLICY_TYPE_IAM = "Iam"
    _POLICY_TYPE_IP = "Ip"
    _POLICY_TYPE_VPC = "Vpc"

    def __init__(self, doc):
        """
        Initialize the class with a swagger dictionary. This class creates a copy of the Swagger and performs all
        modifications on this copy.

        :param dict doc: Swagger document as a dictionary
        :raises InvalidDocumentException: If the input Swagger document does not meet the basic Swagger requirements.
        """

        if not SwaggerEditor.is_valid(doc):
            raise InvalidDocumentException([InvalidTemplateException("Invalid Swagger document")])

        self._doc = copy.deepcopy(doc)
        self.paths = self._doc["paths"]
        self.security_definitions = self._doc.get("securityDefinitions", Py27Dict())
        self.gateway_responses = self._doc.get(self._X_APIGW_GATEWAY_RESPONSES, Py27Dict())
        self.resource_policy = self._doc.get(self._X_APIGW_POLICY, Py27Dict())
        self.definitions = self._doc.get("definitions", Py27Dict())

        # https://swagger.io/specification/#path-item-object
        # According to swagger spec,
        # each path item object must be a dict (even it is empty).
        # We can do an early path validation on path item objects,
        # so we don't need to validate wherever we use them.
        for path in self.iter_on_path():
            for path_item in self.get_conditional_contents(self.paths.get(path)):
                SwaggerEditor.validate_path_item_is_dict(path_item, path)

    def get_conditional_contents(self, item):
        """
        Returns the contents of the given item.
        If a conditional block has been used inside the item, returns a list of the content
        inside the conditional (both the then and the else cases). Skips {'Ref': 'AWS::NoValue'} content.
        If there's no conditional block, then returns an list with the single item in it.

        :param dict item: item from which the contents will be extracted
        :return: list of item content
        """
        contents = [item]
        if isinstance(item, dict) and self._CONDITIONAL_IF in item:
            contents = item[self._CONDITIONAL_IF][1:]
            contents = [content for content in contents if not is_intrinsic_no_value(content)]
        return contents

    def has_path(self, path, method=None):
        """
        Returns True if this Swagger has the given path and optional method
        For paths with conditionals, only returns true if both items (true case, and false case) have the method.

        :param string path: Path name
        :param string method: HTTP method
        :return: True, if this path/method is present in the document
        """
        if path not in self.paths:
            return False

        method = self._normalize_method_name(method)
        if method:
            for path_item in self.get_conditional_contents(self.paths.get(path)):
                if method not in path_item:
                    return False
        return True

    def method_has_integration(self, method):
        """
        Returns true if the given method contains a valid method definition.
        This uses the get_conditional_contents function to handle conditionals.

        :param dict method: method dictionary
        :return: true if method has one or multiple integrations
        """
        for method_definition in self.get_conditional_contents(method):
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

    def add_disable_execute_api_endpoint_extension(self, disable_execute_api_endpoint):
        """Add endpoint configuration to _X_APIGW_ENDPOINT_CONFIG in open api definition as extension
        Following this guide:
        https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-swagger-extensions-endpoint-configuration.html
        :param boolean disable_execute_api_endpoint: Specifies whether clients can invoke your API by using the default execute-api endpoint.
        """
        if not self._doc.get(self._X_ENDPOINT_CONFIG):
            self._doc[self._X_ENDPOINT_CONFIG] = {}

        DISABLE_EXECUTE_API_ENDPOINT = "disableExecuteApiEndpoint"
        set_disable_api_endpoint = {DISABLE_EXECUTE_API_ENDPOINT: disable_execute_api_endpoint}
        self._doc[self._X_ENDPOINT_CONFIG].update(set_disable_api_endpoint)

    def has_integration(self, path, method):
        """
        Checks if an API Gateway integration is already present at the given path/method.
        For paths with conditionals, it only returns True if both items (true case, false case) have the integration

        :param string path: Path name
        :param string method: HTTP method
        :return: True, if an API Gateway integration is already present
        """
        method = self._normalize_method_name(method)

        if not self.has_path(path, method):
            return False

        for path_item in self.get_conditional_contents(self.paths.get(path)):
            method_definition = path_item.get(method)
            if not (isinstance(method_definition, dict) and self.method_has_integration(method_definition)):
                return False
        # Integration present and non-empty
        return True

    def add_path(self, path, method=None):
        """
        Adds the path/method combination to the Swagger, if not already present

        :param string path: Path name
        :param string method: HTTP method
        """
        method = self._normalize_method_name(method)

        self.paths.setdefault(path, Py27Dict())

        for path_item in self.get_conditional_contents(self.paths.get(path)):
            path_item.setdefault(method, Py27Dict())

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
            raise InvalidDocumentException(
                [
                    InvalidTemplateException(
                        "Lambda integration already exists on Path={}, Method={}".format(path, method)
                    )
                ]
            )

        self.add_path(path, method)

        # Wrap the integration_uri in a Condition if one exists on that function
        # This is necessary so CFN doesn't try to resolve the integration reference.
        if condition:
            integration_uri = make_conditional(condition, integration_uri)

        for path_item in self.get_conditional_contents(self.paths.get(path)):
            path_item[method][self._X_APIGW_INTEGRATION] = Py27Dict()
            # insert key one by one to preserce input order
            path_item[method][self._X_APIGW_INTEGRATION]["type"] = "aws_proxy"
            path_item[method][self._X_APIGW_INTEGRATION]["httpMethod"] = "POST"
            path_item[method][self._X_APIGW_INTEGRATION]["uri"] = integration_uri

            method_auth_config = method_auth_config or Py27Dict()
            api_auth_config = api_auth_config or Py27Dict()
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
                    path_item[method][self._X_APIGW_INTEGRATION]["credentials"] = credentials

            # If 'responses' key is *not* present, add it with an empty dict as value
            path_item[method].setdefault("responses", Py27Dict())

            # If a condition is present, wrap all method contents up into the condition
            if condition:
                path_item[method] = make_conditional(condition, path_item[method])

    def add_state_machine_integration(
        self,
        path,
        method,
        integration_uri,
        credentials,
        request_templates=None,
        condition=None,
    ):
        """
        Adds aws APIGW integration to the given path+method.

        :param string path: Path name
        :param string method: HTTP Method
        :param string integration_uri: URI for the integration
        :param string credentials: Credentials for the integration
        :param dict request_templates: A map of templates that are applied on the request payload.
        :param bool condition: Condition for the integration
        """

        method = self._normalize_method_name(method)
        if self.has_integration(path, method):
            raise InvalidDocumentException(
                [InvalidTemplateException("Integration already exists on Path={}, Method={}".format(path, method))]
            )

        self.add_path(path, method)

        # Wrap the integration_uri in a Condition if one exists on that state machine
        # This is necessary so CFN doesn't try to resolve the integration reference.
        if condition:
            integration_uri = make_conditional(condition, integration_uri)

        for path_item in self.get_conditional_contents(self.paths.get(path)):
            # Responses
            integration_responses = Py27Dict()
            # insert key one by one to preserce input order
            integration_responses["200"] = Py27Dict({"statusCode": "200"})
            integration_responses["400"] = Py27Dict({"statusCode": "400"})

            default_method_responses = Py27Dict()
            # insert key one by one to preserce input order
            default_method_responses["200"] = Py27Dict({"description": "OK"})
            default_method_responses["400"] = Py27Dict({"description": "Bad Request"})

            path_item[method][self._X_APIGW_INTEGRATION] = Py27Dict()
            # insert key one by one to preserce input order
            path_item[method][self._X_APIGW_INTEGRATION]["type"] = "aws"
            path_item[method][self._X_APIGW_INTEGRATION]["httpMethod"] = "POST"
            path_item[method][self._X_APIGW_INTEGRATION]["uri"] = integration_uri
            path_item[method][self._X_APIGW_INTEGRATION]["responses"] = integration_responses
            path_item[method][self._X_APIGW_INTEGRATION]["credentials"] = credentials

            # If 'responses' key is *not* present, add it with an empty dict as value
            path_item[method].setdefault("responses", default_method_responses)

            if request_templates:
                path_item[method][self._X_APIGW_INTEGRATION].update({"requestTemplates": request_templates})

            # If a condition is present, wrap all method contents up into the condition
            if condition:
                path_item[method] = make_conditional(condition, path_item[method])

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

    def iter_on_method_definitions_for_path_at_method(
        self, path_name, method_name, skip_methods_without_apigw_integration=True
    ):
        """
        Yields all the method definitions for the path+method combinations if path and/or method have IF conditionals.
        If there are no conditionals, will just yield the single method definition at the given path and method name.

        :param path_name: path name
        :param method_name: method name
        :param skip_methods_without_apigw_integration: if True, skips method definitions without apigw integration
        :yields dict: method definition
        """
        normalized_method_name = self._normalize_method_name(method_name)

        for path_item in self.get_conditional_contents(self.paths.get(path_name)):
            for method_definition in self.get_conditional_contents(path_item.get(normalized_method_name)):
                if skip_methods_without_apigw_integration and not self.method_definition_has_integration(
                    method_definition
                ):
                    continue
                yield method_definition

    def iter_on_all_methods_for_path(self, path_name, skip_methods_without_apigw_integration=True):
        """
        Yields all the (method name, method definition) tuples for the path, including those inside conditionals.

        :param path_name: path name
        :param skip_methods_without_apigw_integration: if True, skips method definitions without apigw integration
        :yields list of (method name, method definition) tuples
        """
        for path_item in self.get_conditional_contents(self.paths.get(path_name)):
            for method_name, method in path_item.items():
                # Excluding non-method sections
                if method_name in SwaggerEditor._EXCLUDED_PATHS_FIELDS:
                    continue

                for method_definition in self.get_conditional_contents(method):
                    SwaggerEditor.validate_is_dict(
                        method_definition,
                        'Value of "{}" ({}) for path {} is not a valid dictionary.'.format(
                            method_name, method_definition, path_name
                        ),
                    )
                    if skip_methods_without_apigw_integration and not self.method_definition_has_integration(
                        method_definition
                    ):
                        continue
                    normalized_method_name = self._normalize_method_name(method_name)
                    yield normalized_method_name, method_definition

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
        :raises InvalidTemplateException: When values for one of the allowed_* variables is empty
        """

        for path_item in self.get_conditional_contents(self.paths.get(path)):
            # Skip if Options is already present
            method = self._normalize_method_name(self._OPTIONS_METHOD)
            if method in path_item:
                continue

            if not allowed_origins:
                raise InvalidTemplateException("Invalid input. Value for AllowedOrigins is required")

            if not allowed_methods:
                # AllowMethods is not given. Let's try to generate the list from the given Swagger.
                allowed_methods = self._make_cors_allowed_methods_for_path_item(path_item)

                # APIGW expects the value to be a "string expression". Hence wrap in another quote. Ex: "'GET,POST,DELETE'"
                allowed_methods = "'{}'".format(allowed_methods)

            if allow_credentials is not True:
                allow_credentials = False

            # Add the Options method and the CORS response
            path_item[self._OPTIONS_METHOD] = self._options_method_response_for_cors(
                allowed_origins, allowed_headers, allowed_methods, max_age, allow_credentials
            )

    def add_binary_media_types(self, binary_media_types):
        """
        Args:
            binary_media_types: list
        """

        def replace_recursively(bmt):
            """replaces "~1" with "/" for the input binary_media_types recursively"""
            if isinstance(bmt, dict):
                to_return = Py27Dict()
                for k, v in bmt.items():
                    to_return[Py27UniStr(k.replace("~1", "/"))] = replace_recursively(v)
                return to_return
            if isinstance(bmt, list):
                return [replace_recursively(item) for item in bmt]
            if isinstance(bmt, str) or isinstance(bmt, Py27UniStr):
                return Py27UniStr(bmt.replace("~1", "/"))
            return bmt

        bmt = replace_recursively(binary_media_types)
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

        response_parameters = Py27Dict(
            {
                # AllowedOrigin is always required
                HEADER_RESPONSE(ALLOW_ORIGIN): allowed_origins
            }
        )

        response_headers = Py27Dict(
            {
                # Allow Origin is always required
                ALLOW_ORIGIN: {"type": "string"}
            }
        )

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

        # construct snippet and insert key one by one to preserce input order
        to_return = Py27Dict()
        to_return["summary"] = "CORS support"
        to_return["consumes"] = ["application/json"]
        to_return["produces"] = ["application/json"]
        to_return[self._X_APIGW_INTEGRATION] = Py27Dict()
        to_return[self._X_APIGW_INTEGRATION]["type"] = "mock"
        to_return[self._X_APIGW_INTEGRATION]["requestTemplates"] = {"application/json": '{\n  "statusCode" : 200\n}\n'}
        to_return[self._X_APIGW_INTEGRATION]["responses"] = Py27Dict()
        to_return[self._X_APIGW_INTEGRATION]["responses"]["default"] = Py27Dict()
        to_return[self._X_APIGW_INTEGRATION]["responses"]["default"]["statusCode"] = "200"
        to_return[self._X_APIGW_INTEGRATION]["responses"]["default"]["responseParameters"] = response_parameters
        to_return[self._X_APIGW_INTEGRATION]["responses"]["default"]["responseTemplates"] = {"application/json": "{}\n"}
        to_return["responses"] = Py27Dict()
        to_return["responses"]["200"] = Py27Dict()
        to_return["responses"]["200"]["description"] = "Default response for CORS method"
        to_return["responses"]["200"]["headers"] = response_headers
        return to_return

    def _make_cors_allowed_methods_for_path_item(self, path_item):
        """
        Creates the value for Access-Control-Allow-Methods header for given path item. All HTTP methods defined for this
        path item will be included in the result. If the path item contains "ANY" method, then *all available* HTTP methods will
        be returned as result.

        :param dict path_item: Path item to generate AllowMethods value for
        :return string: String containing the value of AllowMethods, if the path item contains any methods.
                        "OPTIONS", otherwise
        """
        methods = list(path_item.keys())

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
        self.security_definitions = self.security_definitions or Py27Dict()

        for authorizer_name, authorizer in authorizers.items():
            self.security_definitions[authorizer_name] = authorizer.generate_swagger()

    def add_awsiam_security_definition(self):
        """
        Adds AWS_IAM definition to the securityDefinitions part of Swagger.
        Note: this method is idempotent
        """

        # construct aws_iam_security_definition as Py27Dict and insert key one by one to preserce input order
        aws_iam_security_definition = Py27Dict()
        aws_iam_security_definition["AWS_IAM"] = Py27Dict()
        aws_iam_security_definition["AWS_IAM"]["x-amazon-apigateway-authtype"] = "awsSigv4"
        aws_iam_security_definition["AWS_IAM"]["type"] = "apiKey"
        aws_iam_security_definition["AWS_IAM"]["name"] = "Authorization"
        aws_iam_security_definition["AWS_IAM"]["in"] = "header"

        self.security_definitions = self.security_definitions or Py27Dict()

        # Only add the security definition if it doesn't exist.  This helps ensure
        # that we minimize changes to the swagger in the case of user defined swagger
        if "AWS_IAM" not in self.security_definitions:
            self.security_definitions.update(aws_iam_security_definition)

    def add_apikey_security_definition(self):
        """
        Adds api_key definition to the securityDefinitions part of Swagger.
        Note: this method is idempotent
        """

        # construct api_key_security_definiton as py27 dict
        # and insert keys one by one to preserve input order
        api_key_security_definition = Py27Dict()
        api_key_security_definition["api_key"] = Py27Dict()
        api_key_security_definition["api_key"]["type"] = "apiKey"
        api_key_security_definition["api_key"]["name"] = "x-api-key"
        api_key_security_definition["api_key"]["in"] = "header"

        self.security_definitions = self.security_definitions or Py27Dict()

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

        for method_name, method_definition in self.iter_on_all_methods_for_path(path):
            if not (add_default_auth_to_preflight or method_name != "options"):
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
                SwaggerEditor.validate_is_dict(
                    security,
                    "{} in Security for path {} method {} is not a valid dictionary.".format(
                        security, path, method_name
                    ),
                )
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
                security_dict = Py27Dict()
                security_dict[default_authorizer] = self._get_authorization_scopes(api_authorizers, default_authorizer)
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

        for method_name, method_definition in self.iter_on_all_methods_for_path(path):
            existing_security = method_definition.get("security", [])
            apikey_security_names = set(["api_key", "api_key_false"])
            existing_non_apikey_security = []
            existing_apikey_security = []
            apikey_security = []

            # Split existing security into ApiKey and everything else
            # (e.g. sigv4 (AWS_IAM), authorizers, NONE (marker for ignoring default authorizer))
            # We want to ensure only a single ApiKey security entry exists while keeping everything else
            for security in existing_security:
                SwaggerEditor.validate_is_dict(
                    security,
                    "{} in Security for path {} method {} is not a valid dictionary.".format(
                        security, path, method_name
                    ),
                )
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
                security_dict = Py27Dict()
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

    def _set_method_authorizer(self, path, method_name, authorizer_name, authorizers=None, method_scopes=None):
        """
        Adds the authorizer_name to the security block for each method on this path.
        This is used to configure the authorizer for individual functions.

        :param string path: Path name
        :param string method_name: Method name
        :param string authorizer_name: Name of the authorizer to use. Must be a key in the
            authorizers param.
        """
        if authorizers is None:
            authorizers = Py27Dict()

        for method_definition in self.iter_on_method_definitions_for_path_at_method(path, method_name):
            existing_security = method_definition.get("security", [])

            security_dict = Py27Dict()
            security_dict[authorizer_name] = []
            authorizer_security = [security_dict]

            # This assumes there are no autorizers already configured in the existing security block
            security = existing_security + authorizer_security

            if authorizer_name != "NONE" and authorizers:
                method_auth_scopes = authorizers.get(authorizer_name, Py27Dict()).get("AuthorizationScopes")
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
        for method_definition in self.iter_on_method_definitions_for_path_at_method(path, method_name):
            existing_security = method_definition.get("security", [])

            if apikey_required:
                # We want to enable apikey required security
                security_dict = Py27Dict()
                security_dict["api_key"] = []
                apikey_security = [security_dict]
                self.add_apikey_security_definition()
            else:
                # The method explicitly does NOT require apikey and there is an API default
                # so let's add a marker 'api_key_false' so that we don't incorrectly override
                # with the api default
                security_dict = Py27Dict()
                security_dict["api_key_false"] = []
                apikey_security = [security_dict]

            # This assumes there are no autorizers already configured in the existing security block
            security = existing_security + apikey_security

            if security != existing_security:
                method_definition["security"] = security

    def add_request_validator_to_method(self, path, method_name, validate_body=False, validate_parameters=False):
        """
        Adds request model body parameter for this path/method.

        :param string path: Path name
        :param string method_name: Method name
        :param bool validate_body: Add validator parameter on the body
        :param bool validate_parameters: Validate request
        """

        validator_name = SwaggerEditor.get_validator_name(validate_body, validate_parameters)

        # Creating validator as py27 dict
        # and insert keys one by one to preserve input order
        request_validator_definition = Py27Dict()
        request_validator_definition[validator_name] = Py27Dict()
        request_validator_definition[validator_name]["validateRequestBody"] = validate_body
        request_validator_definition[validator_name]["validateRequestParameters"] = validate_parameters

        if not self._doc.get(self._X_APIGW_REQUEST_VALIDATORS):
            self._doc[self._X_APIGW_REQUEST_VALIDATORS] = Py27Dict()

        if not self._doc[self._X_APIGW_REQUEST_VALIDATORS].get(validator_name):
            # Adding only if the validator hasn't been defined already
            self._doc[self._X_APIGW_REQUEST_VALIDATORS].update(request_validator_definition)

        for method_definition in self.iter_on_method_definitions_for_path_at_method(path, method_name):
            set_validator_to_method = Py27Dict({self._X_APIGW_REQUEST_VALIDATOR: validator_name})
            # Setting validator to the given method
            method_definition.update(set_validator_to_method)

    def add_request_model_to_method(self, path, method_name, request_model):
        """
        Adds request model body parameter for this path/method.

        :param string path: Path name
        :param string method_name: Method name
        :param dict request_model: Model name
        """
        model_name = request_model and request_model.get("Model").lower()
        model_required = request_model and request_model.get("Required")

        for method_definition in self.iter_on_method_definitions_for_path_at_method(path, method_name):
            if self._doc.get("swagger") is not None:

                existing_parameters = method_definition.get("parameters", [])

                # construct parameter as py27 dict
                # and insert keys one by one to preserve input order
                parameter = Py27Dict()
                parameter["in"] = "body"
                parameter["name"] = model_name
                parameter["schema"] = {"$ref": "#/definitions/{}".format(model_name)}

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
        self.gateway_responses = self.gateway_responses or Py27Dict()

        for response_type, response in gateway_responses.items():
            self.gateway_responses[response_type] = response.generate_swagger()

    def add_models(self, models):
        """
        Add Model definitions to Swagger.

        :param dict models: Dictionary of Model schemas which gets translated
        :return:
        """

        self.definitions = self.definitions or Py27Dict()

        for model_name, schema in models.items():

            model_type = schema.get("type")
            model_properties = schema.get("properties")

            if not model_type:
                raise InvalidDocumentException([InvalidTemplateException("'Models' schema is missing 'type'.")])

            if not model_properties:
                raise InvalidDocumentException([InvalidTemplateException("'Models' schema is missing 'properties'.")])

            self.definitions[model_name.lower()] = schema

    def add_resource_policy(self, resource_policy, path, stage):
        """
        Add resource policy definition to Swagger.

        :param dict resource_policy: Dictionary of resource_policy statements which gets translated
        :return:
        """
        if resource_policy is None:
            return
        SwaggerEditor.validate_is_dict(resource_policy, "Resource Policy is not a valid dictionary.")

        aws_account_whitelist = resource_policy.get("AwsAccountWhitelist")
        aws_account_blacklist = resource_policy.get("AwsAccountBlacklist")
        ip_range_whitelist = resource_policy.get("IpRangeWhitelist")
        ip_range_blacklist = resource_policy.get("IpRangeBlacklist")
        source_vpc_whitelist = resource_policy.get("SourceVpcWhitelist")
        source_vpc_blacklist = resource_policy.get("SourceVpcBlacklist")

        # Intrinsic's supported in these properties
        source_vpc_intrinsic_whitelist = resource_policy.get("IntrinsicVpcWhitelist")
        source_vpce_intrinsic_whitelist = resource_policy.get("IntrinsicVpceWhitelist")
        source_vpc_intrinsic_blacklist = resource_policy.get("IntrinsicVpcBlacklist")
        source_vpce_intrinsic_blacklist = resource_policy.get("IntrinsicVpceBlacklist")

        if aws_account_whitelist is not None:
            resource_list = self._get_method_path_uri_list(path, stage)
            self._add_iam_resource_policy_for_method(aws_account_whitelist, "Allow", resource_list)

        if aws_account_blacklist is not None:
            resource_list = self._get_method_path_uri_list(path, stage)
            self._add_iam_resource_policy_for_method(aws_account_blacklist, "Deny", resource_list)

        if ip_range_whitelist is not None:
            resource_list = self._get_method_path_uri_list(path, stage)
            self._add_ip_resource_policy_for_method(ip_range_whitelist, "NotIpAddress", resource_list)

        if ip_range_blacklist is not None:
            resource_list = self._get_method_path_uri_list(path, stage)
            self._add_ip_resource_policy_for_method(ip_range_blacklist, "IpAddress", resource_list)

        if not SwaggerEditor._validate_list_property_is_resolved(source_vpc_blacklist):
            raise InvalidDocumentException(
                [
                    InvalidTemplateException(
                        "SourceVpcBlacklist must be a list of strings. Use IntrinsicVpcBlacklist instead for values that use Intrinsic Functions"
                    )
                ]
            )

        # FIXME: check if this requires py27 dict?
        blacklist_dict = {
            "StringEndpointList": source_vpc_blacklist,
            "IntrinsicVpcList": source_vpc_intrinsic_blacklist,
            "IntrinsicVpceList": source_vpce_intrinsic_blacklist,
        }
        resource_list = self._get_method_path_uri_list(path, stage)
        self._add_vpc_resource_policy_for_method(blacklist_dict, "StringEquals", resource_list)

        if not SwaggerEditor._validate_list_property_is_resolved(source_vpc_whitelist):
            raise InvalidDocumentException(
                [
                    InvalidTemplateException(
                        "SourceVpcWhitelist must be a list of strings. Use IntrinsicVpcWhitelist instead for values that use Intrinsic Functions"
                    )
                ]
            )

        whitelist_dict = {
            "StringEndpointList": source_vpc_whitelist,
            "IntrinsicVpcList": source_vpc_intrinsic_whitelist,
            "IntrinsicVpceList": source_vpce_intrinsic_whitelist,
        }
        self._add_vpc_resource_policy_for_method(whitelist_dict, "StringNotEquals", resource_list)

        self._doc[self._X_APIGW_POLICY] = self.resource_policy

    def add_custom_statements(self, custom_statements):
        self._add_custom_statement(custom_statements)

        self._doc[self._X_APIGW_POLICY] = self.resource_policy

    def _add_iam_resource_policy_for_method(self, policy_list, effect, resource_list):
        """
        This method generates a policy statement to grant/deny specific IAM users access to the API method and
        appends it to the swagger under `x-amazon-apigateway-policy`
        :raises InvalidDocumentException: If the effect passed in does not match the allowed values.
        """
        if not policy_list:
            return

        if effect not in ["Allow", "Deny"]:
            raise InvalidDocumentException(
                [InvalidTemplateException("Effect must be one of {}".format(["Allow", "Deny"]))]
            )

        if not isinstance(policy_list, (dict, list)):
            raise InvalidDocumentException(
                [InvalidTemplateException("Type of '{}' must be a list or dictionary".format(policy_list))]
            )

        if not isinstance(policy_list, list):
            policy_list = [policy_list]

        self.resource_policy["Version"] = "2012-10-17"
        policy_statement = Py27Dict()
        policy_statement["Effect"] = effect
        policy_statement["Action"] = "execute-api:Invoke"
        policy_statement["Resource"] = resource_list
        policy_statement["Principal"] = Py27Dict({"AWS": policy_list})

        if self.resource_policy.get("Statement") is None:
            self.resource_policy["Statement"] = policy_statement
        else:
            statement = self.resource_policy["Statement"]
            if not isinstance(statement, list):
                statement = [statement]
            statement.extend([policy_statement])
            self.resource_policy["Statement"] = statement

    def _get_method_path_uri_list(self, path, stage):
        """
        It turns out that APIGW doesn't like trailing slashes in paths (#665)
        and removes as a part of their behavior, but this isn't documented.
        The regex removes the trailing slash to ensure the permission works as intended
        """
        methods = []
        for path_item in self.get_conditional_contents(self.paths.get(path)):
            methods += list(path_item.keys())

        uri_list = []
        path = SwaggerEditor.get_path_without_trailing_slash(path)

        for m in methods:
            method = "*" if (m.lower() == self._X_ANY_METHOD or m.lower() == "any") else m.upper()
            resource = "execute-api:/${__Stage__}/" + method + path
            resource = (
                Py27UniStr(resource) if isinstance(method, Py27UniStr) or isinstance(path, Py27UniStr) else resource
            )
            resource = fnSub(resource, {"__Stage__": stage})
            uri_list.extend([resource])
        return uri_list

    def _add_ip_resource_policy_for_method(self, ip_list, conditional, resource_list):
        """
        This method generates a policy statement to grant/deny specific IP address ranges access to the API method and
        appends it to the swagger under `x-amazon-apigateway-policy`
        :raises InvalidDocumentException: If the conditional passed in does not match the allowed values.
        """
        if not ip_list:
            return

        if not isinstance(ip_list, list):
            ip_list = [ip_list]

        if conditional not in ["IpAddress", "NotIpAddress"]:
            raise InvalidDocumentException(
                [InvalidTemplateException("Conditional must be one of {}".format(["IpAddress", "NotIpAddress"]))]
            )

        self.resource_policy["Version"] = "2012-10-17"
        allow_statement = Py27Dict()
        allow_statement["Effect"] = "Allow"
        allow_statement["Action"] = "execute-api:Invoke"
        allow_statement["Resource"] = resource_list
        allow_statement["Principal"] = "*"

        deny_statement = Py27Dict()
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

    def _add_vpc_resource_policy_for_method(self, endpoint_dict, conditional, resource_list):
        """
        This method generates a policy statement to grant/deny specific VPC/VPCE access to the API method and
        appends it to the swagger under `x-amazon-apigateway-policy`
        :raises InvalidDocumentException: If the conditional passed in does not match the allowed values.
        """

        if conditional not in ["StringNotEquals", "StringEquals"]:
            raise InvalidDocumentException(
                [InvalidTemplateException("Conditional must be one of {}".format(["StringNotEquals", "StringEquals"]))]
            )

        condition = Py27Dict()
        string_endpoint_list = endpoint_dict.get("StringEndpointList")
        intrinsic_vpc_endpoint_list = endpoint_dict.get("IntrinsicVpcList")
        intrinsic_vpce_endpoint_list = endpoint_dict.get("IntrinsicVpceList")

        if string_endpoint_list is not None:
            vpce_regex = r"^vpce-"
            vpc_regex = r"^vpc-"
            vpc_list = []
            vpce_list = []
            for endpoint in string_endpoint_list:
                if re.match(vpce_regex, endpoint):
                    vpce_list.append(endpoint)
                if re.match(vpc_regex, endpoint):
                    vpc_list.append(endpoint)
            if vpc_list:
                condition.setdefault("aws:SourceVpc", []).extend(vpc_list)
            if vpce_list:
                condition.setdefault("aws:SourceVpce", []).extend(vpce_list)
        if intrinsic_vpc_endpoint_list is not None:
            condition.setdefault("aws:SourceVpc", []).extend(intrinsic_vpc_endpoint_list)
        if intrinsic_vpce_endpoint_list is not None:
            condition.setdefault("aws:SourceVpce", []).extend(intrinsic_vpce_endpoint_list)

        # Skip writing to transformed template if both vpc and vpce endpoint lists are empty
        if (not condition.get("aws:SourceVpc", [])) and (not condition.get("aws:SourceVpce", [])):
            return

        self.resource_policy["Version"] = "2012-10-17"
        allow_statement = Py27Dict()
        allow_statement["Effect"] = "Allow"
        allow_statement["Action"] = "execute-api:Invoke"
        allow_statement["Resource"] = resource_list
        allow_statement["Principal"] = "*"

        deny_statement = Py27Dict()
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

        for method_definition in self.iter_on_method_definitions_for_path_at_method(path, method_name):
            existing_parameters = method_definition.get("parameters", [])

            for request_parameter in request_parameters:

                parameter_name = request_parameter["Name"]
                location_name = parameter_name.replace("method.request.", "")

                location, name = location_name.split(".", 1)

                if location == "querystring":
                    location = "query"

                # create parameter as py27 dict
                # and insert keys one by one to preserve input orders
                parameter = Py27Dict()
                parameter["in"] = location
                parameter["name"] = name
                parameter["required"] = request_parameter["Required"]
                parameter["type"] = "string"

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
        # iterate keys to make sure if "paths" is of Py27UniStr type, it won't be overriden as str
        for key in self._doc.keys():
            if key == "paths":
                self._doc[key] = self.paths

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
    def validate_is_dict(obj, exception_message):
        """
        Throws exception if obj is not a dict

        :param obj: object being validated
        :param exception_message: message to include in exception if obj is not a dict
        """

        if not isinstance(obj, dict):
            raise InvalidDocumentException([InvalidTemplateException(exception_message)])

    @staticmethod
    def validate_path_item_is_dict(path_item, path):
        """
        Throws exception if path_item is not a dict

        :param path_item: path_item (value at the path) being validated
        :param path: path name
        """

        SwaggerEditor.validate_is_dict(
            path_item, "Value of '{}' path must be a dictionary according to Swagger spec.".format(path)
        )

    @staticmethod
    def gen_skeleton():
        """
        Method to make an empty swagger file, with just some basic structure. Just enough to pass validator.

        :return dict: Dictionary of a skeleton swagger document
        """
        skeleton = Py27Dict()
        skeleton["swagger"] = "2.0"
        skeleton["info"] = Py27Dict()
        skeleton["info"]["version"] = "1.0"
        skeleton["info"]["title"] = ref("AWS::StackName")
        skeleton["paths"] = Py27Dict()
        return skeleton

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
        if not method or not isinstance(method, str):
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
        # convert greedy paths to such as {greedy+}, {proxy+} to "*"
        sub = re.sub(r"{([a-zA-Z0-9._-]+|[a-zA-Z0-9._-]+\+|proxy\+)}", "*", path)
        if isinstance(path, Py27UniStr):
            return Py27UniStr(sub)
        return sub

    @staticmethod
    def get_validator_name(validate_body, validate_parameters):
        """
        Get a readable path name to use as validator name

        :param boolean validate_body: Boolean if validate body
        :param boolean validate_request: Boolean if validate request
        :return string: Normalized validator name
        """
        if validate_body and validate_parameters:
            return "body-and-params"

        if validate_body and not validate_parameters:
            return "body-only"

        if not validate_body and validate_parameters:
            return "params-only"

        return "no-validation"

    @staticmethod
    def _validate_list_property_is_resolved(property_list):
        """
        Validate if the values of a Property List are all of type string

        :param property_list: Value of a Property List
        :return bool: True if the property_list is all of type string otherwise False
        """

        if property_list is not None and not all(isinstance(x, str) for x in property_list):
            return False

        return True
