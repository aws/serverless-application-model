import json
from unittest.case import skipIf

import pytest
import requests

from integration.config.service_names import APP_SYNC
from integration.helpers.base_test import BaseTest
from integration.helpers.resource import current_region_does_not_support


def execute_and_verify_appsync_query(url, api_key, query):
    """
    Executes a query to an AppSync GraphQLApi.

    Also checks that the response is 200 and does not contain errors before returning.
    """
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
    }
    payload = {"query": query}

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    if "errors" in data:
        raise Exception(json.dumps(data["errors"]))

    return data


@skipIf(current_region_does_not_support([APP_SYNC]), "AppSync is not supported in this testing region")
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
class TestGraphQLApiConfiguration(BaseTest):
    def test_api(self):
        file_name = "single/graphqlapi-configuration"
        self.create_and_verify_stack(file_name)

        outputs = self.get_stack_outputs()

        url = outputs["SuperCoolAPI"]
        api_key = outputs["MyApiKey"]

        introspection_disable_api_url = outputs["IntrospectionDisableSuperCoolAPI"]
        introspection_disable_api_key = outputs["IntrospectionDisableSuperCoolAPIMyApiKey"]

        book_name = "GoodBook"
        query = f"""
            query MyQuery {{
              getBook(
                bookName: "{book_name}"
              ) {{
                id
                bookName
              }}
            }}
        """

        response = execute_and_verify_appsync_query(url, api_key, query)
        self.assertEqual(response["data"]["getBook"]["bookName"], book_name)

        introspection_disable_query_response = execute_and_verify_appsync_query(
            introspection_disable_api_url, introspection_disable_api_key, query
        )
        self.assertEqual(introspection_disable_query_response["data"]["getBook"]["bookName"], book_name)

        query_introsepction = """
            query myQuery {
              __schema { 
                types {
                  name
                }
               }
            }
        """

        introspection_query_response = execute_and_verify_appsync_query(url, api_key, query_introsepction)
        self.assertIsNotNone(introspection_query_response["data"]["__schema"])

        # sending introspection query and expecting error as introspection is DISABLED for this API using template file
        with self.assertRaises(Exception):
            execute_and_verify_appsync_query(
                introspection_disable_api_url, introspection_disable_api_key, query_introsepction
            )
