'use strict';

exports.handler = (event, context, callback) => {
    function CustomError(message) {
        this.name = 'CustomError';
        this.message = message;
    }
    CustomError.prototype = new Error();

    const error = new CustomError('This is a custom error!');
    callback(error);
};
