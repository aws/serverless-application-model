'use strict';

console.log('Loading function');

const output = `
<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Pause length="2" />
    <Say>Hello Amazon, this is Twilio powered by Lambda</Say>
</Response>
`;

exports.handler = (event, context, callback) => callback(null, {
    statusCode: '200',
    body: output.trim(),
    headers: {
        'Content-Type': 'application/xml',
    },
});
