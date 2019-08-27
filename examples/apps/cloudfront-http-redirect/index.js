'use strict';

exports.handler = (event, context, callback) => {
    
    var response = {
        "statusCode": 302,
        "headers": {
            "Location": "http://docs.aws.amazon.com/lambda/latest/dg/lambda-edge.html"
        },
        "body": "{}",
        "isBase64Encoded": false
    };
    callback(null, response);
};

