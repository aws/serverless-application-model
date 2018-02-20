'use strict';

/**
 * A sample Lambda function that looks up the latest AMI ID for a given
 * region and architecture. Make sure to include permissions for
 * `ec2:DescribeImages` in your execution role!
 *
 * See http://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/walkthrough-custom-resources-lambda-lookup-amiids.html
 * for documentation on how to use this blueprint.
 */
const aws = require('aws-sdk');
const https = require('https');
const url = require('url');

// Map instance architectures to an AMI name pattern
const archToAMINamePattern = {
    PV64: 'amzn-ami-pv*.x86_64-ebs',
    HVM64: 'amzn-ami-hvm*.x86_64-gp2',
    HVMG2: 'amzn-ami-graphics-hvm-*x86_64-ebs*',
};

// Check if the image is a beta or RC image (the Lambda function won't return any of these images)
const isBeta = (imageName) => imageName.toLowerCase().includes('beta') || imageName.toLowerCase().includes('.rc');

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

    let responseStatus = 'FAILED';
    let responseData = {};
    const ec2 = new aws.EC2({ region: event.ResourceProperties.Region });
    const describeImagesParams = {
        Filters: [
            {
                Name: 'name',
                Values: [archToAMINamePattern[event.ResourceProperties.Architecture]],
            },
        ],
        Owners: [event.ResourceProperties.Architecture === 'HVMG2' ? '679593333241' : 'amazon'],
    };

    // Get AMI IDs with the specified name pattern and owner
    ec2.describeImages(describeImagesParams, (err, data) => {
        if (err) {
            responseData = { Error: 'DescribeImages call failed' };
            console.log(`${responseData.Error}:\n`, err);
        } else {
            const images = data.Images;
            // Sort images by name in descending order -- the names contain the AMI version formatted as YYYY.MM.Ver.
            images.sort((x, y) => y.Name.localeCompare(x.Name));
            for (let i = 0; i < images.length; i++) {
                if (!isBeta(images[i].Name)) {
                    responseStatus = 'SUCCESS';
                    responseData.Id = images[i].ImageId;
                    break;
                }
            }
        }
        sendResponse(event, callback, context.logStreamName, responseStatus, responseData);
    });
};
