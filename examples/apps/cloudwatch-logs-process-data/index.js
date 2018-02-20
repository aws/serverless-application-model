'use strict';

const zlib = require('zlib');

exports.handler = (event, context, callback) => {
    const payload = new Buffer(event.awslogs.data, 'base64');
    zlib.gunzip(payload, (err, res) => {
        if (err) {
            return callback(err);
        }
        const parsed = JSON.parse(res.toString('utf8'));
        console.log('Decoded payload:', JSON.stringify(parsed));
        callback(null, `Successfully processed ${parsed.logEvents.length} log events.`);
    });
};
