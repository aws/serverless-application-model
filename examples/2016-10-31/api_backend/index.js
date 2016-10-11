'use strict';
console.log('Loading function');

let doc = require('dynamodb-doc');
let dynamo = new doc.DynamoDB();

const tableName = process.env.TABLE_NAME;

const createResponse = (statusCode, body) => {
    return {
        "statusCode": statusCode,
        "body": body
    }
};

exports.get = (event, context, callback) => {
    var params = {
        "TableName": tableName,
        "Key": {
            id: event.pathParameters.resourceId
        }
    };
    dynamo.getItem(params, (err, data) => {
        var response;
        if (err)
            response = createResponse(500, err);
        else
            response = createResponse(200, data.Item.doc);
        callback(null, response);
    });
};

exports.put = (event, context, callback) => {
    var item = {
        "id": event.pathParameters.resourceId,
        "doc": event.body
    };

    var params = {
        "TableName": tableName,
        "Item": item
    };
    dynamo.putItem(params, (err, data) => {
        var response;
        if (err)
            response = createResponse(500, err);
        else
            response = createResponse(200, null);
        callback(null, response);
    });
};

exports.delete = (event, context, callback) => {
    var params = {
        "TableName": tableName,
        "Key": {
            "id": event.pathParameters.resourceId
        }
    };
    dynamo.deleteItem(params, (err, data) => {
        var response;
        if (err)
            response = createResponse(500, err);
        else
            response = createResponse(200, null);
        callback(null, response);
    });
};
