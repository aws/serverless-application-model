'use strict';

/**
 * A blueprint to schedule a recurring assessment run for an Amazon Inspector assessment template.
 *
 * This blueprint assumes that you've already done the following:
 * 1. onboarded with the Amazon Inspector service https://aws.amazon.com/inspector
 * 2. created an assessment target - what hosts you want to assess
 * 3. created an assessment template - how you want to assess your target
 *
 * Then, all you need to do to use this blueprint is to define an environment variable in the Lambda console called
 * `assessmentTemplateArn` and provide the template arn you want to run on a schedule.
 */

const AWS = require('aws-sdk');

const inspector = new AWS.Inspector();

const params = {
    assessmentTemplateArn: process.env.assessmentTemplateArn,
};

exports.handler = (event, context, callback) => {
    try {
        // Inspector.StartAssessmentRun response will look something like:
        // {"assessmentRunArn":"arn:aws:inspector:us-west-2:123456789012:target/0-wJ0KWygn/template/0-jRPJqnQh/run/0-Ga1lDjhP"
        inspector.startAssessmentRun(params, (error, data) => {
            if (error) {
                console.log(error, error.stack);
                return callback(error);
            }

            console.log(data);
            return callback(null, data);
        });
    } catch (error) {
        console.log('Caught Error: ', error);
        callback(error);
    }
};
