const cors = require("../cors-util");
const config = require("../cors-config.json");

/**
 * Demonstrates an endpoint that accepts DELETE requests.
 * 
 * In this case, the browser will perform a CORS preflight request, so we must
 * handle OPTIONS requests and provide the CORS headers.
 * When the browser makes the DELETE request, we only need to provide the origin.
 */
exports.handler = async (event, context) => {
    const origin = cors.getOriginFromEvent(event);
    const allowedMethods = ["OPTIONS", "DELETE"];

    if (event.httpMethod === "OPTIONS") {
        return cors.createPreflightResponse(origin, config.allowedOrigins, allowedMethods);
    } else if (event.httpMethod === "DELETE") {
        // return an empty response, with CORS origin
        return {
            headers: cors.createOriginHeader(origin, config.allowedOrigins),
            statusCode: 204
        };
    }
};
