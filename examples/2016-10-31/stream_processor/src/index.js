'use strict';
console.log('Loading function');

exports.handler = (event, context, callback) => {
    event.Records.forEach((record) => {
        // Kinesis data is base64 encoded so decode here
        const payload = new Buffer(record.kinesis.data, 'base64').toString('ascii');
        console.log('Decoded payload:', payload);
    });
    callback(null, `Successfully processed ${event.Records.length} records.`);
};