'use strict';
console.log('Loading function');

/* Syslog format parser */
const parser = '^((?:\\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?' +
    '|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\\b\\s+(?:(?:0[1-9])|(?:[12][0-9])|(?:3[01])|[1-9])\\s+' +
    '(?:(?:2[0123]|[01]?[0-9]):(?:[0-5][0-9]):(?:(?:[0-5]?[0-9]|60)(?:[:\\.,][0-9]+)?)))) (?:<(?:[0-9]+).(?:[0-9]+)> ' +
    ')?((?:[a-zA-Z0-9._-]+)) ([\\w\\._/%-]+)(?:\\[((?:[1-9][0-9]*))\\])?: (.*)';

exports.handler = (event, context, callback) => {
    let success = 0; // Number of valid entries found
    let failure = 0; // Number of invalid entries found

    /* Process the list of records and transform them */
    const output = event.records.map((record) => {
        // Kinesis data is base64 encoded so decode here
        console.log(record.recordId);
        const payload = new Buffer(record.data, 'base64').toString('ascii');
        console.log('Decoded payload:', payload);
        const match = payload.match(parser);
        if (match) {
            /* Prepare JSON version from Syslog log data */
            const result = {
                timestamp: match[1],
                hostname: match[2],
                program: match[3],
                processid: match[4],
                message: match[5],
            };
            success++;
            return {
                recordId: record.recordId,
                result: 'Ok',
                data: new Buffer(JSON.stringify(result)).toString('base64'),
            };
        } else {
            /* Failed event, notify the error and leave the record intact */
            failure++;
            return {
                recordId: record.recordId,
                result: 'ProcessingFailed',
                data: record.data,
            };
        }
    });
    console.log(`Processing completed.  Successful records ${success}, Failed records ${failure}.`);
    callback(null, { records: output });
};

