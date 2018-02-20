'use strict';

const aws = require('aws-sdk'); // Loads the AWS SDK for JavaScript.

const config = new aws.ConfigService(); // Constructs a service object to use the aws.ConfigService class.
const COMPLIANCE_STATES = {
    COMPLIANT: 'COMPLIANT',
    NON_COMPLIANT: 'NON_COMPLIANT',
    NOT_APPLICABLE: 'NOT_APPLICABLE',
};


// Checks whether the invoking event is ScheduledNotification
function isScheduledNotification(invokingEvent) {
    return (invokingEvent.messageType === 'ScheduledNotification');
}

// Evaluates the configuration items in the snapshot and returns the compliance value to the handler.
function evaluateCompliance(maxCount, actualCount) {
    return (actualCount > maxCount) ? COMPLIANCE_STATES.NON_COMPLIANT : COMPLIANCE_STATES.COMPLIANT;
}

function countResourceTypes(applicableResourceType, nextToken, count, callback) {
    config.listDiscoveredResources({ resourceType: applicableResourceType, nextToken }, (err, data) => {
        if (err) {
            return callback(err);
        }
        const updated = count + data.resourceIdentifiers.length;
        if (data.nextToken) {
            countResourceTypes(applicableResourceType, data.nextToken, updated, callback);
        } else {
            callback(null, updated);
        }
    });
}


// Receives the event and context from AWS Lambda. You can copy this handler and use it in your own
// code with little or no change.
exports.handler = (event, context, callback) => {
    // Parses the invokingEvent and ruleParameters values, which contain JSON objects passed as strings.
    const invokingEvent = JSON.parse(event.invokingEvent);
    const ruleParameters = JSON.parse(event.ruleParameters);
    const resourceCount = 0;

    if (isScheduledNotification(invokingEvent)) {
        countResourceTypes(ruleParameters.applicableResourceType, '', resourceCount, (err, count) => {
            if (err) {
                return callback(err);
            }
            // Initializes the request that contains the evaluation results.
            const putEvaluationsRequest = {
                Evaluations: [{
                    // Applies the evaluation result to the AWS account published in the event.
                    ComplianceResourceType: 'AWS::::Account',
                    ComplianceResourceId: event.accountId,
                    ComplianceType: evaluateCompliance(ruleParameters.maxCount, count),
                    OrderingTimestamp: new Date(),
                }],
                ResultToken: event.resultToken,
            };
            // Sends the evaluation results to AWS Config.
            config.putEvaluations(putEvaluationsRequest, (putErr, data) => {
                if (putErr) {
                    return callback(putErr);
                }
                if (data.FailedEvaluations.length > 0) {
                    // Ends the function execution if any evaluation results are not successfully reported
                    return callback(JSON.stringify(data));
                }
                callback(null, data);
            });
        });
    } else {
        callback('Invoked for a notification other than Scheduled Notification... Ignoring.');
    }
};
