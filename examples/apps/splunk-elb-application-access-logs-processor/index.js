/**
 * Forward Application Load Balancer Access Logs from S3 to Splunk via AWS Lambda
 *
 * This function streams events to Splunk Enterprise using Splunk's HTTP event collector API.
 *
 * Define the following Environment Variables in the console below to configure
 * this function to log to your Splunk host:
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
const aws = require('aws-sdk');
const zlib = require('zlib');

const logger = new SplunkLogger(loggerConfig);
const s3 = new aws.S3({ apiVersion: '2006-03-01' });

exports.handler = (event, context, callback) => {
    console.log('Received event:', JSON.stringify(event, null, 2));

    // Get the object from the event and show its content type
    const bucket = event.Records[0].s3.bucket.name;
    const key = decodeURIComponent(event.Records[0].s3.object.key.replace(/\+/g, ' '));
    const params = {
        Bucket: bucket,
        Key: key,
    };
    s3.getObject(params, (err, data) => {
        if (err) {
            console.log(err);
            const message = `Error getting object ${key} from bucket ${bucket}. Make sure they exist and your bucket is in the same region as this function.`;
            console.log(message);
            callback(message);
        } else {
            console.log(`Retrieved access log: LastModified="${data.LastModified}" ContentLength=${data.ContentLength}`);
            const payload = data.Body;

            zlib.gunzip(payload, (err, result) => { // eslint-disable-line no-shadow
                if (err) {
                    console.log(err);
                    callback(err);
                } else {
                    const parsed = result.toString('ascii');
                    const logEvents = parsed.split('\n');
                    let count = 0;
                    let time;

                    if (logEvents) {
                        logEvents.forEach((logEntry) => {
                            if (logEntry) {
                                // Extract timestamp as 2nd field in log entry
                                // For more details: http://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html#access-log-entry-format
                                time = logEntry.split(' ')[1];
                                // Log event with specific host, source & sourcetype
                                // Full list of request parameters available on this page - click on [Expand]:
                                // http://docs.splunk.com/Documentation/Splunk/latest/RESTREF/RESTinput#services.2Fcollector
                                logger.logEvent({
                                    time: new Date(time).getTime() / 1000,
                                    host: 'serverless',
                                    source: `s3://${bucket}/${key}`,
                                    sourcetype: 'aws:elb:accesslogs',
                                    event: logEntry,
                                });
                                count += 1;
                            }
                        });
                        console.log(`Processed ${count} log entries`);
                    }

                    logger.flushAsync((err, response) => { // eslint-disable-line no-shadow
                        if (err) {
                            callback(err);
                        } else {
                            console.log(`Response from Splunk:\n${response}`);
                            callback(null, count); // Echo number of events forwarded
                        }
                    });
                }
            });
        }
    });
};
