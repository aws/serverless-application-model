/*
For processing data sent to Firehose by Cloudwatch Logs subscription filters.

Cloudwatch Logs sends to Firehose records that look like this:

{
  "messageType": "DATA_MESSAGE",
  "owner": "123456789012",
  "logGroup": "log_group_name",
  "logStream": "log_stream_name",
  "subscriptionFilters": [
    "subscription_filter_name"
  ],
  "logEvents": [
    {
      "id": "01234567890123456789012345678901234567890123456789012345",
      "timestamp": 1510109208016,
      "message": "log message 1"
    },
    {
      "id": "01234567890123456789012345678901234567890123456789012345",
      "timestamp": 1510109208017,
      "message": "log message 2"
    }
    ...
  ]
}

The data is additionally compressed with GZIP.

The code below will:

1) Gunzip the data
2) Parse the json
3) Set the result to ProcessingFailed for any record whose messageType is not DATA_MESSAGE, thus redirecting them to the
   processing error output. Such records do not contain any log events. You can modify the code to set the result to
   Dropped instead to get rid of these records completely.
4) For records whose messageType is DATA_MESSAGE, extract the individual log events from the logEvents field, and pass
   each one to the transformLogEvent method. You can modify the transformLogEvent method to perform custom
   transformations on the log events.
5) Concatenate the result from (4) together and set the result as the data of the record returned to Firehose. Note that
   this step will not add any delimiters. Delimiters should be appended by the logic within the transformLogEvent
   method.
*/

'use strict';

const zlib = require('zlib');

/**
 * logEvent has this format:
 *
 * {
 *   "id": "01234567890123456789012345678901234567890123456789012345",
 *   "timestamp": 1510109208016,
 *   "message": "log message 1"
 * }
 *
 * The default implementation below just extracts the message and appends a newline to it.
 *
 * The result must be returned in a Promise.
 */
function transformLogEvent(logEvent) {
    return Promise.resolve(`${logEvent.message}\n`);
}

exports.handler = (event, context, callback) => {
    Promise.all(event.records.map(r => {
        const buffer = new Buffer(r.data, 'base64');
        const decompressed = zlib.gunzipSync(buffer);
        const data = JSON.parse(decompressed);
        if (data.messageType !== 'DATA_MESSAGE') {
            return Promise.resolve({
                recordId: r.recordId,
                result: 'ProcessingFailed',
            });
        } else {
            const promises = data.logEvents.map(transformLogEvent);
            return Promise.all(promises).then(transformed => {
                const payload = transformed.reduce((a, v) => a + v, '');
                const encoded = new Buffer(payload).toString('base64');
                return {
                    recordId: r.recordId,
                    result: 'Ok',
                    data: encoded,
                };
            });
        }
    })).then(recs => callback(null, { records: recs }));
};
