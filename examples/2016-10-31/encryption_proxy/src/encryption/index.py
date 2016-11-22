import boto3
import json
import base64
import os

kms = boto3.client('kms')
bad_request = {
    'error': 'Invalid argument'
}


def encrypt(key, message):
    '''encrypt leverages KMS encrypt and base64-encode encrypted blob

        More info on KMS encrypt API:
        https://docs.aws.amazon.com/kms/latest/APIReference/API_encrypt.html
    '''
    try:
        ret = kms.encrypt(KeyId=key, Plaintext=message)
        encrypted_data = base64.encodestring(ret.get('CiphertextBlob'))
    except Exception as e:
        raise ("Unable to encrypt data.", e)

    return encrypted_data


def post(event, context):

    try:
        key_id = os.environ['keyId']
    except KeyError:
        raise Exception("KMS Key ID not found.")

    try:
        if event['body'] is None:
            raise Exception(
                "Nothing to encrypt or request didn't come through API")
        message = event['body']
    except:
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(bad_request)
        }

    encrypted_message = encrypt(key_id, message)
    response = {'data': encrypted_message}

    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps(response)
    }
