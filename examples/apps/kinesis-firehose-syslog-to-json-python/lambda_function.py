from __future__ import print_function

import base64
import json
import re

print('Loading function')


def lambda_handler(event, context):
    output = []
    succeeded_record_cnt = 0
    failed_record_cnt = 0

    for record in event['records']:
        print(record['recordId'])
        payload = base64.b64decode(record['data'])

        regex_string = (r"^((?:\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?"
                        r"|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b\s+(?:(?:0[1-9])|(?:[12][0-9])|(?:3[01])|[1-9])\s+"
                        r"(?:(?:2[0123]|[01]?[0-9]):(?:[0-5][0-9]):(?:(?:[0-5]?[0-9]|60)(?:[:\.,][0-9]+)?)))) (?:<(?:[0-9]+).(?:[0-9]+)> )"
                        r"?((?:[a-zA-Z0-9._-]+)) ([\w\._/%-]+)(?:\[((?:[1-9][0-9]*))\])?: (.*)")
        p = re.compile(regex_string)
        m = p.match(payload)
        if m:
            succeeded_record_cnt += 1
            data_field = {
                'timestamp': m.group(1),
                'hostname': m.group(2),
                'program': m.group(3),
                'processid': m.group(4),
                'message': m.group(5)
            }
            output_record = {
                'recordId': record['recordId'],
                'result': 'Ok',
                'data': base64.b64encode(json.dumps(data_field))
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
