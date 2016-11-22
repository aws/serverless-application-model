console.log('Loading function');

var AWS = require('aws-sdk');
var dynamo = new AWS.DynamoDB.DocumentClient();
var table = process.env.TABLE_NAME;

exports.handler = function(event, context, callback) {
    //console.log('Received event:', JSON.stringify(event, null, 2));

   var params = {
    TableName:table,
    Item:{
        "id": event.id,
        "thing": event.thing
        }
    };
       
    console.log("Adding a new IoT device...");
    dynamo.put(params, function(err, data) {
    if (err) {
        console.error("Unable to add device. Error JSON:", JSON.stringify(err, null, 2));
        callback(err);
    } else {
        console.log("Added device:", JSON.stringify(data, null, 2));
        callback(null,'DynamoDB updated');
    }
    });

    
}
