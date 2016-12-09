'use strict';


const AWS = require('aws-sdk');
const dynamo = new AWS.DynamoDB.DocumentClient();

const tableName = process.env.TABLE_NAME;

const createResponse = (statusCode, body) => {
    
    return {
        statusCode: statusCode,
        body: body
    }
};

exports.get = (event, context, callback) => {
    
    let params = {
        TableName: tableName,
        Key: {
            id: event.pathParameters.resourceId
        }
    };
    
    let dbGet = (params) => { return dynamo.get(params).promise() };
    
    dbGet(params).then( (data) => {
        if (!data.Item) {
            callback(null, createResponse(404, "ITEM NOT FOUND"));
            return;
        }
        console.log(`RETRIEVED ITEM SUCCESSFULLY WITH doc = ${data.Item.doc}`);
        callback(null, createResponse(200, data.Item.doc));
    }).catch( (err) => { 
        console.log(`GET ITEM FAILED FOR doc = ${data.Item.doc}, WITH ERROR: ${err}`);
        callback(null, createResponse(500, err));
    });
};

exports.put = (event, context, callback) => {
    
    let item = {
        id: event.pathParameters.resourceId,
        doc: event.body
    };

    let params = {
        TableName: tableName,
        Item: item
    };
    
    let dbPut = (params) => { return dynamo.put(params).promise() };
    
    dbPut(params).then( (data) => {
        console.log(`PUT ITEM SUCCEEDED WITH doc = ${item.doc}`);
        callback(null, createResponse(200, null));
    }).catch( (err) => { 
        console.log(`PUT ITEM FAILED FOR doc = ${item.doc}, WITH ERROR: ${err}`);
        callback(null, createResponse(500, err)); 
    });
};

exports.delete = (event, context, callback) => {
    
    let params = {
        TableName: tableName,
        Key: {
            id: event.pathParameters.resourceId
        },
        ReturnValues: 'ALL_OLD'
    };
    
    let dbDelete = (params) => { return dynamo.delete(params).promise() };
    
    dbDelete(params).then( (data) => {
        if (!data.Attributes) {
            callback(null, createResponse(404, "ITEM NOT FOUND FOR DELETION"));
            return;
        }
        console.log(`DELETED ITEM SUCCESSFULLY WITH id = ${event.pathParameters.resourceId}`);
        callback(null, createResponse(200, null));
    }).catch( (err) => { 
        console.log(`DELETE ITEM FAILED FOR id = ${event.pathParameters.resourceId}, WITH ERROR: ${err}`);
        callback(null, createResponse(500, err));
    });
};
