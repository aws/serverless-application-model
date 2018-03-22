'use strict';

exports.handler = (evt, ctx, cb) => {
    console.log("New request received... adding Hello World HTTP Header");
    var request = evt.Records[0].cf.request;
    request.headers['hello'] = [{ key: 'hello', value: 'world'}];

    cb(null, request);

}