from unittest import TestCase

import pytest
from samtranslator.model import InvalidResourceException
from samtranslator.model.api.websocket_api_generator import WebSocketApiGenerator


class TestWebSocketApiGenerator(TestCase):
    kwargs = {
        "logical_id": "WebSocketApiId",
        "stage_variables": None,
        "depends_on": None,
        "name": "WebSocketApi",
        "stage_name": None,
        "tags": None,
        "auth_config": None,
        "ip_address_type": None,
        "access_log_settings": None,
        "resource_attributes": None,
        "routes": {"$connect": {"FunctionArn": {"Fn::GetAtt": ["ConnectFunction", "Arn"]}}},
        "route_selection_expression": "$request.body.action",
        "passthrough_resource_attributes": None,
        "domain": None,
    }

    def test_auto_generated_name(self):
        kwargs = self.kwargs.copy()
        kwargs["name"] = None
        api = WebSocketApiGenerator(**kwargs)._construct_websocket_api()
        self.assertEqual(api.Name, "WebSocketApiId")

    def test_auth_type_no_id(self):
        kwargs = self.kwargs.copy()
        # A copy is created because using self.kwargs directly required resetting the values at the end.
        # In this case, a failed test could exit before resetting the value and cause problems for other tests.
        kwargs["auth_config"] = {"AuthType": "AWS_IAM"}
        WebSocketApiGenerator(**kwargs)._construct_websocket_api()
        r, _, _, _ = WebSocketApiGenerator(**kwargs)._construct_route_infr("$connect", kwargs["routes"]["$connect"])
        self.assertEqual(r.AuthorizationType, "AWS_IAM")

    def test_perms(self):
        kwargs = self.kwargs.copy()
        WebSocketApiGenerator(**kwargs)._construct_websocket_api()
        _, _, perm, _ = WebSocketApiGenerator(**kwargs)._construct_route_infr("$connect", kwargs["routes"]["$connect"])
        self.assertEqual(
            perm.SourceArn["Fn::Sub"],
            "arn:${AWS::Partition}:execute-api:${AWS::Region}:${AWS::AccountId}:${WebSocketApiId.ApiId}/default/$connect",
        )

    def test_none_auth_no_id(self):
        kwargs = self.kwargs.copy()
        kwargs["auth_config"] = {"AuthType": "NONE"}
        WebSocketApiGenerator(**kwargs)._construct_websocket_api()
        route, _, _, auth = WebSocketApiGenerator(**kwargs)._construct_route_infr(
            "$connect", kwargs["routes"]["$connect"]
        )
        self.assertEqual(route.AuthorizationType, "NONE")
        self.assertIsNone(route.AuthorizerId)
        self.assertIsNone(auth)

    def test_none_auth_has_id(self):
        kwargs = self.kwargs.copy()
        kwargs["auth_config"] = {
            "AuthArn": {"Fn::GetAtt": ["AuthFunc", "Arn"]},
        }
        with pytest.raises(InvalidResourceException) as e:
            WebSocketApiGenerator(**kwargs)._construct_route_infr("$connect", kwargs["routes"]["$connect"])
        self.assertEqual(
            e.value.message,
            "Resource with id [WebSocketApiId] is invalid. "
            + "AuthType must be specified for additional auth configurations.",
        )

    def test_auth_id_no_type(self):
        kwargs = self.kwargs.copy()
        kwargs["auth_config"] = {"AuthArn": {"Fn::GetAtt": ["saucefunction", "Arn"]}}
        with pytest.raises(InvalidResourceException) as e:
            WebSocketApiGenerator(**kwargs)._construct_route_infr("$connect", kwargs["routes"]["$connect"])
        self.assertEqual(
            e.value.message,
            "Resource with id [WebSocketApiId] is invalid. "
            + "AuthType must be specified for additional auth configurations.",
        )

    def test_auth_no_connect(self):
        kwargs = self.kwargs.copy()
        kwargs["auth_config"] = {"AuthType": "CUSTOM", "AuthArn": {"Fn::GetAtt": ["AuthFunc", "Arn"]}}
        kwargs["routes"] = {"$default": {"FunctionArn": {"Fn::GetAtt": ["DefaultFunction", "Arn"]}}}
        with pytest.raises(InvalidResourceException) as e:
            WebSocketApiGenerator(**kwargs)._construct_websocket_api()
        self.assertEqual(
            e.value.message,
            "Resource with id [WebSocketApiId] is invalid. "
            + "Authorization is only available if there is a $connect route.",
        )

    def test_none_auth_no_connect(self):
        kwargs = self.kwargs.copy()
        kwargs["auth_config"] = {"AuthType": "NONE"}
        WebSocketApiGenerator(**kwargs)._construct_websocket_api()
        route, _, _, auth = WebSocketApiGenerator(**kwargs)._construct_route_infr(
            "$connect", kwargs["routes"]["$connect"]
        )
        self.assertEqual(route.AuthorizationType, "NONE")
        self.assertIsNone(route.AuthorizerId)
        self.assertIsNone(auth)

    def test_invalid_auth_type(self):
        kwargs = self.kwargs.copy()
        kwargs["auth_config"] = {"AuthType": "nonsense", "AuthArn": {"Fn::GetAtt": ["AuthFunction", "Arn"]}}

        with pytest.raises(InvalidResourceException) as e:
            WebSocketApiGenerator(**kwargs)._construct_route_infr("$connect", kwargs["routes"]["$connect"])
        self.assertEqual(
            e.value.message,
            "Resource with id [WebSocketApiId] is invalid. " + "AuthType is not one of AWS_IAM, CUSTOM or NONE.",
        )

    def test_auth_set(self):
        kwargs = self.kwargs.copy()
        kwargs["auth_config"] = {"AuthType": "CUSTOM", "AuthArn": {"Fn::GetAtt": ["AuthFunction", "Arn"]}}
        kwargs["routes"] = {
            "$connect": {"FunctionArn": {"Fn::GetAtt": ["ConnectFunction", "Arn"]}},
            "$disconnect": {"FunctionArn": {"Fn::GetAtt": ["AuthFunction", "Arn"]}},
        }
        WebSocketApiGenerator(**kwargs)._construct_websocket_api()
        croute, _, _, cauth = WebSocketApiGenerator(**kwargs)._construct_route_infr(
            "$connect", kwargs["routes"]["$connect"]
        )
        self.assertEqual(croute.AuthorizationType, "CUSTOM")
        self.assertEqual(croute.AuthorizerId, {"Ref": cauth.logical_id})
        self.assertIsNotNone(cauth)
        droute, _, _, dauth = WebSocketApiGenerator(**kwargs)._construct_route_infr(
            "$disconnect", kwargs["routes"]["$disconnect"]
        )
        self.assertIsNone(droute.AuthorizationType)
        self.assertIsNone(droute.AuthorizerId)
        self.assertIsNone(dauth)

    def test_custom_auth_params(self):
        kwargs = self.kwargs.copy()
        kwargs["auth_config"] = {
            "AuthArn": {"Fn::GetAtt": ["AuthFunc", "Arn"]},
            "AuthType": "CUSTOM",
            "InvokeRole": {"Fn::GetAtt": ["AuthInvokeRole", "Arn"]},
            "IdentitySource": ["id_source"],
            "Name": "Auth",
        }

    def test_route_no_function_name(self):
        kwargs = self.kwargs.copy()
        kwargs["routes"] = {"$connect": {}}
        WebSocketApiGenerator(**kwargs)._construct_websocket_api()
        with pytest.raises(InvalidResourceException) as e:
            WebSocketApiGenerator(**kwargs)._construct_route_infr("$connect", kwargs["routes"]["$connect"])
        self.assertEqual(
            e.value.message, "Resource with id [WebSocketApiId] is invalid. Route must have associated function."
        )

    def test_invalid_route_name(self):
        kwargs = self.kwargs.copy()
        kwargs["routes"] = {"$sauce": {"FunctionArn": {"Fn::GetAtt": ["SauceFunction", "Arn"]}}}
        WebSocketApiGenerator(**kwargs)._construct_websocket_api()
        with pytest.raises(InvalidResourceException) as e:
            WebSocketApiGenerator(**kwargs)._construct_route_infr("$sauce", kwargs["routes"]["$sauce"])
        self.assertEqual(
            e.value.message,
            "Resource with id [WebSocketApiId] is invalid. "
            + "Route key '$sauce' must be alphanumeric. Only $connect, $disconnect, and $default special routes are supported.",
        )

    def test_no_stage_name(self):
        kwargs = self.kwargs.copy()
        WebSocketApiGenerator(**kwargs)._construct_websocket_api()
        stage = WebSocketApiGenerator(**kwargs)._construct_stage()
        self.assertEqual(stage.StageName, "default")

    def test_set_stage_name(self):
        kwargs = self.kwargs.copy()
        kwargs["stage_name"] = "prod"
        WebSocketApiGenerator(**kwargs)._construct_websocket_api()
        stage = WebSocketApiGenerator(**kwargs)._construct_stage()
        self.assertEqual(stage.StageName, "prod")

    def test_invalid_stage_name(self):
        kwargs = self.kwargs.copy()
        kwargs["stage_name"] = "$default"
        WebSocketApiGenerator(**kwargs)._construct_websocket_api()
        with pytest.raises(InvalidResourceException) as e:
            WebSocketApiGenerator(**kwargs)._construct_stage()
        self.assertEqual(
            e.value.message,
            "Resource with id [WebSocketApiId] is invalid. " + "Stages cannot be named $default for WebSocket APIs.",
        )

    def test_ipv4(self):
        kwargs = self.kwargs.copy()
        kwargs["ip_address_type"] = "ipv4"
        websocket_api = WebSocketApiGenerator(**kwargs)._construct_websocket_api()
        self.assertEqual(websocket_api.IpAddressType, "ipv4")

    def test_dualstack(self):
        kwargs = self.kwargs.copy()
        kwargs["ip_address_type"] = "dualstack"
        websocket_api = WebSocketApiGenerator(**kwargs)._construct_websocket_api()
        self.assertEqual(websocket_api.IpAddressType, "dualstack")

    def test_invalid_ip(self):
        kwargs = self.kwargs.copy()
        kwargs["ip_address_type"] = "nonsense"
        with pytest.raises(InvalidResourceException) as e:
            WebSocketApiGenerator(**kwargs)._construct_websocket_api()
        self.assertEqual(
            e.value.message,
            "Resource with id [WebSocketApiId] is invalid. " + "IpAddressType must be 'ipv4' or 'dualstack'.",
        )
