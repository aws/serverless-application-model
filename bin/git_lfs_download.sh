#!/bin/bash
set -eux

# Here is the reference I found on how to download Git LFS file 
# https://gist.github.com/fkraeutli/66fa741d9a8c2a6a238a01d17ed0edc5#retrieving-lfs-files

# Check if a URL parameter is provided
if [ $# -eq 0 ]; then
    echo "Script Usage: $0 <URL>"
    exit 1
fi

# Get the URL from the first command-line parameter
url="$1"

# Fetch the metadata from the URL
response=$(curl -s "$url")

# Extract oid and size from the metadata
oid=$(echo "$response" | grep '^oid' | cut -d: -f2)
size=$(echo "$response" | grep 'size' | cut -d ' ' -f 2)

# String interpolation to create the request JSON content
request_json=$(jq -nc --arg oid "$oid" --argjson size "$size" '{"operation":"download","objects":[{"oid":$oid,"size":$size}],"transfers":["basic"]}')

# Send a POST request to Git LFS with the retrieved metadata JSON content
response=$(curl \
  -X POST \
  -H "Accept: application/vnd.git-lfs+json" \
  -H "Content-type: application/json" \
  -d "$request_json" \
  https://github.com/cdklabs/awscdk-service-spec.git/info/lfs/objects/batch)

# The above command should return a JSON object that tells you where the file is stored
href=$(echo "$response" | jq -r '.objects[0].actions.download.href')

# Download the file and store it in .tmp/cfn-docs.json
curl -o .tmp/cfn-docs.json $href