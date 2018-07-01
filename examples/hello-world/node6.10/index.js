'use strict';

// A simple hello world Lambda function
exports.handler = (event, context, callback) => {

    console.log('LOG: Name is ' + event.name);
    callback(null, "Hello " + event.name);

}
