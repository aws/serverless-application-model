/*
 * Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 */

/*
 * Demonstrates a simple publish to a topic using Greengrass Core NodeJS SDK
 * This lambda function will retrieve underlying platform information and send
 * a hello world message along with the platform information to the topic
 * 'hello/world'. The function will sleep for five seconds, then repeat.
 * Since the function is long-lived it will run forever when deployed to a
 * Greengrass core.
 */

const ggSdk = require('aws-greengrass-core-sdk');

const iotClient = new ggSdk.IotData();
const os = require('os');
const util = require('util');

function publishCallback(err, data) {
    console.log(err);
    console.log(data);
}

const myPlatform = util.format('%s-%s', os.platform(), os.release());
const pubOpt = {
    topic: 'hello/world',
    payload: JSON.stringify({ message: util.format('Hello world! Sent from Greengrass Core running on platform: %s using NodeJS', myPlatform) }),
};

function greengrassHelloWorldRun() {
    iotClient.publish(pubOpt, publishCallback);
}

// Schedule the job to run every 5 seconds
setInterval(greengrassHelloWorldRun, 5000);

// This is a handler which does nothing for this example
exports.handler = function handler(event, context) {
    console.log(event);
    console.log(context);
};
