'use strict';
const createResponse = (statusCode, body) => ({ statusCode, body });

exports.get = (event, context, callback) => {
    callback(null, createResponse(200, 'You will never see this.'));
};

exports.auth = (event, context, callback) => {
    return callback('Unauthorized', null)
};
