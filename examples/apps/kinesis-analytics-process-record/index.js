'use strict';
console.log('Loading function');

exports.handler = (event, context, callback) => {
    /* Process the list of records */
    const output = event.records.map((record) => ({
        recordId: record.recordId,
        result: 'Ok',
        data: record.data,
    }));
    console.log(`Processing completed.  Successful records ${output.length}.`);
    callback(null, { records: output });
};
