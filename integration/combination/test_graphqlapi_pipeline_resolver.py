import json
from unittest.case import skipIf

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
class TestGraphQLApiPipelineResolver(BaseTest):
    def test_api(self):
        file_name = "combination/graphqlapi_pipeline_resolver"
        self.create_and_verify_stack(file_name)

        outputs = self.get_stack_outputs()

        author = "AUTHORNAME"
        title = "Our first post!"
        content = "This is our first post."

        query = f"""
            mutation addPost {{
              addPost(
                author: "{author}"
                title: "{title}"
                content: "{content}"
              ) {{
                id
                author
                title
                content
                ups
                downs
                version
              }}
            }}
        """

        url = outputs["SuperCoolAPI"]
        api_key = outputs["MyApiKey"]

        response = execute_and_verify_appsync_query(url, api_key, query)

        add_post = response["data"]["addPost"]

        self.assertEqual(add_post["author"], author)
        self.assertEqual(add_post["title"], title)
        self.assertEqual(add_post["content"], content)
        self.assertEqual(add_post["ups"], 1)
        self.assertEqual(add_post["downs"], 0)
        self.assertEqual(add_post["version"], 1)

        post_id = add_post["id"]
        query = f"""
            query getPost {{
              getPost(id:"{post_id}") {{
                id
                author
                title
                content
                ups
                downs
                version
              }}
            }}
        """

        response = execute_and_verify_appsync_query(url, api_key, query)

        get_post = response["data"]["getPost"]

        self.assertEqual(get_post["author"], author)
        self.assertEqual(get_post["title"], title)
        self.assertEqual(get_post["content"], content)
        self.assertEqual(get_post["ups"], 1)
        self.assertEqual(get_post["downs"], 0)
        self.assertEqual(get_post["version"], 1)
        self.assertEqual(get_post["id"], post_id)
