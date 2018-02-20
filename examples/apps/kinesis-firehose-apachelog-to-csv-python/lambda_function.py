from __future__ import print_function

import base64
import re

print('Loading function')


def lambda_handler(event, context):
    output = []
    succeeded_record_cnt = 0
    failed_record_cnt = 0

    for record in event['records']:
        print(record['recordId'])
        payload = base64.b64decode(record['data'])

        p = re.compile(r"^([\d.]+) (\S+) (\S+) \[([\w:/]+\s[\+\-]\d{4})\] \"(.+?)\" (\d{3}) (\d+)")
        m = p.match(payload)
        if m:
            succeeded_record_cnt += 1
            output_payload = m.group(1) + ',' + m.group(2) + ',' + m.group(3) + ',' + m.group(4) + ',' + m.group(5) + ',' + m.group(6) + ',' + m.group(7) + '\n'
            output_record = {
                'recordId': record['recordId'],
                'result': 'Ok',
                'data': base64.b64encode(output_payload)
            }
        else:
            print('Parsing failed')
            failed_record_cnt += 1
            output_record = {
                'recordId': record['recordId'],
                'result': 'ProcessingFailed',
                'data': record['data']
            }

        output.append(output_record)

    print('Processing completed.  Successful records {}, Failed records {}.'.format(succeeded_record_cnt, failed_record_cnt))
    return {'records': output}
