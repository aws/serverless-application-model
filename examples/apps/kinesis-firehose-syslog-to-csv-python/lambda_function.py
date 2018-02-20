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

        regex_string = (r"^((?:\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?"
                        r"|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b\s+(?:(?:0[1-9])|(?:[12][0-9])|(?:3[01])|[1-9])\s+"
                        r"(?:(?:2[0123]|[01]?[0-9]):(?:[0-5][0-9]):(?:(?:[0-5]?[0-9]|60)(?:[:\.,][0-9]+)?)))) (?:<(?:[0-9]+).(?:[0-9]+)> )"
                        r"?((?:[a-zA-Z0-9._-]+)) ([\w\._/%-]+)(?:\[((?:[1-9][0-9]*))\])?: (.*)")
        p = re.compile(regex_string)
        m = p.match(payload)

        def str_or_null(s):
            return s or 'null'

        if m:
            succeeded_record_cnt += 1
            output_payload = m.group(1) + ',' + m.group(2) + ',' + m.group(3) + ',' + str_or_null(m.group(4)) + ',' + m.group(5) + '\n'
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
