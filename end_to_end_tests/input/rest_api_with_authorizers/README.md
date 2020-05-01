# RestApi with Auth Example

Example SAM template with Cognito, Lambda token and Lambda request authorization for Rest Apis

## Running the example

```bash
$ sam deploy \
    --template-file template.yaml \
    --stack-name my-stack-name \
    --capabilities CAPABILITY_IAM
```
