# AWS::Serverless::S3 Event Code Example
This example shows you how to get events of S3 bucket. When you upload an image in the source bucket it will resize that image and save in the destination bucket.
###### Note
Don't forget to chnage S3 bucket name, source bucket prefix.

## Package and deploy template
#### Build
Run the following command to build binary of your code
```
GOOS=linux go build -o main
```
#### Package
To package your application run the following command
```
sam package --template-file template.yaml --output-template-file serverless-output.yaml --s3-bucket <YOUR_S3_BUCKET>
```
It will validate the template, zip you applicaiton, upload to your S3 bucket and generates the output template. Replace the `<YOUR_S3_BUCKET>` with your bucket name.
#### Deploy
Run the following command replacing  `<BUCKET_PREFIX>` with your desire prefix name to deploye your application
```
sam deploy --template-file serverless-output.yaml --stack-name image-resizer --capabilities CAPABILITY_IAM --parameter-overrides BucketNamePrefix=<BUCKET_PREFIX>
```
It will create necessary resources and link them according to the template using cloudformation.

## Test
Upload an image in `JPEG` format to the `SourceBucket` defined in the template and verify the same image with smaller size in `DestBucket`.

