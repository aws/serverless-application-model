#/bin/bash -e

# Test invocation using httpie (http) in place of curl for syntax simplicity
#
# Args: $1: API GW path
#       $2 json payload data file
#
# eg: ./test.sh https://vxldx8ck9i.execute-api.us-west-2.amazonaws.com/Prod/MyResource ./test-payload.json

set -x

# Write one item

http POST $1 Item:=@$2

# Read all back

http GET $1 

