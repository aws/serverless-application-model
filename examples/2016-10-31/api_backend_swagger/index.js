'use strict';
console.log('Loading function');

let table = process.env.TABLE_NAME;

exports.handler = (event, context, callback) => {
    var response = {
        HTTP_Method: event.context["http-method"],
        API_ID: event.context["api-id"],
        Lambda_Function: context.functionName,
        DynamoDB_Table: table,
        API_Request: event
    };
    callback(null, response);
};