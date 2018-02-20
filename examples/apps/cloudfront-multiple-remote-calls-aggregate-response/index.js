'use strict';

const https = require('https');

/*
 * Makes multiple remote calls to fetch forecast for each of the city
 * mentioned in GET request from CloudFront/S3 and generates one aggregated
 * custom response for origin request event.
 *
 * The forecast details for each city are present in following S3 locations
 * as a text file.
 * https://cloudfront-blueprints.s3.amazonaws.com/blueprints/cities/{city}
 *
 * For lower latency, we use a CloudFront distribition with the S3 bucket
 * as an origin and fetch the forecast from the CloudFront cache of
 * the closest edge location.
 * https://d1itj4mrjr44ts.cloudfront.net/blueprints/cities/{city}
 */

function getCityForecast(request) {
    return new Promise((resolve, reject) => {
        https.get(request.uri, (response) => {
            let content = '';
            response.setEncoding('utf8');
            response.on('data', (chunk) => { content += chunk; });
            response.on('end', () => resolve({ city: request.city, forecast: content }));
        }).on('error', e => reject(e));
    });
}

exports.handler = (event, context, callback) => {
    const request = event.Records[0].cf.request;
    const citiesBaseUri = 'https://d1itj4mrjr44ts.cloudfront.net/blueprints/cities/';
    const uri = request.uri;

    console.log('Requested URI: ', uri);

    if (!uri.match('^/forecast/')) {
        /* Not a forecast request, continue */
        callback(null, request);
    } else {       /* Forecast request*/
        /* Forcast format: /forecast/City1:City2:City3:City4 */
        const uriSplit = uri.split('/');

        /* 0 is the host, 1 is 'forecast', the cities are in index 2 */
        const cities = uriSplit[2].split(':');

        /* List to maintain forecast uri of individual city */
        const forecasts = [];

        cities.forEach((cityName) => {
            const cityForecastUri = citiesBaseUri + cityName;
            forecasts.push({ city: cityName, uri: cityForecastUri });
        });

        /* Get forecast for requested cities */
        console.log('Getting forecasts for: ', forecasts);

        Promise.all(forecasts.map(getCityForecast)).then((ret) => {
            console.log('Aggregating the responses:\n', ret);
            const response = {
                status: '200',  /* Status signals this is a generated response */
                statusDescription: 'OK',
                headers: {
                    'cache-control': [{
                        key: 'Cache-Control',
                        value: 'max-age=60',
                    }],
                    'content-type': [{
                        key: 'Content-Type',
                        value: 'application/json',
                    }],
                    'content-encoding': [{
                        key: 'Content-Encoding',
                        value: 'UTF-8',
                    }],
                },
                body: JSON.stringify(ret, null, '\t'),
            };

            console.log('Generated response: ', JSON.stringify(response));
            callback(null, response);
        });
    }
};
