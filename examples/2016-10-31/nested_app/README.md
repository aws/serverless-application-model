## Nested App Example

This app uses the [twitter event source app](https://serverlessrepo.aws.amazon.com/applications/arn:aws:serverlessrepo:us-east-1:077246666028:applications~aws-serverless-twitter-event-source) as a nested app and logs the tweets received from the nested app.

All you need to do is supply the desired parameters for this app and deploy. SAM will create a nested stack for any nested app inside of your template with all of the parameters that are passed to it. 

## Installation Instructions
 Please refer to the Installation Steps section of the [twitter-event-source application](https://serverlessrepo.aws.amazon.com/applications/arn:aws:serverlessrepo:us-east-1:077246666028:applications~aws-serverless-twitter-event-source) for detailed information regarding how to obtain and use the tokens and secrets for this application.