'use strict';

const AWS = require('aws-sdk');

// Update the emailDomain environment variable to the correct domain, e.g. <MYDOMAIN>.com
const emailDomain = process.env.emailDomain;

exports.handler = (event, context, callback) => {
    console.log('Spam filter starting');

    const sesNotification = event.Records[0].ses;
    const messageId = sesNotification.mail.messageId;
    const receipt = sesNotification.receipt;

    console.log('Processing message:', messageId);

    // Check if any spam check failed
    if (receipt.spfVerdict.status === 'FAIL' ||
            receipt.dkimVerdict.status === 'FAIL' ||
            receipt.spamVerdict.status === 'FAIL' ||
            receipt.virusVerdict.status === 'FAIL') {
        const sendBounceParams = {
            BounceSender: `mailer-daemon@${emailDomain}`,
            OriginalMessageId: messageId,
            MessageDsn: {
                ReportingMta: `dns; ${emailDomain}`,
                ArrivalDate: new Date(),
                ExtensionFields: [],
            },
            BouncedRecipientInfoList: receipt.recipients.map((recipient) => ({
                Recipient: recipient,
                BounceType: 'ContentRejected',
            })),
        };

        console.log('Bouncing message with parameters:');
        console.log(JSON.stringify(sendBounceParams, null, 2));

        new AWS.SES().sendBounce(sendBounceParams, (err, data) => {
            if (err) {
                console.log(`An error occurred while sending bounce for message: ${messageId}`, err);
                callback(err);
            } else {
                console.log(`Bounce for message ${messageId} sent, bounce message ID: ${data.MessageId}`);
                callback(null, {
                    disposition: 'stop_rule_set',
                });
            }
        });
    } else {
        console.log('Accepting message:', messageId);
        callback();
    }
};
