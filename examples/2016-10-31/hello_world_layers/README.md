# Hello world with Layers

You can configure your Lambda function to pull in additional code and content in the form of layers. A layer is a ZIP archive that contains libraries, a [custom runtime](https://docs.aws.amazon.com/lambda/latest/dg/runtimes-custom.html), or other dependencies. With layers, you can use libraries in your function without needing to include them in your deployment package.

Layers let you keep your deployment package small, which makes development easier. You can avoid errors that can occur when you install and package dependencies with your function code. For Node.js, Python, and Ruby functions, you can [develop your function code in the Lambda console](https://docs.aws.amazon.com/lambda/latest/dg/code-editor.html) as long as you keep your deployment package under 3 MB.

>**Note**

>A function can use up to 5 layers at a time. The total unzipped size of the function and all layers can't exceed the unzipped deployment package size limit of 250 MB. For more information, see [AWS Lambda Limits](https://docs.aws.amazon.com/lambda/latest/dg/limits.html).

You can create layers, or use layers published by AWS and other AWS customers. Layers support [resource-based policies](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html#configuration-layers-permissions) for granting permission specific AWS accounts, [AWS Organizations](https://docs.aws.amazon.com/organizations/latest/userguide/), or all accounts.

Layers are extracted to the /opt directory in the function execution environment. Each runtime looks for libraries in a different location under /opt, depending on the language. Structure your layer so that function code can access libraries without additional configuration.

You can also use AWS Serverless Application Model (AWS SAM) to manage layers and your function's layer configuration. For instructions, see [Declaring Serverless Resources](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-sam-template.html) in the AWS Serverless Application Model Developer Guide.

-- 
For more information, please access the [AWS Lambda Layers documentation](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html). 