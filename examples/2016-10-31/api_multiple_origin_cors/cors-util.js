const DEFAULT_ALLOWED_HEADERS = [
    "Content-Type",
    "X-Amz-Date",
    "Authorization",
    "X-Api-Key",
    "X-Amz-Security-Token"
];

/**
 * Return an object literal that contains an Access-Control-Allow-Origin header
 * if the request origin matches a pattern for an allowed origin.
 * Otherwise, return an empty object literal.
 * @param event Lambda event event associated with a request
 * @param allowedOrigins A list of strings or regexes representing allowed origin URLs
 * @return {Object} an object containing a header => value mapping, or nothing
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

    // console.log("origin: " + origin);
    // console.log("allowed by: " + allowedPattern);
    
    // produce origin header
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
 * Compiles a path containing wildcards into a regular expression.
 * Using this is optional.
 * @param {String} path the path to compile
 * @return {RegExp} compiled regular expression
 */
exports.compileURLWildcards = (path) => {
    const parts = path.split("*");
    const escapeRegex = str => str.replace(/([.?*+^$(){}|[\-\]\\])/g, "\\$1");
    const escaped = parts.map(escapeRegex);
    return new RegExp("^" + escaped.join(".*?") + "$");
};