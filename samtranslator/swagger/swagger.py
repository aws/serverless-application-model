import copy
from six import string_types

from samtranslator.model.intrinsics import ref


class SwaggerEditor(object):
    """
    Wrapper class capable of parsing and generating Swagger JSON.  This implements Swagger spec just enough that SAM
    cares about. It is built to handle "partial Swagger" ie. Swagger that is incomplete and won't
    pass the Swagger spec. But this is necessary for SAM because it iteratively builds the Swagger starting from an
    empty skeleton.
    """

    _OPTIONS_METHOD = "options"
    _X_APIGW_INTEGRATION = 'x-amazon-apigateway-integration'
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

    def has_path(self, path, method=None):
        """
        Returns True if this Swagger has the given path and optional method

        :param string path: Path name
        :param string method: HTTP method
        :return: True, if this path/method is present in the document
        """
        method = self._normalize_method_name(method)

        result = path in self.paths
        if method:
            result = result and \
                    isinstance(self.paths[path], dict) and \
                    method in self.paths[path]

        return result

    def has_integration(self, path, method):
        """
        Checks if an API Gateway integration is already present at the given path/method

        :param string path: Path name
        :param string method: HTTP method
        :return: True, if an API Gateway integration is already present
        """
        method = self._normalize_method_name(method)

        return self.has_path(path, method) and \
            isinstance(self.paths[path][method], dict) and \
            bool(self.paths[path][method].get(self._X_APIGW_INTEGRATION))  # Key should be present & Value is non-empty

    def add_path(self, path, method=None):
        """
        Adds the path/method combination to the Swagger, if not already present

        :param string path: Path name
        :param string method: HTTP method
        :raises ValueError: If the value of `path` in Swagger is not a dictionary
        """
        method = self._normalize_method_name(method)

        self.paths.setdefault(path, {})

        if not isinstance(self.paths[path], dict):
            # Either customers has provided us an invalid Swagger, or this class has messed it somehow
            raise ValueError("Value of '{}' path must be a dictionary according to Swagger spec".format(path))

        self.paths[path].setdefault(method, {})

    def add_lambda_integration(self, path, method, integration_uri):
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

        self.paths[path][method][self._X_APIGW_INTEGRATION] = {
                'type': 'aws_proxy',
                'httpMethod': 'POST',
                'uri': integration_uri
            }

        # If 'responses' key is *not* present, add it with an empty dict as value
        self.paths[path][method].setdefault('responses', {})

    def iter_on_path(self):
        """
        Yields all the paths available in the Swagger. As a caller, if you add new paths to Swagger while iterating,
        they will not show up in this iterator

        :yields string: Path name
        """

        for path, value in self.paths.items():
            yield path

    def add_cors(self, path, allowed_origins, allowed_headers=None, allowed_methods=None, max_age=None):
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

        # Add the Options method and the CORS response
        self.add_path(path, self._OPTIONS_METHOD)
        self.paths[path][self._OPTIONS_METHOD] = self._options_method_response_for_cors(allowed_origins,
                                                                                        allowed_headers,
                                                                                        allowed_methods,
                                                                                        max_age)

    def _options_method_response_for_cors(self, allowed_origins, allowed_headers=None, allowed_methods=None,
                                          max_age=None):
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

        :return dict: Dictionary containing Options method configuration for CORS
        """

        ALLOW_ORIGIN = "Access-Control-Allow-Origin"
        ALLOW_HEADERS = "Access-Control-Allow-Headers"
        ALLOW_METHODS = "Access-Control-Allow-Methods"
        MAX_AGE = "Access-Control-Max-Age"
        HEADER_RESPONSE = lambda x: "method.response.header."+x

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
        methods = self.paths[path].keys()

        if self._X_ANY_METHOD in methods:
            # API Gateway's ANY method is not a real HTTP method but a wildcard representing all HTTP methods
            allow_methods = all_http_methods
        else:
            allow_methods = methods
            allow_methods.append("options") # Always add Options to the CORS methods response

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

    @property
    def swagger(self):
        """
        Returns a **copy** of the Swagger document as a dictionary.

        :return dict: Dictionary containing the Swagger document
        """

        # Make sure any changes to the paths are reflected back in output
        self._doc["paths"] = self.paths
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
