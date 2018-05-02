#/bin/bash

# Test invocation using httpie (http) in place of curl for syntax simplicity
#
# Args: $1: API GW path
#       $2 Dynamodb table name
#       $3 json payload data file

# Note, Dynamodb table must already exist.

http POST $1 TableName=$2 Item:=@$3

# eg:
# http https://k0dagiifr0.execute-api.us-west-2.amazonaws.com/Prod/MyResource TableName=http-ep-p3 Item:=@test-payload.json

# Sample output:

HTTP/1.1 200 OK
Connection: keep-alive
Content-Length: 414
Content-Type: application/json
Date: Wed, 02 May 2018 20:48:59 GMT
Via: 1.1 f97210398b4cfef9ad2de33146167726.cloudfront.net (CloudFront)
X-Amz-Cf-Id: dFRjdDXHhBm2LC6hEBuD8rAbNsf0gb7QPZ3VePYgPe9CfymHSz70vg==
X-Amzn-Trace-Id: Root=1-5aea243b-5405221a6a87ac4dd1403b05
X-Cache: Miss from cloudfront
x-amz-apigw-id: GRqZOGDvPHcFcQQ=
x-amzn-RequestId: 3cdc7fdd-4e4a-11e8-b075-97a0b9051b0f

{
    "ResponseMetadata": {
        "HTTPHeaders": {
            "connection": "keep-alive",
            "content-length": "2",
            "content-type": "application/x-amz-json-1.0",
            "date": "Wed, 02 May 2018 20:48:59 GMT",
            "server": "Server",
            "x-amz-crc32": "2745614147",
            "x-amzn-requestid": "I4V5B6P7ERJMEGMMDH5O939BNVVV4KQNSO5AEMVJF66Q9ASUAAJG"
        },
        "HTTPStatusCode": 200,
        "RequestId": "I4V5B6P7ERJMEGMMDH5O939BNVVV4KQNSO5AEMVJF66Q9ASUAAJG",
        "RetryAttempts": 0
    }
}

