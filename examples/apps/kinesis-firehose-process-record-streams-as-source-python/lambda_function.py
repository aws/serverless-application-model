from __future__ import print_function

import base64

print('Loading function')


def lambda_handler(event, context):
    output = []

    for record in event['records']:
        print(record['recordId'])
        payload = base64.b64decode(record['data'])
        print(record['recordId'])

        # Print stream as source only data here
        kinesisMetadata = record['kinesisRecordMetadata']
        print(kinesisMetadata['sequenceNumber'])
        print(kinesisMetadata['subsequenceNumber'])
        print(kinesisMetadata['partitionKey'])
        print(kinesisMetadata['shardId'])
        print(kinesisMetadata['approximateArrivalTimestamp'])

        # Do custom processing on the payload here
        output_record = {
            'recordId': record['recordId'],
            'result': 'Ok',
            'data': base64.b64encode(payload)
        }
        output.append(output_record)

    print('Successfully processed {} records.'.format(len(event['records'])))

    return {'records': output}
