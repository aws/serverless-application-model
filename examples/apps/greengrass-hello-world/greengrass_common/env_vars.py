#
# Copyright 2010-2016 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#

import os

AUTH_TOKEN = os.getenv('AWS_CONTAINER_AUTHORIZATION_TOKEN')
MY_FUNCTION_ARN = os.getenv('MY_FUNCTION_ARN')
SHADOW_FUNCTION_ARN = os.getenv('SHADOW_FUNCTION_ARN')
ROUTER_FUNCTION_ARN = os.getenv('ROUTER_FUNCTION_ARN')
