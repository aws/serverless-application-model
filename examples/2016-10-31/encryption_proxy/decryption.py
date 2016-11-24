import boto3
import json
import base64

kms = boto3.client('kms')
bad_request = {
    'error': 'Invalid argument'
}


def decrypt(message):
    '''decrypt leverages KMS decrypt and base64-encode decrypted blob

        More info on KMS decrypt API:
        https://docs.aws.amazon.com/kms/latest/APIReference/API_decrypt.html
    '''
    try:
        encrypted_data = json.loads(message)
        ret = kms.decrypt(
            CiphertextBlob=base64.decodestring(encrypted_data['data']))
        decrypted_data = ret.get('Plaintext')
    except Exception as e:
        raise ("Unable to encrypt data.", e)

    return decrypted_data


def post(event, context):

    try:
        if event['body'] is None:
            raise Exception(
                "Nothing to decrypt or request didn't come through API")
        message = event['body']
    except:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(bad_request)
        }

    decrypted_message = decrypt(message)
    response = {'data': decrypted_message}

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(response)
    }
