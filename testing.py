import boto3
import requests
import pprint
import json
import datetime
import hmac
import hashlib
from requests_aws4auth import AWS4Auth

appsync = boto3.client('appsync')

query = '''
mutation addPost {
  addPost(
    author: "AUTHORNAME"
    title: "Our first post!"
    content: "This is our first post."
    url: "https://aws.amazon.com/appsync/"
  ) {
    id
    author
    title
    content
    url
    ups
    downs
    version
  }
}
'''
response = appsync.list_graphql_apis()

pprint.pprint(response)

url = response['graphqlApis'][0]['uris']['GRAPHQL']
api_id = response['graphqlApis'][0]['apiId']

response = appsync.list_api_keys(apiId=api_id)
api_key = response['apiKeys'][0]['id']

# Define the AWS region and service for the IAM credential
region = 'us-west-2'
service = 'appsync'

# Define the AWS IAM access key, secret key, and session token

# Define the HTTP headers
headers = {
    'Content-Type': 'application/json',
    'x-api-key': api_key,
}

payload = {"query": query}

# Send the GraphQL query to AWS AppSync using the requests module
response = requests.post(url, json=payload, headers=headers)

# Get the response data as a JSON object
data = json.loads(response.text)

# Print the response data
pprint.pprint(data)


