const cors = require("./cors-util");

// createOriginHeader
test("use createOriginHeader to make a header for no origin", () => {
    const result = cors.createOriginHeader(undefined, []);
    expect(result).toEqual({});
});

test("use createOriginHeader to make a header for a single origin", () => {
    const origin = "https://amazon.com";
    const allowedOrigins = [origin];
    const result = cors.createOriginHeader(origin, allowedOrigins);
    expect(result).toEqual({"Access-Control-Allow-Origin": origin});
});

test("use createOriginHeader to make a header for one of several origins", () => {
    const origin = "https://amazon.com";
    const allowedOrigins = ["https://example.com", origin, "http://amazon.com"];
    const result = cors.createOriginHeader(origin, allowedOrigins);
    expect(result).toEqual({"Access-Control-Allow-Origin": origin});
});

test("use createOriginHeader to make a header for a disallowed origin", () => {
    const origin = "https://not-amazon.com";
    const allowedOrigins = [];
    const result = cors.createOriginHeader(origin, allowedOrigins);
    expect(result).toEqual({});
});

test("use createOriginHeader to make a header for a disallowed origin", () => {
    const origin = "https://not-amazon.com";
    const allowedOrigins = ["https://example.com", "https://amazon.com", "http://amazon.com"];
    const result = cors.createOriginHeader(origin, allowedOrigins);
    expect(result).toEqual({});
});

// createPreflightResponse
test("use createPreflightResponse to make CORS preflight headers", () => {
    const origin = "https://amazon.com";
    const allowedOrigins = [origin];
    const allowedMethods = ["CREATE", "OPTIONS"];
    const allowedHeaders = ["Authorization"];
    const maxAge = 8400;
    const result = cors.createPreflightResponse(origin, allowedOrigins, allowedMethods, allowedHeaders, maxAge);
    expect(result).toEqual({
        headers: {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": "CREATE,OPTIONS",
            "Access-Control-Allow-Headers": "Authorization",
            "Access-Control-Max-Age": 8400
        }, 
        statusCode: 204
    });
});

// compileURLWildcards
test("compile pattern with no wildcards", () => {
    const pattern = "https://amazon.com";
    const regex = cors.compileURLWildcards(pattern);
    expect(pattern).toMatch(regex);
    expect("https://example.com").not.toMatch(regex);
});

test("test pattern with wildcard", () => {
    const pattern = "https://*";
    const regex = cors.compileURLWildcards(pattern);
    expect("https://example.com").toMatch(regex);
});

test("test pattern with subdomain wildcard", () => {
    const pattern = "https://*.amazon.com";
    const regex = cors.compileURLWildcards(pattern);
    expect("https://restaurants.amazon.com").toMatch(regex);
    expect("https://amazon.com").not.toMatch(regex);
    expect("https://x.y.z.amazon.com").toMatch(regex);
    expect("https://restaurants.example.com").not.toMatch(regex);
});

test("test pattern with subdomain wildcard against malicious input", () => {
    const pattern = "https://*.amazon.com";
    const regex = cors.compileURLWildcards(pattern);
    expect("https://restaurants.amazon.com").toMatch(regex);
    expect("https://my.website/restaurants.amazon.com").not.toMatch(regex);
});