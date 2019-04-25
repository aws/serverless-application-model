import copy
from six import string_types

from samtranslator.model.intrinsics import ref
from samtranslator.model.intrinsics import make_conditional
from samtranslator.model.exceptions import InvalidDocumentException, InvalidTemplateException


class SwaggerEditor(object):
    """
    Wrapper class capable of parsing and generating Swagger JSON.  This implements Swagger spec just enough that SAM
    cares about. It is built to handle "partial Swagger" ie. Swagger that is incomplete and won't
    pass the Swagger spec. But this is necessary for SAM because it iteratively builds the Swagger starting from an
    empty skeleton.
    """

    _OPTIONS_METHOD = "options"
    _X_APIGW_INTEGRATION = 'x-amazon-apigateway-integration'
    _CONDITIONAL_IF = "Fn::If"
    _X_APIGW_GATEWAY_RESPONSES = 'x-amazon-apigateway-gateway-responses'
    _X_ANY_METHOD = 'x-amazon-apigateway-any-method'

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
        return self.has_path(path, method) and \
            isinstance(path_dict[method], dict) and \
            self.method_has_integration(path_dict[method])  # Integration present and non-empty

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
                [InvalidTemplateException("Value of '{}' path must be a dictionary according to Swagger spec."
                                          .format(path))])

        if self._CONDITIONAL_IF in path_dict:
            path_dict = path_dict[self._CONDITIONAL_IF][1]

        path_dict.setdefault(method, {})

    def add_lambda_integration(self, path, method, integration_uri,
                               method_auth_config=None, api_auth_config=None, condition=None):
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
                'type': 'aws_proxy',
                'httpMethod': 'POST',
                'uri': integration_uri
        }

        method_auth_config = method_auth_config or {}
        api_auth_config = api_auth_config or {}
        if method_auth_config.get('Authorizer') == 'AWS_IAM' \
           or api_auth_config.get('DefaultAuthorizer') == 'AWS_IAM' and not method_auth_config:
            self.paths[path][method][self._X_APIGW_INTEGRATION]['credentials'] = self._generate_integration_credentials(
                method_invoke_role=method_auth_config.get('InvokeRole'),
                api_invoke_role=api_auth_config.get('InvokeRole')
            )

        # If 'responses' key is *not* present, add it with an empty dict as value
        path_dict[method].setdefault('responses', {})

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
        CALLER_CREDENTIALS_ARN = 'arn:aws:iam::*:user/*'
        return invoke_role if invoke_role and invoke_role != 'CALLER_CREDENTIALS' else CALLER_CREDENTIALS_ARN

    def iter_on_path(self):
        """
        Yields all the paths available in the Swagger. As a caller, if you add new paths to Swagger while iterating,
        they will not show up in this iterator

        :yields string: Path name
        """

        for path, value in self.paths.items():
            yield path

    def add_cors(self, path, allowed_origins, allowed_headers=None, allowed_methods=None, max_age=None,
                 allow_credentials=None):
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
        self.get_path(path)[self._OPTIONS_METHOD] = self._options_method_response_for_cors(allowed_origins,
                                                                                           allowed_headers,
                                                                                           allowed_methods,
                                                                                           max_age,
                                                                                           allow_credentials)

    def _options_method_response_for_cors(self, allowed_origins, allowed_headers=None, allowed_methods=None,
                                          max_age=None, allow_credentials=None):
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
        HEADER_RESPONSE = (lambda x: "method.response.header." + x)

        response_parameters = {
            # AllowedOrigin is always required
            HEADER_RESPONSE(ALLOW_ORIGIN): allowed_origins
        }

        response_headers = {
            # Allow Origin is always required
            ALLOW_ORIGIN: {
                "type": "string"
            }
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
                "requestTemplates": {
                    "application/json": "{\n  \"statusCode\" : 200\n}\n"
                },
                "responses": {
                    "default": {
                        "statusCode": "200",
                        "responseParameters": response_parameters,
                        "responseTemplates": {
                            "application/json": "{}\n"
                        }
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Default response for CORS method",
                    "headers": response_headers
                }
            }
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

        # https://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html
        all_http_methods = ["OPTIONS", "GET", "HEAD", "POST", "PUT", "DELETE", "PATCH"]

        if not self.has_path(path):
            return ""

        # At this point, value of Swagger path should be a dictionary with method names being the keys
        methods = list(self.get_path(path).keys())

        if self._X_ANY_METHOD in methods:
            # API Gateway's ANY method is not a real HTTP method but a wildcard representing all HTTP methods
            allow_methods = all_http_methods
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
        return ','.join(allow_methods)

    def add_authorizers(self, authorizers):
        """
        Add Authorizer definitions to the securityDefinitions part of Swagger.

        :param list authorizers: List of Authorizer configurations which get translated to securityDefinitions.
        """
        self.security_definitions = self.security_definitions or {}

        for authorizer_name, authorizer in authorizers.items():
            self.security_definitions[authorizer_name] = authorizer.generate_swagger()

    def set_path_default_authorizer(self, path, default_authorizer, authorizers):
        """
        Sets the DefaultAuthorizer for each method on this path. The DefaultAuthorizer won't be set if an Authorizer
        was defined at the Function/Path/Method level

        :param string path: Path name
        :param string default_authorizer: Name of the authorizer to use as the default. Must be a key in the
            authorizers param.
        :param list authorizers: List of Authorizer configurations defined on the related Api.
        """
        for method_name, method in self.get_path(path).items():
            self.set_method_authorizer(path, method_name, default_authorizer, authorizers,
                                       default_authorizer=default_authorizer, is_default=True)

    def add_auth_to_method(self, path, method_name, auth, api):
        """
        Adds auth settings for this path/method. Auth settings currently consist solely of Authorizers
        but this method will eventually include setting other auth settings such as API Key,
        Resource Policy, etc.

        :param string path: Path name
        :param string method_name: Method name
        :param dict auth: Auth configuration such as Authorizers, ApiKey, ResourcePolicy (only Authorizers supported
                          currently)
        :param dict api: Reference to the related Api's properties as defined in the template.
        """
        method_authorizer = auth and auth.get('Authorizer')
        if method_authorizer:
            api_auth = api.get('Auth')
            api_authorizers = api_auth and api_auth.get('Authorizers')
            default_authorizer = api_auth and api_auth.get('DefaultAuthorizer')

            self.set_method_authorizer(path, method_name, method_authorizer, api_authorizers, default_authorizer)

    def set_method_authorizer(self, path, method_name, authorizer_name, authorizers, default_authorizer,
                              is_default=False):
        normalized_method_name = self._normalize_method_name(method_name)
        # It is possible that the method could have two definitions in a Fn::If block.
        for method_definition in self.get_method_contents(self.get_path(path)[normalized_method_name]):

            # If no integration given, then we don't need to process this definition (could be AWS::NoValue)
            if not self.method_definition_has_integration(method_definition):
                continue
            existing_security = method_definition.get('security', [])
            # TEST: [{'sigv4': []}, {'api_key': []}])
            authorizer_list = ['AWS_IAM']
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

            # If this is the Api-level DefaultAuthorizer we need to check for an
            # existing Authorizer before applying the default. It would be simpler
            # if instead we applied the DefaultAuthorizer first and then simply
            # overwrote it if necessary, however, the order in which things get
            # applied (Function Api Events first; then Api Resource) complicates it.
            if is_default:
                # Check if Function/Path/Method specified 'NONE' for Authorizer
                for idx, security in enumerate(existing_non_authorizer_security):
                    is_none = any(key == 'NONE' for key in security.keys())

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
                    security_dict[authorizer_name] = []
                    authorizer_security = [security_dict]

            # This is a Function/Path/Method level Authorizer; simply set it
            else:
                security_dict = {}
                security_dict[authorizer_name] = []
                authorizer_security = [security_dict]

            security = existing_non_authorizer_security + authorizer_security

            if security:
                method_definition['security'] = security

                # The first element of the method_definition['security'] should be AWS_IAM
                # because authorizer_list = ['AWS_IAM'] is hardcoded above
                if 'AWS_IAM' in method_definition['security'][0]:
                    aws_iam_security_definition = {
                        'AWS_IAM': {
                            'x-amazon-apigateway-authtype': 'awsSigv4',
                            'type': 'apiKey',
                            'name': 'Authorization',
                            'in': 'header'
                        }
                    }
                    if not self.security_definitions:
                        self.security_definitions = aws_iam_security_definition
                    elif 'AWS_IAM' not in self.security_definitions:
                        self.security_definitions.update(aws_iam_security_definition)

    def add_gateway_responses(self, gateway_responses):
        """
        Add Gateway Response definitions to Swagger.

        :param dict gateway_responses: Dictionary of GatewayResponse configuration which gets translated.
        """
        self.gateway_responses = self.gateway_responses or {}

        for response_type, response in gateway_responses.items():
            self.gateway_responses[response_type] = response.generate_swagger()

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

        return copy.deepcopy(self._doc)

    @staticmethod
    def is_valid(data):
        """
        Checks if the input data is a Swagger document

        :param dict data: Data to be validated
        :return: True, if data is a Swagger
        """
        return bool(data) and \
            isinstance(data, dict) and \
            bool(data.get("swagger")) and \
            isinstance(data.get('paths'), dict)

    @staticmethod
    def gen_skeleton():
        """
        Method to make an empty swagger file, with just some basic structure. Just enough to pass validator.

        :return dict: Dictionary of a skeleton swagger document
        """
        return {
            'swagger': '2.0',
            'info': {
                'version': '1.0',
                'title': ref('AWS::StackName')
            },
            'paths': {
            }
        }

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
        if method == 'any':
            return SwaggerEditor._X_ANY_METHOD
        else:
            return method
