'use strict';
console.log('Loading function');

exports.handler = (event, context, callback) => {
    /*Print streams as source only data here*/
    event.records.forEach((record) => {
        console.log(record.kinesisRecordMetadata.sequenceNumber);
        console.log(record.kinesisRecordMetadata.subsequenceNumber);
        console.log(record.kinesisRecordMetadata.partitionKey);
        console.log(record.kinesisRecordMetadata.shardId);
        console.log(record.kinesisRecordMetadata.approximateArrivalTimestamp);
    });
    /* Process the list of records and transform them */
    const output = event.records.map((record) => ({
        /* This transformation is the "identity" transformation, the data is left intact */
        recordId: record.recordId,
        result: 'Ok',
        data: record.data,
    }));
    console.log(`Processing completed.  Successful records ${output.length}.`);
    callback(null, { records: output });
};
