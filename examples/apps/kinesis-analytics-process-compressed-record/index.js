'use strict';
console.log('Loading function');
const zlib = require('zlib');

exports.handler = (event, context, callback) => {
    let success = 0; // Number of valid entries found
    let failure = 0; // Number of invalid entries found
    /* Process the list of records */
    const output = event.records.map((record) => {
        /* Data is base64 encoded, so decode here */
        const compressedData = Buffer.from(record.data, 'base64');
        try {
            const decompressedData = zlib.unzipSync(compressedData);
            /* Encode decompressed JSON or CSV */
            const result = (Buffer.from(decompressedData, 'utf8')).toString('base64');
            success++;
            return {
                recordId: record.recordId,
                result: 'Ok',
                data: result,
            };
        } catch (err) {
            failure++;
            return {
                recordId: record.recordId,
                result: 'ProcessingFailed',
                data: record.data,
            };
        }
    });
    console.log(`Processing completed.  Successful records ${success}, Failed records ${failure}.`);
    callback(null, {
        records: output,
    });
};
