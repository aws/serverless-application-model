const cors = require("./cors-util");

const makeMockEvent = origin => {
    return {"headers": {"origin": origin}};
};

// makeOriginHeader
test("use makeOriginHeader to make a header for no origin", () => {
    const result = cors.makeOriginHeader({headers: {}}, []);
    expect(result).toEqual({});
});

test("use makeOriginHeader to make a header for a single origin", () => {
    const origin = "https://amazon.com";
    const event = makeMockEvent(origin);
    const allowedOrigins = [origin];
    const result = cors.makeOriginHeader(event, allowedOrigins);
    expect(result).toEqual({"Access-Control-Allow-Origin": origin});
});

test("use makeOriginHeader to make a header for one of several origins", () => {
    const origin = "https://amazon.com";
    const allowedOrigins = ["https://example.com", origin, "http://amazon.com"];
    const event = makeMockEvent(origin);
    const result = cors.makeOriginHeader(event, allowedOrigins);
    expect(result).toEqual({"Access-Control-Allow-Origin": origin});
});

test("use makeOriginHeader to make a header for a disallowed origin", () => {
    const origin = "https://not-amazon.com";
    const allowedOrigins = [];
    const event = makeMockEvent(origin);
    const result = cors.makeOriginHeader(event, allowedOrigins);
    expect(result).toEqual({});
});

test("use makeOriginHeader to make a header for a disallowed origin", () => {
    const origin = "https://not-amazon.com";
    const allowedOrigins = ["https://example.com", "https://amazon.com", "http://amazon.com"];
    const event = makeMockEvent(origin);
    const result = cors.makeOriginHeader(event, allowedOrigins);
    expect(result).toEqual({});
});

// makeHeaders
test("use makeHeaders to make CORS preflight headers", () => {
    const origin = "https://amazon.com";
    const allowedOrigins = [origin];
    const allowedMethods = ["CREATE", "OPTIONS"];
    const allowedHeaders = ["Authorization"]
    const event = makeMockEvent(origin);
    const result = cors.makeHeaders(event, allowedOrigins, allowedMethods, allowedHeaders);
    expect(result).toEqual({
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Methods": "CREATE,OPTIONS",
        "Access-Control-Allow-Headers": "Authorization"
    });
});

// compileURLWildcards
test("compile pattern with no wildcards", () => {
    const pattern = "https://amazon.com";
    const regex = cors.compileURLWildcards(pattern);
    expect(pattern).toMatch(regex);
    expect("https://example.com").not.toMatch(regex);
});

test("compile '*'", () => {
    const pattern = "*";
    const regex = cors.compileURLWildcards(pattern);
    expect("https://example.com").toMatch(regex);
    expect("apple").toMatch(regex);
});

test("compile pattern with subdomain wildcard", () => {
    const pattern = "https://*.amazon.com";
    const regex = cors.compileURLWildcards(pattern);
    expect("https://restaurants.amazon.com").toMatch(regex);
    expect("https://amazon.com").not.toMatch(regex);
    expect("https://x.y.z.amazon.com").toMatch(regex);
    expect("https://restaurants.example.com").not.toMatch(regex);
})