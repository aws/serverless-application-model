# Api Resource Policy Event Source Example

Example SAM template for adding Custom Resource Policy to Api.

## Running the example

```bash
# Replace YOUR_S3_ARTIFACTS_BUCKET
aws cloudformation package --template-file template.yaml --output-template-file cfn-transformed-template.yaml --s3-bucket YOUR_S3_ARTIFACTS_BUCKET
aws cloudformation deploy --template-file ./cfn-transformed-template.yaml --stack-name example-resource-policy --capabilities CAPABILITY_IAM
```
