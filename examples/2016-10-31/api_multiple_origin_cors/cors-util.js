// this is the list of headers allowed by default by the API Gateway console
// see: https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-cors.html
// and: https://docs.aws.amazon.com/AmazonS3/latest/API/RESTCommonRequestHeaders.html
const DEFAULT_ALLOWED_HEADERS = [
    "Content-Type",        // indicates the media type of the resource
    "X-Amz-Date",          // the current date and time according to the requester (must be present for authorization)
    "Authorization",       // information required for request authentication
    "X-Api-Key",           // an AWS API key
    "X-Amz-Security-Token" // see link above
];

/**
 * Return an object literal that contains an Access-Control-Allow-Origin header
 * if the request origin matches a pattern for an allowed origin.
 * Otherwise, return an empty object literal.
 * @param event Lambda event event associated with a request
 * @param allowedOrigins A list of strings or regexes representing allowed origin URLs
 * @return {Object} an object containing allowed header and its value
 */
exports.makeOriginHeader = (event, allowedOrigins) => {
    // determine origin
    const origin = event.headers.Origin || event.headers.origin;
    if (typeof origin === "undefined")
        return {}; // no CORS headers necessary; browser will load resource

    // look for origin in list of allowed origins
    const allowedPattern = allowedOrigins.find(pattern => origin.match(pattern));
    if (typeof allowedPattern === "undefined")
        return {}; // return no CORS headers; browser will not load resource
                   // we do not return a "null" origin because this is exploitable
    
    allowedOrigin = origin.match(allowedPattern)[0]; // determine exact match

    return {"Access-Control-Allow-Origin": allowedOrigin};
};

/**
 * Return an object literal that contains all headers necessary for a CORS
 * preflight.
 * @param event Lambda event associated with a request
 * @param {Array} allowedOrigins see documentation for makeOriginHeader() 
 * @param {Array} allowedMethods a list of strings representing allowed HTTP methods
 * @param {Array} allowedHeaders (optional) a list of strings representing allowed headers
 * @return {Object} an object containing several header => value mappings
 */
exports.makeHeaders = (event, allowedOrigins, allowedMethods, allowedHeaders = DEFAULT_ALLOWED_HEADERS) => {
    return Object.assign(exports.makeOriginHeader(event, allowedOrigins), {
        "Access-Control-Allow-Headers": allowedHeaders.join(","),
        "Access-Control-Allow-Methods": allowedMethods.join(",")
    });
};

/**
 * Compiles a URL containing wildcards into a regular expression.
 * Using this is optional.
 * 
 * Builds a regular expression that matches exactly the input URL, but with 
 * the pattern .*? in place of any wildcard (*) characters. In practice,
 * http://*.example.com matches http://abc.xyz.example.com but not http://example.com
 * http://*.example.com does not match http://example.org/.example.com
 * @param {String} url the url to compile
 * @return {RegExp} compiled regular expression
 */
exports.compileURLWildcards = (url) => {
    // unreserved characters as per https://tools.ietf.org/html/rfc3986#section-2.3
    const url_unreserved_pattern = "[A-Za-z0-9\-._~]";
    const wildcard_pattern = url_unreserved_pattern + "*";
    
    const parts = url.split("*");
    const escapeRegex = str => str.replace(/([.?*+^$(){}|[\-\]\\])/g, "\\$1");
    const escaped = parts.map(escapeRegex);
    return new RegExp("^" + escaped.join(wildcard_pattern) + "$");
};