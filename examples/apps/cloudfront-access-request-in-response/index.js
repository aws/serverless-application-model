'use strict';

exports.handler = (event, context, callback) => {
    const request = event.Records[0].cf.request;
    const response = event.Records[0].cf.response;

    /*
     * Set the Content-Disposition Header based on the user-name request header
     */
    if (request.headers['user-name']) {
        response.headers['content-disposition'] = [{
            key: 'Content-Disposition',
            value: `attachment; filename=${request.headers['user-name'][0].value}`,
        }];
        console.log(`Add content disposition response header "${response.headers['content-disposition'][0].value}"`);
    }
    callback(null, response);
};
