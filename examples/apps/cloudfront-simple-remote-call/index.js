'use strict';

const https = require('https');

exports.handler = (event, context, callback) => {
    const request = event.Records[0].cf.request;

    let username = 'Guest';
    if (request.headers['user-name']) {
        username = request.headers['user-name'][0].value;
    }
    console.log(`username = ${username}`);

    /*
     * Fetch the template from CloudFront/S3 and replace the
     * placeholder with a custom user name.
     *
     * The HTML template is stored in S3 bucket:
     * https://cloudfront-blueprints.s3.amazonaws.com/blueprints/template.html
     *
     * For lower latency, we use a CloudFront distribition with the S3 bucket
     * as an origin and fetch the template from the CloudFront cache of
     * the closest edge location.
     */
    const templateUrl = 'https://d1itj4mrjr44ts.cloudfront.net/blueprints/template.html';
    https.get(templateUrl, (res) => {
        let content = '';
        res.on('data', (chunk) => { content += chunk; });
        res.on('end', () => {
            content = content.replace(/{{user-name}}/ig, username);
            const response = {
                status: '200',
                statusDescription: 'OK',
                body: content,
                headers: {
                    vary: [{
                        key: 'Vary',
                        value: '*',
                    }],
                    'last-modified': [{
                        key: 'Last-Modified',
                        value: '2017-01-13',
                    }],
                },
            };
            console.log(`Generated response =  ${response.body}`);
            callback(null, response);
        });
    });
};
