from __future__ import print_function

from aws_kinesis_agg.deaggregator import deaggregate_record
import base64


def construct_response_record(record_id, data, is_parse_success):
    return {
        'recordId': record_id,
        'result': 'Ok' if is_parse_success else 'ProcessingFailed',
        'data': base64.b64encode(data)}


def process_kpl_record(kpl_record):
    raw_kpl_record_data = base64.b64decode(kpl_record['data'])
    try:
        # Concatenate the data from de-aggregated records into a single output payload.
        output_data = "".join(deaggregate_record(raw_kpl_record_data))
        return construct_response_record(kpl_record['recordId'], output_data, True)
    except BaseException as e:
        print('Processing failed with exception:' + str(e))
        return construct_response_record(kpl_record['recordId'], raw_kpl_record_data, False)


def lambda_handler(event, context):
    '''A Python AWS Lambda function to process aggregated records sent to KinesisAnalytics.'''
    raw_kpl_records = event['records']
    output = [process_kpl_record(kpl_record) for kpl_record in raw_kpl_records]

    # Print number of successful and failed records.
    success_count = sum(1 for record in output if record['result'] == 'Ok')
    failure_count = sum(1 for record in output if record['result'] == 'ProcessingFailed')
    print('Processing completed.  Successful records: {0}, Failed records: {1}.'.format(success_count, failure_count))

    return {'records': output}
