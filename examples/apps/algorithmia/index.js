/**
 * Algorithmia Lambda Function
 *
 * Calls any algorithm in the Algorithmia marketplace
 * Get an API key and free credits by creating an account at algorithmia.com
 * For more documentation see: algorithmia.com/docs/clients/lambda
 *
 *
 * Follow these steps to encrypt your Algorithmia API Key for use in this function:
 *
 * 1. Create a KMS key - http://docs.aws.amazon.com/kms/latest/developerguide/create-keys.html
 *
 * 2. Encrypt the event collector token using the AWS CLI
 *      aws kms encrypt --key-id alias/<KMS key name> --plaintext "<ALGORITHMIA_API_KEY>"
 *
 * 3. Copy the base-64 encoded, encrypted key (CiphertextBlob) to the kmsEncryptedApiKey variable
 *
 * 4. Give your function's role permission for the kms:Decrypt action.
 * Example:

{
    "Version": "2012-10-17",
    "Statement": [
    {
        "Sid": "Stmt1443036478000",
        "Effect": "Allow",
        "Action": [
            "kms:Decrypt"
            ],
        "Resource": [
            "<your KMS key ARN>"
            ]
    }
    ]
}
 */
'use strict';

const algorithmia = require('algorithmia');
const AWS = require('aws-sdk');

let apiKey;

// Enter the base-64 encoded, encrypted key (CiphertextBlob)
const kmsEncryptedApiKey = '<kmsEncryptedApiKey>';

/*
 * Configure your function to interact
*/
const processEvent = (event, context) => {
    /*
     * Step 1: Set the algorithm you want to call
     *  This may be any algorithm in the Algorithmia marketplace
    */
    const algorithm = 'algo://demo/Hello'; // algorithmia.com/algorithms/demo/Hello

    /*
     * Step 2: Use your event source to set inputData according to the algorithm's input format
     *         This demo example uses the S3 Object's name as inputData
     */
    const inputData = event.Records[0].s3.object.key; // Example for algo://demo/Hello

    /*  Advanced example:
     *      Create 200x50 thumbnails for S3 file events using algo://opencv/SmartThumbnail
     *          Algorithm expects input as [URL, WIDTH, HEIGHT]
     *          Output is a base64 encoding of the resulting PNG thumbnail
     *
     *      var algorithm = "algo://opencv/SmartThumbnail"
     *      var s3 = new AWS.S3();
     *      var bucket = event.Records[0].s3.bucket.name;
     *      var key = decodeURIComponent(event.Records[0].s3.object.key.replace(/\+/g, " ")) ;
     *      var params = {Bucket: bucket, Key: key};
     *      var signedUrl = s3.getSignedUrl('getObject', params);
     *      var inputData = [signedUrl, 200, 50];
     */

    // Run the algorithm
    const client = algorithmia(apiKey);
    client.algo(algorithm).pipe(inputData).then((output) => {
        if (output.error) {
            console.log(`Error: ${output.error.message}`);
            context.fail(output.error.message);
        } else {
            /*
             * Step 3: Process the algorithm output here
             *         This demo example prints and succeeds with the algorithm result
             */
            console.log(output);
            context.succeed(output.result);
        }
    });
};

/*
 * This is the lambda entrypoint (no modification necessary)
 *   it ensures apiKey is set (decrypting kmsEncryptedApiKey if provided)
 *   and then calls processEvent with the same event and context
 */
exports.handler = (event, context) => {
    if (kmsEncryptedApiKey && kmsEncryptedApiKey !== '<kmsEncryptedApiKey>') {
        const encryptedBuf = new Buffer(kmsEncryptedApiKey, 'base64');
        const cipherText = { CiphertextBlob: encryptedBuf };

        const kms = new AWS.KMS();
        kms.decrypt(cipherText, (err, data) => {
            if (err) {
                console.log(`Decrypt error: ${err}`);
                context.fail(err);
            } else {
                apiKey = data.Plaintext.toString('ascii');
                processEvent(event, context);
            }
        });
    } else if (apiKey) {
        processEvent(event, context);
    } else {
        context.fail('API Key has not been set.');
    }
};

