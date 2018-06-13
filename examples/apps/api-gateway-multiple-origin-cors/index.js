// Demonstrates a Lambda function that provides CORS headers for many origins.

const cors = require("./cors-util");

// define a whitelist of allowed origins
const allowedOrigins = [
    "http://127.0.0.1",
    "https://*.example.com",
    "https://*.amazon.com"
].map(cors.compileURLWildcards);

/**
 * Demonstrates a simple endpoint that accepts GET requests.
 * 
 * In most cases, browsers do not perform CORS preflight requests when using
 * the GET method, so we do not have to handle OPTIONS requests.
 * We include all CORS headers in the GET response.
 */
exports.handleRoot = async (event, context) => {
    const origin = cors.getOriginFromEvent(event);
    const allowedMethods = ["GET"];

    // return an empty response, with CORS headers
    return {
        headers: Object.assign(cors.makeHeaders(origin, allowedOrigins, allowedMethods), {
            // use Object.assign to include additional headers
        }),
        statusCode: 204
    };
};

/**
 * Demonstrates an endpoint that accepts DELETE requests.
 * 
 * In this case, the browser will perform a CORS preflight request, so we must
 * handle OPTIONS requests and provide the CORS headers.
 * When the browser makes the DELETE request, we only need to provide the origin.
 */
exports.handleTest = async (event, context) => {
    const origin = cors.getOriginFromEvent(event);
    const allowedMethods = ["OPTIONS", "DELETE"];

    if (event.httpMethod === "OPTIONS") {
        // return an empty response, with all CORS headers
        return {
            headers: cors.makeHeaders(origin, allowedOrigins, allowedMethods),
            statusCode: 204
        };
    } else if (event.httpMethod === "DELETE") {
        // return an empty response, with CORS origin
        return {
            headers: cors.makeOriginHeader(origin, allowedOrigins),
            statusCode: 204
        };
    }
    return {statusCode: 405}; // invalid method
};
