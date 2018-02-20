#Kinesis Aggregation/Deaggregation Libraries for Python
#
#Copyright 2014, Amazon.com, Inc. or its affiliates. All Rights Reserved. 
#
#Licensed under the Amazon Software License (the "License").
#You may not use this file except in compliance with the License.
#A copy of the License is located at
#
# http://aws.amazon.com/asl/
#
#or in the "license" file accompanying this file. This file is distributed
#on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
#express or implied. See the License for the specific language governing
#permissions and limitations under the License.

import md5

#Message aggregation protocol-specific constants
#(https://github.com/awslabs/amazon-kinesis-producer/blob/master/aggregation-format.md)
MAGIC = '\xf3\x89\x9a\xc2'
DIGEST_SIZE = md5.digest_size

#Kinesis Limits
#(https://docs.aws.amazon.com/kinesis/latest/APIReference/API_PutRecord.html)
MAX_BYTES_PER_RECORD = 1024*1024 # 1 MB
