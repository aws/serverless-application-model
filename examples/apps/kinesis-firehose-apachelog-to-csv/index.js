'use strict';
console.log('Loading function');

/* Apache Log format parser */
const parser = /^([\d.]+) (\S+) (\S+) \[([\w:/]+\s[\+\-]\d{4})\] "(.+?)" (\d{3}) (\d+)/;

exports.handler = (event, context, callback) => {
    let success = 0; // Number of valid entries found
    let failure = 0; // Number of invalid entries found

    /* Process the list of records and transform them */
    const output = event.records.map((record) => {
        const entry = (Buffer.from(record.data, 'base64')).toString('utf8');
        const match = parser.exec(entry);
        if (match) {
            /* Prepare CSV version from Apache log data */
            const result = `${match[1]},${match[2]},${match[3]},${match[4]},${match[5]},${match[6]},${match[7]}\n`;
            const payload = (Buffer.from(result, 'utf8')).toString('base64');
            success++;
            return {
                recordId: record.recordId,
                result: 'Ok',
                data: payload,
            };
        } else {
            /* Failed event, notify the error and leave the record intact */
            failure++;
            return {
                recordId: record.recordId,
                result: 'ProcessingFailed',
                data: record.data,
            };
        }
    });
    console.log(`Processing completed.  Successful records ${success}, Failed records ${failure}.`);
    callback(null, { records: output });
};
