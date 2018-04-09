# Overview

SAM is called by the CloudFormation Service. CloudFormation recognises the `Transform: AWS::Serverless-2016-10-31` header and invokes the SAM translator. This will then take your SAM template and expand it
into a full fledged CloudFormation Template. The CloudFormation Template that is produced from SAM is the template that is executed by CloudFormation to create/update/delete AWS resources.

The entry point for SAM starts in the Translator class [here](https://github.com/awslabs/serverless-application-model/blob/develop/samtranslator/translator/translator.py#L29), where SAM iterates through the
template and acts on `AWS::Serverless::*` Type Resources.

# Design decisions

Document design decisions here.

## CloudWatchLogs Event Source

### LogGroupName

For now we have decided `LogGroupName` should be a required property for simplicity. A future enhancement could make this optional and create a new CloudWatch Log Group when not provided. Users could `Ref` the resource if we exposed/documented the resource naming convention.

### FilterPattern

Decided `FilterPattern` should be a required property so as not to provide a footgun to users. If this were to default to `""`, noisy logs could invoke hundreds/thousands of Lambda functions in short periods of time.