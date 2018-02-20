/**
 * Stream events from AWS Kinesis to Splunk
 *
 * This function streams AWS Kinesis events to Splunk using
 * Splunk's HTTP event collector API.
 *
 * Define the following Environment Variables in the console below to configure
 * this function to stream events to your Splunk host:
 *
 * 1. SPLUNK_HEC_URL: URL address for your Splunk HTTP event collector endpoint.
 * Default port for event collector is 8088. Example: https://host.com:8088/services/collector
 *
 * 2. SPLUNK_HEC_TOKEN: Token for your Splunk HTTP event collector.
 * To create a new token for this Lambda function, refer to Splunk Docs:
 * http://docs.splunk.com/Documentation/Splunk/latest/Data/UsetheHTTPEventCollector#Create_an_Event_Collector_token
 */

'use strict';

const loggerConfig = {
    url: process.env.SPLUNK_HEC_URL,
    token: process.env.SPLUNK_HEC_TOKEN,
};

const SplunkLogger = require('./lib/mysplunklogger');

const logger = new SplunkLogger(loggerConfig);

exports.handler = (event, context, callback) => {
    console.log('Received event:', JSON.stringify(event, null, 2));
    let count = 0;

    event.Records.forEach((record) => {
        // Kinesis data is base64 encoded so decode here
        const data = new Buffer(record.kinesis.data, 'base64').toString('ascii');
        let item = null;

        /* NOTE: if Kinesis stream records originates from CloudWatch Logs, data is
        compressed and needs to be expanded here. Refer to 'splunk-cloudwatch-log-processor'
        blueprint in AWS Lambda console for sample code using zlib */

        console.log('Decoded payload:', JSON.stringify(data, null, 2));

        try {
            item = JSON.parse(data);
        } catch (exception) {
            item = data;
        }

        /* Log event to Splunk
        - Use optional 'context' argument to send Lambda metadata e.g. awsRequestId, functionName.
        - Change to "logger.logWithTime(<EVENT_TIMESTAMP>, item, context)" to explicitly set event timestamp */
        logger.log(item, context);

        /* Alternatively, UNCOMMENT logger call below if you want to override Splunk input settings */
        /* Log event to Splunk with any combination of explicit timestamp, index, source, sourcetype, and host.
        - Complete list of input settings available at http://docs.splunk.com/Documentation/Splunk/latest/RESTREF/RESTinput#services.2Fcollector */
        // logger.logEvent({
        //     time: record.kinesis.approximateArrivalTimestamp,
        //     host: 'serverless',
        //     source: `lambda:${context.functionName}`,
        //     sourcetype: 'httpevent',
        //     index: 'main',
        //     event: item,
        // });

        count += 1;
    });

    // Send all the events in a single batch to Splunk
    logger.flushAsync((error, response) => {
        if (error) {
            callback(error);
        } else {
            console.log(`Response from Splunk:\n${response}`);
            console.log(`Successfully processed ${count} record(s).`);
            callback(null, count); // Return number of records processed
        }
    });
};
