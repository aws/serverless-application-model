'use strict';


exports.handler = async (event, context, callback) => {
    console.log("Message attributes: " + JSON.stringify(event.Records[0].Sns.MessageAttributes));

    callback(null, "Success");
};