'use strict';

const crypto = require('crypto');


const respond = (callback, contents) => callback(null, {
    statusCode: '200',
    body: `<?xml version="1.0" encoding="UTF-8"?><Response>${contents}</Response>`,
    headers: {
        'Content-Type': 'application/xml',
    },
});


/**
 * Conference allows multiple people to chat together in a conference room.
 *
 * Example request: /<function_name>?Name=My+Conference&Password=123&Message=Hello
 */
exports.handler = (event, context, callback) => {
    const query = event.queryStringParameters || {};

    if (query.Password && query.Digits !== query.Password) {
        // Password is set, so ask for it (minimum of 3 digits for security)
        return respond(callback, `
<Gather method="GET" numDigits="${Math.max(3, query.Password.length)}">
    <Say>Please enter your conference pass code</Say>
</Gather>
<Redirect></Redirect>
`);
    }

    const response = [];

    if (query.Message && query.Message.trim().substring(0, 4).toLowerCase() === 'http') {
        // Play the given message from an HTTP URL
        response.push(`<Play>${query.Message}</Play>`);
    } else if (query.Message) {
        // Read back the message given
        response.push(`<Say>${query.Message}</Say>`);
    } else {
        // Default message
        response.push('<Say>You are now entering the conference line.</Say>');
    }

    // Get the conference name or generate a unique hash if none is provided
    const name = query.Name || crypto.createHash('md5').update(JSON.stringify(query)).digest('hex');

    response.push(`<Dial method="GET"><Conference>${name}</Conference></Dial>`);

    // Flush out response
    respond(callback, response.join(''));
};
