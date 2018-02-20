from __future__ import print_function

import base64
import json
import re
from dateutil.parser import parse
from datetime import datetime, tzinfo, timedelta

print('Loading function')


class UTC(tzinfo):
    """UTC"""

    def utcoffset(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return timedelta(0)

utc = UTC()


def lambda_handler(event, context):
    output = []
    succeeded_record_cnt = 0
    failed_record_cnt = 0

    safe_string_to_int = lambda x: int(x) if x.isdigit() else x

    for record in event['records']:
        print(record['recordId'])
        payload = base64.b64decode(record['data'])
        p = re.compile(r"^([\d.]+) (\S+) (\S+) \[([\w:/]+)(\s[\+\-]\d{4}){0,1}\] \"(.+?)\" (\d{3}) (\d+)")
        m = p.match(payload)
        if m:
            succeeded_record_cnt += 1

            ts = m.group(4)
            try:
                d = parse(ts.replace(':', ' ', 1))
                ts = d.isoformat()
            except:
                print('Parsing the timestamp to date failed.')

            data_field = {
                'host': m.group(1),
                'ident': m.group(2),
                'authuser': m.group(3),
                '@timestamp': ts,
                'request': m.group(6),
                'response': safe_string_to_int(m.group(7)),
                'bytes': safe_string_to_int(m.group(8))
            }

            if m.group(6) and len(m.group(6).split()) > 1:
                data_field['verb'] = m.group(6).split()[0]

            # If time offset is present, add the timezone and @timestamp_utc fields
            if m.group(5):
                data_field['timezone'] = m.group(5).strip()
                try:
                    ts_with_offset = m.group(4) + m.group(5)
                    d = parse(ts_with_offset.replace(':', ' ', 1))
                    utc_d = d.astimezone(utc)
                    data_field['@timestamp_utc'] = utc_d.isoformat()
                except:
                    print('Calculating UTC time failed.')

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
