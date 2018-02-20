'use strict';

/**
 * A sample Lambda function that takes an AWS CloudFormation stack name
 * and returns the outputs from that stack. Make sure to include permissions
 * for `cloudformation:DescribeStacks` in your execution role!
 *
 * See http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/walkthrough-custom-resources-lambda-cross-stack-ref.html
 * for documentation on how to use this blueprint.
 */
const https = require('https');
const url = require('url');

// Sends a response to the pre-signed S3 URL
function sendResponse(event, callback, logStreamName, responseStatus, responseData) {
    const responseBody = JSON.stringify({
        Status: responseStatus,
        Reason: `See the details in CloudWatch Log Stream: ${logStreamName}`,
        PhysicalResourceId: logStreamName,
        StackId: event.StackId,
        RequestId: event.RequestId,
        LogicalResourceId: event.LogicalResourceId,
        Data: responseData,
    });

    console.log('RESPONSE BODY:\n', responseBody);

    const parsedUrl = url.parse(event.ResponseURL);
    const options = {
        hostname: parsedUrl.hostname,
        port: 443,
        path: parsedUrl.path,
        method: 'PUT',
        headers: {
            'Content-Type': '',
            'Content-Length': responseBody.length,
        },
    };

    const req = https.request(options, (res) => {
        console.log('STATUS:', res.statusCode);
        console.log('HEADERS:', JSON.stringify(res.headers));
        callback(null, 'Successfully sent stack response!');
    });

    req.on('error', (err) => {
        console.log('sendResponse Error:\n', err);
        callback(err);
    });

    req.write(responseBody);
    req.end();
}

exports.handler = (event, context, callback) => {
    //console.log('Received event:', JSON.stringify(event, null, 2));

    if (event.RequestType === 'Delete') {
        sendResponse(event, callback, context.logStreamName, 'SUCCESS');
        return;
    }

    const stackName = event.ResourceProperties.StackName;
    let responseStatus = 'FAILED';
    let responseData = {};

    // Verifies that a stack name was passed
    if (stackName) {
        const aws = require('aws-sdk');

        const cfn = new aws.CloudFormation();
        cfn.describeStacks({ StackName: stackName }, (err, data) => {
            if (err) {
                responseData = { Error: 'DescribeStacks call failed' };
                console.log(`${responseData.Error}:\n`, err);
            } else {
                // Populates the return data with the outputs from the specified stack
                responseStatus = 'SUCCESS';
                data.Stacks[0].Outputs.forEach((output) => responseData[output.OutputKey] = output.OutputValue);
            }
            sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
        });
    } else {
        responseData = { Error: 'Stack name not specified' };
        console.log(responseData.Error);
        sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
    }
};
