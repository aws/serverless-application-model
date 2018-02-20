'use strict';

const url = require('url');

const Logger = function Logger(config) {
    this.url = config.url;
    this.token = config.token;

    this.addMetadata = true;
    this.setSource = true;

    this.parsedUrl = url.parse(this.url);
    // eslint-disable-next-line import/no-dynamic-require
    this.requester = require(this.parsedUrl.protocol.substring(0, this.parsedUrl.protocol.length - 1));
    // Initialize request options which can be overridden & extended by consumer as needed
    this.requestOptions = {
        hostname: this.parsedUrl.hostname,
        path: this.parsedUrl.path,
        port: this.parsedUrl.port,
        method: 'POST',
        headers: {
            Authorization: `Splunk ${this.token}`,
        },
        rejectUnauthorized: false,
    };

    this.payloads = [];
};

// Simple logging API for Lambda functions
Logger.prototype.log = function log(message, context) {
    this.logWithTime(Date.now(), message, context);
};

Logger.prototype.logWithTime = function logWithTime(time, message, context) {
    const payload = {};

    if (Object.prototype.toString.call(message) === '[object Array]') {
        throw new Error('message argument must be a string or a JSON object.');
    }
    payload.event = message;

    // Add Lambda metadata
    if (typeof context !== 'undefined') {
        if (this.addMetadata) {
            // Enrich event only if it is an object
            if (message === Object(message)) {
                payload.event = JSON.parse(JSON.stringify(message)); // deep copy
                payload.event.awsRequestId = context.awsRequestId;
            }
        }
        if (this.setSource) {
            payload.source = `lambda:${context.functionName}`;
        }
    }

    payload.time = new Date(time).getTime() / 1000;

    this.logEvent(payload);
};

Logger.prototype.logEvent = function logEvent(payload) {
    this.payloads.push(JSON.stringify(payload));
};

Logger.prototype.flushAsync = function flushAsync(callback) {
    callback = callback || (() => {}); // eslint-disable-line no-param-reassign

    console.log('Sending event');
    const req = this.requester.request(this.requestOptions, (res) => {
        res.setEncoding('utf8');

        console.log('Response received');
        res.on('data', (data) => {
            let error = null;
            if (res.statusCode !== 200) {
                error = new Error(`error: statusCode=${res.statusCode}\n\n${data}`);
                console.error(error);
            } else {
                console.log('Sent');
            }
            this.payloads.length = 0;
            callback(error, data);
        });
    });

    req.on('error', (error) => {
        callback(error);
    });

    req.end(this.payloads.join(''), 'utf8');
};

module.exports = Logger;
