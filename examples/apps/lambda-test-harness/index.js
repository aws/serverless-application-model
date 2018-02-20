'use strict';

/**
 * Provides a simple framework for conducting various tests of your Lambda
 * functions. Make sure to include permissions for `lambda:InvokeFunction`
 * and `dynamodb:PutItem` in your execution role!
 */
const AWS = require('aws-sdk');
const doc = require('dynamodb-doc');

const lambda = new AWS.Lambda({ apiVersion: '2015-03-31' });
const dynamo = new doc.DynamoDB();


// Asynchronously runs a given function X times
const asyncAll = (opts) => {
    let i = -1;
    const next = () => {
        i++;
        if (i === opts.times) {
            opts.done();
            return;
        }
        opts.fn(next, i);
    };
    next();
};


/**
 * Will invoke the given function and write its result to the DynamoDB table
 * `event.resultsTable`. This table must have a hash key string of "testId"
 * and range key number of "iteration". Specify a unique `event.testId` to
 * differentiate each unit test run.
 */
const unit = (event, callback) => {
    const lambdaParams = {
        FunctionName: event.function,
        Payload: JSON.stringify(event.event),
    };
    lambda.invoke(lambdaParams, (err, data) => {
        if (err) {
            return callback(err);
        }
        // Write result to Dynamo
        const dynamoParams = {
            TableName: event.resultsTable,
            Item: {
                testId: event.testId,
                iteration: event.iteration || 0,
                result: data.Payload,
                passed: !Object.prototype.hasOwnProperty.call(JSON.parse(data.Payload), 'errorMessage'),
            },
        };
        dynamo.putItem(dynamoParams, callback);
    });
};

/**
 * Will invoke the given function asynchronously `event.iterations` times.
 */
const load = (event, callback) => {
    const payload = event.event;
    asyncAll({
        times: event.iterations,
        fn: (next, i) => {
            payload.iteration = i;
            const lambdaParams = {
                FunctionName: event.function,
                InvocationType: 'Event',
                Payload: JSON.stringify(payload),
            };
            lambda.invoke(lambdaParams, next);
        },
        done: () => callback(null, 'Load test complete'),
    });
};


const ops = {
    unit,
    load,
};

/**
 * Pass the test type (currently either "unit" or "load") as `event.operation`,
 * the name of the Lambda function to test as `event.function`, and the event
 * to invoke this function with as `event.event`.
 *
 * See the individual test methods above for more information about each
 * test type.
 */
exports.handler = (event, context, callback) => {
    if (Object.prototype.hasOwnProperty.call(ops, event.operation)) {
        ops[event.operation](event, callback);
    } else {
        callback(`Unrecognized operation "${event.operation}"`);
    }
};
