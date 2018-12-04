# AWS::Serverless::LayerVersion Library Code Example

This example shows you how to download and publish an application that bundles its Function dependencies into an AWS::Serverless::LayerVersion resource. The function resizes an image that is uploaded to the source bucket and saves the resized image to the destination bucket.

## Running the example

Below are instructions on how to deploy and use this example.

### Download dependencies:

We are using the [`sam build`](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/sam-cli-command-reference-sam-build.html) command to download the correct versions of all of our python dependencies. At the time of creating this example, `sam build` does not support building layers, but that may change in the future. We can still use it to get our dependencies and then separate them out into separate directories for our Lamda Function and LayerVersion.
```
# Use `sam build` to get dependencies
sam build -b ./build --use-container -m ./requirements.txt

# Move dependencies into our layer directory
mv ./build/ImageProcessorFunction/PIL ./layer/
mv ./build/ImageProcessorFunction/Pillow* ./layer/

# Remove the build directory and its contents
rm -rf ./build
```

### Package and deploy template:

**Package:**
```
# Run the following command, replacing s3_bucket with an existing bucket name
aws cloudformation package --template-file template.yaml --s3-bucket <s3_bucket> --output-template-file packaged.yaml
```


**Deploy:**
```
# Run the following command, replacing bucket_prefix with the desired prefix name for the s3 buckets this example will create
aws cloudformation deploy --template-file ./packaged.yaml --stack-name layers-example-stack --capabilities CAPABILITY_IAM --parameter-overrides BucketNamePrefix=<bucket_prefix>
```

### Test example:

Upload a picture to the `SourceBucket` defined in the template and verify that it creates a smaller version of the same picture in the `DestBucket` created in the same stack.

Code taken from https://docs.aws.amazon.com/lambda/latest/dg/with-s3-example-deployment-pkg.html#with-s3-example-deployment-pkg-python

