exports.handler = function(event, context, callback) {

    callback(null, {
        statusCode: '200',
        body: "Hello world",
        headers: {
            // This is ALSO required for CORS to work. When browsers issue cross origin requests, they make a 
            // preflight request (HTTP Options) which is responded automatically based on SAM configuration. 
            // But the actual HTTP request (GET/POST etc) also needs to contain the AllowOrigin header. 
            // 
            // NOTE: This value is *not* double quoted: ie. "'www.example.com'" is wrong
            "Access-Control-Allow-Origin": "https://www.example.com"
        }
    });

}
