AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Description: Example demonstrating API EndpointConfiguration

Parameters:
  EndpointConfigType:
    Type: String
    Default: PRIVATE
  VpcEndpointId:
    Type: String

Resources:
  MyApi:
    Type: AWS::Serverless::Api
    Properties:
      StageName: Prod
      EndpointConfiguration:
        Type: !Ref EndpointConfigType
        VPCEndpointIds:
          - !Ref VpcEndpointId