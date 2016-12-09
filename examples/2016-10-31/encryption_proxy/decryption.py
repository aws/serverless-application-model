import boto3
import json
import base64

kms = boto3.client('kms')
bad_request = {
    'statusCode': 400,
    'headers': {
        'Content-Type': 'application/json'
    },
    'body': json.dumps({'error': 'Invalid argument'})
}


def decrypt(message):
    '''decrypt leverages KMS decrypt and base64-encode decrypted blob

        More info on KMS decrypt API:
        https://docs.aws.amazon.com/kms/latest/APIReference/API_decrypt.html
    '''
    try:
        ret = kms.decrypt(
            CiphertextBlob=base64.decodestring(message))
        decrypted_data = ret.get('Plaintext')
    except Exception as e:
        # returns http 500 back to user and log error details in Cloudwatch Logs
        raise Exception("Unable to decrypt data: ", e)

    return decrypted_data


def post(event, context):

    try:
        payload = json.loads(event['body'])
        message = payload['data']
    except (KeyError, TypeError, ValueError):
        return bad_request

    decrypted_message = decrypt(message)
    response = {'data': decrypted_message}

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(response)
    }
