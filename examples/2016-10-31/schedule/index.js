'use strict';
console.log('Loading function');

exports.handler = (event, context, callback) => {
    console.log("Invocation with event =", event);
    callback(null, 'Everything is ok!');
};