
# Lambda function with VPC Access

This example shows you how to create a Lambda function in a VPC with the appropriate permissions using SAM. It primarily aims to demonstrate Cloudformation parameters as well as a simplified configuration made possible with SAM Policies, therefore it'll not utilise API Gateway or any other Event source and as a result only the account owner can invoke it.

It is important to remember that VPC-enabled functions need NAT in order to access any public IP address (if needed) and therefore should be in a private subnet with VPC NAT Gateway and not VPC Internet Gateway.

## Running the example

Deploy the example into your account:

```bash
# Replace YOUR_S3_ARTIFACTS_BUCKET
aws cloudformation package --template-file template.yaml --output-template-file template.packaged.yaml --s3-bucket YOUR_S3_ARTIFACTS_BUCKET

# Replace YOUR_SECURITY_GROUP_1 and YOUR_SECURITY_GROUP_2
# Replace YOUR_SUBNET_1 and YOUR_SUBNET_2
## They must belong to the same VPC
aws cloudformation deploy \
    --template-file template.packaged.yaml \
    --stack-name sam-example-hello-vpc \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides SecurityGroupIds="YOUR_SECURITY_GROUP_1,YOUR_SECURITY_GROUP_2" VpcSubnetIds="YOUR_SUBNET_1,YOUR_SUBNET_2"
```

Invoke the Lambda function using Lambda Invoke API via AWS CLI:

```bash
hello_function_vpc=$(aws cloudformation describe-stacks \
    --stack-name hello-vpc-sample \
    --query 'Stacks[].Outputs[?OutputKey==`HelloWorldFunction`].OutputValue' \
    --output text)

aws lambda invoke --function-name $hello_function_vpc result.txt
```

If successful, you should see a similar output and the function return under ``result.txt``:

```javascript
{
    "StatusCode": 200,
    "ExecutedVersion": "$LATEST"
}
```
```bash
cat result.txt

"Hello world!"
```


## Additional resources

- https://docs.aws.amazon.com/lambda/latest/dg/vpc.html
- https://aws.amazon.com/premiumsupport/knowledge-center/nat-gateway-vpc-private-subnet/
