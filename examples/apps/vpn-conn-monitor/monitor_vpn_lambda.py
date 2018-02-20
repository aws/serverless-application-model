'''
To use this blueprint, your function's role must have permissions
to call ec2:DescribeRegions and ec2:DescribeVpnConnections.
For these permissions, you must specify "Resource": "*".

Example:
{
    "Version": "2012-10-17",
    "Statement": [{
        "Sid": "Stmt1443036478000",
        "Effect": "Allow",
        "Action": [
            "ec2:DescribeRegions",
            "ec2:DescribeVpnConnections"
        ],
        "Resource": "*"
    }]
}
'''

from __future__ import print_function

import boto3

print('Loading function')
cw = boto3.client('cloudwatch')


def put_cloudwatch_metric(metric_name, value, vgw, cgw, region):
    cw.put_metric_data(
        Namespace='VPNStatus',
        MetricData=[{
            'MetricName': metric_name,
            'Value': value,
            'Unit': 'Count',
            'Dimensions': [
                {
                    'Name': 'VGW',
                    'Value': vgw
                },
                {
                    'Name': 'CGW',
                    'Value': cgw
                },
                {
                    'Name': 'Region',
                    'Value': region
                }
            ]
        }]
    )


def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    aws_regions = ec2.describe_regions()['Regions']
    num_connections = 0
    for region in aws_regions:
        try:
            ec2 = boto3.client('ec2', region_name=region['RegionName'])
            vpns = ec2.describe_vpn_connections()['VpnConnections']
            for vpn in vpns:
                if vpn['State'] == 'available':
                    num_connections += 1
                    active_tunnels = 0
                    if vpn['VgwTelemetry'][0]['Status'] == 'UP':
                        active_tunnels += 1
                    if vpn['VgwTelemetry'][1]['Status'] == 'UP':
                        active_tunnels += 1
                    put_cloudwatch_metric(vpn['VpnConnectionId'],
                                          active_tunnels,
                                          vpn['VpnGatewayId'],
                                          vpn['CustomerGatewayId'],
                                          region['RegionName'])
        except Exception as e:
            print("Exception: " + str(e))
            continue
    return num_connections
