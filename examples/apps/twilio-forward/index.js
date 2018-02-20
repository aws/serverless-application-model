'use strict';

const respond = (callback, contents) => callback(null, {
    statusCode: '200',
    body: `<?xml version="1.0" encoding="UTF-8"?><Response>${contents}</Response>`,
    headers: {
        'Content-Type': 'application/xml',
    },
});

// e.g. 415-555-1212 --> +14155551212
const normalizeNumber = (number) => `+1${number.replace(/[^0-9]/g, '')}`;


/**
 * Forward will forward a call to another phone number. If the call isn't answered
 * or the line is busy, the call is optionally forwarded to a new URL.
 *
 * Example request: /<function_name>?PhoneNumber=415-555-1212
 */
exports.handler = (event, context, callback) => {
    const query = event.queryStringParameters || {};

    if (query.DialCallStatus) {
        // We're returning from an attempted Dial
        const status = query.DialCallStatus;
        if (status === 'completed' || status === 'answered' || !query.FailUrl) {
            // Answered, or no failure URL given, so just hang up
            return respond(callback, '<Hangup />');
        }
        // DialStatus was not answered, so redirect to FailUrl
        return respond(callback, `<Redirect>${query.FailUrl}</Redirect>`);
    }

    // We made it to here, so just dial the number with the optional Timeout given
    const failUrl = query.FailUrl ? `?FailUrl=${encodeURIComponent(query.FailUrl)}` : '';
    const action = `${event.path}${failUrl}`;
    respond(callback, `<Dial method="GET" action="${action}">${normalizeNumber(query.PhoneNumber)}</Dial>`);
};
