### Encryption/Decryption Proxy

This template creates the following resources:

* 2 Lambda functions (Encryption, Decryption)
    - SAM takes care of creating 2 stages API Gateway {Stage,Prod} that sits on top
* IAM Role for each function
* KMS Key and KMS Decrypt/Encrypt permissions for each IAM Role separately
    - KMS Key ID is then passed to Encryption Lambda via Env vars


#### How to launch it

Firstly, you need to package both functions locally to S3 via the following command:


```bash
aws cloudformation package --template template.yaml --s3-bucket <s3_bucket> --output-template packaged-template.yaml --region <aws_region>
```

Once complete, you should be ready to deploy it as a cloudformation stack:

```bash
aws cloudformation deploy --template packaged-template.yaml --stack-name encryption-proxy --capabilities CAPABILITY_IAM -- region <aws_region>
```

**Note**: S3 bucket must reside in the same region you are launching this stack to.

---

#### Encrypt Action

* Consumes up to 4KB of data (string, json blob, etc.)
* Returns encrypted data via JSON blob as follows

```javascript
{
    "data": "base64_encrypted_blob"
}
```

##### Encrypting data via cURL

```bash
encryptURL=$(aws cloudformation describe-stacks --stack-name encryption-proxy --query 'Stacks[].Outputs[?OutputKey==`EncryptURL`].OutputValue' --output text)

curl -H "Content-Type: application/json" -X POST -d "Here's my super secret data..." ${encryptURL}
```

#### Decrypt Action

* Consumes JSON blob received out of Encryption Action
* Returns decrypted data via JSON blob as follows

```javascript
{
    "data": "decrypted_data"
}
```

##### Decrypting data via cURL

```bash
decryptURL=$(aws cloudformation describe-stacks --stack-name encryption-proxy --query 'Stacks[].Outputs[?OutputKey==`DecryptURL`].OutputValue' --output text)

curl -H "Content-Type: application/json" -X POST -d "{ 'data': 'AQECAHjgf/RDFTAO0+ief3VXaJRnnKbyaaEsVhkmYxTcbiNhcgAAAHIwcAYJKoZIhvcNAQcGoGMw\nYQIBADBcBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDBX7iv8CwG1gr2Hc4wIBEIAvS1cXraMW\n3PU96z4AACGj7Wuo007HwWjtK/quSi3FKyYFvkJ10YhDOEvzxOD7Ntw=\n' }" ${decryptURL}
```
