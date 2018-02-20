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
        const payload = (Buffer.from(record.data, 'base64')).toString('ascii');
        const match = payload.match(parser);
        if (match) {
            /* Prepare CSV version from Syslog log data */
            const result = `${match[1]},${match[2]},${match[3]},${match[4]},${match[5]},${match[6]}\n`;
            success++;
            return {
                recordId: record.recordId,
                result: 'Ok',
                data: (Buffer.from(result, 'utf8')).toString('base64'),
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

