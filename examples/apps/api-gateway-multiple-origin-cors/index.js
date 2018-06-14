// Demonstrates Lambda functions that provide CORS headers for many origins.

const cors = require("./cors-util");

// define a whitelist of allowed origins
const allowedOrigins = [
    "http://127.0.0.1",
    "https://*.example.com",
    "https://*.amazon.com"
];

/**
 * Demonstrates a simple endpoint that accepts GET requests.
 * 
 * In most cases, browsers do not perform CORS preflight requests when using
 * the GET method, so we do not have to handle OPTIONS requests.
 * Any desired additional CORS headers should be included in the GET response.
 */
exports.handleRoot = async (event, context) => {
    const origin = cors.getOriginFromEvent(event);

    // return an empty response, with CORS origin
    return {
        headers: cors.createOriginHeader(origin, allowedOrigins),
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

    // return an empty response, with CORS origin
    return {
        headers: cors.createOriginHeader(origin, allowedOrigins),
        statusCode: 204
    };
};
exports.handleTestPreflight = async (event, context) => {
    const origin = cors.getOriginFromEvent(event);
    const allowedMethods = ["OPTIONS", "DELETE"];

    return cors.createPreflightResponse(origin, allowedOrigins, allowedMethods);
};
