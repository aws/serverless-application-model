"""Base class for OpenApiEditor and SwaggerEditor."""
import re
from typing import Any, Dict, Iterator, List, Optional, Union

from samtranslator.model.apigateway import ApiGatewayAuthorizer
from samtranslator.model.apigatewayv2 import ApiGatewayV2Authorizer
from samtranslator.model.exceptions import InvalidDocumentException, InvalidTemplateException
from samtranslator.model.intrinsics import is_intrinsic_no_value, make_conditional
from samtranslator.utils.py27hash_fix import Py27Dict


class BaseEditor:
    # constants:
    _X_APIGW_INTEGRATION = "x-amazon-apigateway-integration"
    _CONDITIONAL_IF = "Fn::If"
    _X_ANY_METHOD = "x-amazon-apigateway-any-method"
    # https://www.w3.org/Protocols/rfc2616/rfc2616-sec9.html
    _ALL_HTTP_METHODS = ["OPTIONS", "GET", "HEAD", "POST", "PUT", "DELETE", "PATCH"]
    _SERVERS = "servers"
    _OPENAPI_VERSION_3_REGEX = r"\A3(\.\d)(\.\d)?$"

    # attributes:
    _doc: Dict[str, Any]
    paths: Dict[str, Any]

    @staticmethod
    def get_conditional_contents(item: Any) -> List[Any]:
        """
        Returns the contents of the given item.
        If a conditional block has been used inside the item, returns a list of the content
        inside the conditional (both the then and the else cases). Skips {'Ref': 'AWS::NoValue'} content.
        If there's no conditional block, then returns an list with the single item in it.

        :param dict item: item from which the contents will be extracted
        :return: list of item content
        """
        contents = [item]
        if isinstance(item, dict) and BaseEditor._CONDITIONAL_IF in item:
            if_parameters = item[BaseEditor._CONDITIONAL_IF]
            if not isinstance(if_parameters, list):
                raise InvalidDocumentException(
                    [InvalidTemplateException(f"Value of {BaseEditor._CONDITIONAL_IF} must be a list.")]
                )
            contents = if_parameters[1:]
            return [content for content in contents if not is_intrinsic_no_value(content)]
        return contents

    @staticmethod
    def method_definition_has_integration(method_definition: Dict[str, Any]) -> bool:
        """
        Checks a method definition to make sure it has an apigw integration

        :param dict method_definition: method definition dictionary
        :return: True if an integration exists
        """
        return bool(method_definition.get(BaseEditor._X_APIGW_INTEGRATION))

    def method_has_integration(self, raw_method_definition: Dict[str, Any], path: str, method: str) -> bool:
        """
        Returns true if the given method contains a valid method definition.
        This uses the get_conditional_contents function to handle conditionals.

        :param dict raw_method_definition: raw method dictionary
        :param str path: path name
        :param str method: method name
        :return: true if method has one or multiple integrations
        """
        for method_definition in self.get_conditional_contents(raw_method_definition):
            self.validate_method_definition_is_dict(method_definition, path, method)
            if self.method_definition_has_integration(method_definition):
                return True
        return False

    def make_path_conditional(self, path: str, condition: str) -> None:
        """
        Wrap entire API path definition in a CloudFormation if condition.
        :param path: path name
        :param condition: condition name
        """
        self.paths[path] = make_conditional(condition, self.paths[path])

    def iter_on_path(self) -> Iterator[str]:
        """
        Yields all the paths available in the Swagger. As a caller, if you add new paths to Swagger while iterating,
        they will not show up in this iterator

        :yields string: Path name
        """

        for path, _ in self.paths.items():
            yield path

    @staticmethod
    def _normalize_method_name(method: Any) -> Any:
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
            return BaseEditor._X_ANY_METHOD
        return method

    def has_path(self, path: str, method: Optional[str] = None) -> bool:
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
                if not isinstance(path_item, dict) or method not in path_item:
                    return False
        return True

    def has_integration(self, path: str, method: str) -> bool:
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
            BaseEditor.validate_path_item_is_dict(path_item, path)
            method_definition = path_item.get(method)
            if not (
                isinstance(method_definition, dict) and self.method_has_integration(method_definition, path, method)
            ):
                return False
        # Integration present and non-empty
        return True

    def add_path(self, path: str, method: Optional[str] = None) -> None:
        """
        Adds the path/method combination to the Swagger, if not already present

        :param string path: Path name
        :param string method: HTTP method
        :raises InvalidDocumentException: If the value of `path` in Swagger is not a dictionary
        """
        method = self._normalize_method_name(method)

        path_dict = self.paths.setdefault(path, Py27Dict())

        if not isinstance(path_dict, dict):
            # Either customers has provided us an invalid Swagger, or this class has messed it somehow
            raise InvalidDocumentException(
                [InvalidTemplateException(f"Value of '{path}' path must be a dictionary according to Swagger spec.")]
            )

        for path_item in self.get_conditional_contents(path_dict):
            path_item.setdefault(method, Py27Dict())

    def add_timeout_to_method(self, api: Dict[str, Any], path: str, method_name: str, timeout: int) -> None:
        """
        Adds a timeout to the path/method.

        :param api: dict containing Api to be modified
        :param path: string of path name
        :param method_name: string of method name
        :param timeout: int of timeout duration in milliseconds

        """
        for method_definition in self.iter_on_method_definitions_for_path_at_method(path, method_name):
            method_definition[self._X_APIGW_INTEGRATION]["timeoutInMillis"] = timeout

    @staticmethod
    def _get_authorization_scopes(
        authorizers: Union[Dict[str, ApiGatewayAuthorizer], Dict[str, ApiGatewayV2Authorizer]], default_authorizer: str
    ) -> Any:
        """
        Returns auth scopes for an authorizer if present
        :param authorizers: authorizer definitions
        :param default_authorizer: name of the default authorizer
        """
        authorizer = authorizers.get(default_authorizer)
        if authorizer and authorizer.authorization_scopes is not None:
            return authorizer.authorization_scopes
        return []

    def iter_on_method_definitions_for_path_at_method(
        self, path_name: str, method_name: str, skip_methods_without_apigw_integration: bool = True
    ) -> Iterator[Dict[str, Any]]:
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
            BaseEditor.validate_path_item_is_dict(path_item, path_name)
            for method_definition in self.get_conditional_contents(path_item.get(normalized_method_name)):
                BaseEditor.validate_method_definition_is_dict(method_definition, path_name, method_name)
                if skip_methods_without_apigw_integration and not self.method_definition_has_integration(
                    method_definition
                ):
                    continue
                yield method_definition

    @staticmethod
    def validate_is_dict(obj: Any, exception_message: str) -> None:
        """
        Throws exception if obj is not a dict

        :param obj: object being validated
        :param exception_message: message to include in exception if obj is not a dict
        """

        if not isinstance(obj, dict):
            raise InvalidDocumentException([InvalidTemplateException(exception_message)])

    @staticmethod
    def validate_path_item_is_dict(path_item: Any, path: str) -> None:
        """
        Throws exception if path_item is not a dict

        :param path_item: path_item (value at the path) being validated
        :param path: path name
        """

        BaseEditor.validate_is_dict(
            path_item, f"Value of '{path}' path must be a dictionary according to Swagger spec."
        )

    @staticmethod
    def validate_method_definition_is_dict(method_definition: Optional[Any], path: str, method: str) -> None:
        BaseEditor.validate_is_dict(
            method_definition, f"Definition of method '{method}' for path '{path}' should be a map."
        )

    @staticmethod
    def safe_compare_regex_with_string(regex: str, data: Any) -> bool:
        return re.match(regex, str(data)) is not None
