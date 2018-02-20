'use strict';

const respond = (callback, contents) => callback(null, {
    statusCode: '200',
    body: `<?xml version="1.0" encoding="UTF-8"?><Response>${contents}</Response>`,
    headers: {
        'Content-Type': 'application/xml',
    },
});

const getOptions = (query) => Object.keys(query)
        .map((k) => /^Options\[(.*?)\]$/.exec(k))
        .filter((m) => !!m)
        .reduce((o, m) => {
            const obj = o;
            obj[m[1]] = query[m[0]];
            return obj;
        }, {});


/**
 * Simple Menu will just play a greeting, and wait for the caller to press one
 * or more digits on their keypad. Based on what was pressed, call flow is
 * directed to a new URL.
 *
 * Menu options should be encoded as query string parameters of the following
 * form: `Options[<digits>]=<url>`.
 *
 * Example request: /<function_name>?Message=Hi+There&Options[101]=http://bob.com&Options[102]=http://ann.com&Options[0]=http://operator.com
 */
exports.handler = (event, context, callback) => {
    const query = event.queryStringParameters || {};
    const options = getOptions(query);

    if (query.Digits) {
        // We got here after a Dial attempt
        const location = options[query.Digits];
        if (location) {
            // Valid option given, redirect
            return respond(callback, `<Redirect>${location}</Redirect>`);
        }
        return respond(callback, "<Say>I'm sorry, that wasn't a valid option.</Say>");
    }

    // Calculate the max number of digits we need to wait for
    const maxDigits = Object.keys(options).reduce((a, b) => Math.max(a.length, b.length));
    // Determine the gather action
    let action = '';
    if (query.Message && query.Message.trim().substring(0, 4).toLowerCase() === 'http') {
        // Play the greeting while accepting digits
        action = `<Play>${query.Message}</Play>`;
    } else if (query.Message) {
        // Read back the message given
        action = `<Say>${query.Message}</Say>`;
    }

    // Add a redirect if nothing was pressed
    respond(callback, `<Gather method="GET" numDigits="${maxDigits}">${action}</Gather><Redirect />`);
};
