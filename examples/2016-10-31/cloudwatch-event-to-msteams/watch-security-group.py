# To test locally: (make sure to modifify the "groupId" with a real security group, add your webhook into vars.json)
# sam local invoke -e events/event_iam.json WatchSecurityGroupFunction -n vars.json

import boto3
import json
import os
from botocore.vendored import requests

# Boto3 for security group: https://boto3.readthedocs.io/en/latest/reference/services/ec2.html#EC2.SecurityGroup
ec2 = boto3.resource('ec2')

# Environment Variable for Lambda
TEAM_WEBHOOK = os.environ['TEAM_WEBHOOK']

def get_security_group(event):

    print("--------- Event Received ---------")
    print(json.dumps(event))
    print("--------- End of Event ---------")

    # Read event from something change security groups in console.
    if len(event["detail"]["requestParameters"]["ipPermissions"]) > 0:
        for rule in event["detail"]["requestParameters"]["ipPermissions"]["items"]:

            # Use protocol as port if fromPort is empty
            from_port = rule.get("fromPort", rule["ipProtocol"])

            # Check for multi ip address added as source
            if len(rule["ipRanges"]) > 0:

                for i in rule["ipRanges"]["items"]:

                    # Check if CIDR has been entered or Another Security Group
                    try:
                        cidr_address = i["cidrIp"]
                    except KeyError:
                        cidr_address = i["groupId"]

                    # Get description of individual rule
                    description = i.get("description", "")

                    # Send Message
                    lookup_security_group(event, from_port, cidr_address, description)

            # Check for multi security groups added as source
            if len(rule["groups"]) > 0:

                for i in rule["groups"]["items"]:

                    # Check if CIDR has been entered or Another Security Group
                    try:
                        cidr_address = i["cidrIp"]
                    except KeyError:
                        cidr_address = i["groupId"]

                    # Get description of individual rule
                    description = i.get("description", "")

                    # Send Message
                    lookup_security_group(event, from_port, cidr_address, description)

    # Event isn't coming from Console, use API event                
    else:
       
        # Check if CIDR has been entered or Another Security Group
        try:
            cidr_address = event["detail"]["requestParameters"]["cidrIp"]
        except KeyError:
            cidr_address = event["detail"]["requestParameters"]["groupId"]

        # Get Description and Port
        description = event["detail"]["requestParameters"].get("description", "")
        from_port = event["detail"]["requestParameters"].get("from_port", -1)

        # Send Message
        lookup_security_group(event, from_port, cidr_address, description)


def lookup_security_group(event, source_port, cidr_address, description):

    # Look up security group attributes from group_id
    try:
        lookup_sg_id = event["detail"]["requestParameters"]["groupId"]
        lookup_sg = ec2.SecurityGroup(lookup_sg_id)
        lookup_sg_name = lookup_sg.group_name
        lookup_sg_description = lookup_sg.description
        
        # Get Account and User Details
        event_type = event["detail"]["eventName"]
        aws_account = event["account"]
        user_id = event["detail"]["userIdentity"]["arn"]
        full_username = user_id.split(':')[-1]

        # Colors for Microsoft Teams: Blue = Add, Red = Remove
        if event_type == "AuthorizeSecurityGroupIngress":
            message_color = "0072C6"
        else:
            message_color = "FF0000"

        # Send Teams Message
        create_json_message(TEAM_WEBHOOK, full_username, lookup_sg_id, lookup_sg_name, lookup_sg_description, aws_account, source_port, cidr_address, description, event_type, message_color)

    except Exception as error:
        print("Error getting Security Group from Event:")
        print(f"{error}")
    

def create_json_message(TEAM_WEBHOOK, full_username, lookup_sg_id, lookup_sg_name, lookup_sg_description, aws_account, source_port, cidr_address, description, event_type, message_color):
    
    body = {
        "@context": "http://schema.org/extensions",
        "@type": "MessageCard",
        "themeColor": f"{message_color}",
        "title": "Security Group Watcher",
        "text": " ",
        "sections": [
            {
                "activityText": f"Security group **{lookup_sg_id}** has been modified and trigger this alert"
            },
            {
                "facts": [
                    {
                        "name": "Action",
                        "value": f"{event_type}"
                    },
                    {
                        "name": "User",
                        "value": f"{full_username}"
                    },
                    {
                        "name": "Account",
                        "value": f"{aws_account}"
                    },
                    {
                        "name": "SourcePort",
                        "value": f"{source_port}"
                    },
                    {
                        "name": "Destination",
                        "value": f"{cidr_address}"
                    },
                    {
                        "name": "SecurityGroupId",
                        "value": f"{lookup_sg_id}"
                    },
                    {
                        "name": "Description",
                        "value": f"{lookup_sg_description}"
                    },
                    {
                        "name": "Rule Description",
                        "value": f"{description}"
                    }

                ]
            }
        ]
    }
    
    response = requests.post(TEAM_WEBHOOK, data=json.dumps(body))
    print(f'response from Teams: {response}')

    return response
    

def lambda_handler(event, context):
    get_security_group(event)
