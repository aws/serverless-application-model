do_not_verify = {
    # type_after_transform: type_before_transform
    'AWS::Lambda::Function': 'AWS::Serverless::Function',
    'AWS::Lambda::LayerVersion': 'AWS::Serverless::LayerVersion',
    'AWS::ApiGateway::RestApi': 'AWS::Serverless::Api',
    'AWS::S3::Bucket': 'AWS::S3::Bucket',
    'AWS::SNS::Topic': 'AWS::SNS::Topic',
    'AWS::DynamoDB::Table': 'AWS::Serverless::SimpleTable',
    'AWS::CloudFormation::Stack': 'AWS::Serverless::Application'
}


def verify_unique_logical_id(resource, existing_resources):
    # new resource logicalid exists in the template before transform
    if resource.logical_id is not None and resource.logical_id in existing_resources:
        # new resource logicalid is in  the do_not_resolve list
        if resource.resource_type not in do_not_verify or existing_resources[resource.logical_id]['Type'] \
                not in do_not_verify[resource.resource_type]:
            return False
    return True
