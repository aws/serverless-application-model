/*
 * Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 */

const Buffer = require('buffer').Buffer;

const Lambda = require('./lambda');
const Util = require('./util');
const GreengrassCommon = require('aws-greengrass-common-js');

const envVars = GreengrassCommon.envVars;
const MY_FUNCTION_ARN = envVars.MY_FUNCTION_ARN;
const SHADOW_FUNCTION_ARN = envVars.SHADOW_FUNCTION_ARN;
const ROUTER_FUNCTION_ARN = envVars.ROUTER_FUNCTION_ARN;

class IotData {
    constructor() {
        this.lambda = new Lambda();
    }

    getThingShadow(params, callback) {
        /*
         * Call shadow lambda to obtain current shadow state.
         * @param {object} params object contains parameters for the call
         * REQUIRED: 'thingName' the name of the thing
         */
        const thingName = Util.getRequiredParameter(params, 'thingName');
        if (thingName === undefined) {
            callback(new Error('"thingName" is a required parameter.'), null);
            return;
        }

        const payload = '';
        this._shadowOperation('get', thingName, payload, callback);
    }

    updateThingShadow(params, callback) {
        /*
         * Call shadow lambda to update current shadow state.
         * @param {object} params object contains parameters for the call
         * REQUIRED: 'thingName' the name of the thing
         *           'payload'   the state information in JSON format
         */
        const thingName = Util.getRequiredParameter(params, 'thingName');
        if (thingName === undefined) {
            callback(new Error('"thingName" is a required parameter.'), null);
            return;
        }

        const payload = Util.getRequiredParameter(params, 'payload');
        if (payload === undefined) {
            callback(new Error('"payload" is a required parameter.'), null);
            return;
        }

        this._shadowOperation('update', thingName, payload, callback);
    }

    deleteThingShadow(params, callback) {
        /*
         * Call shadow lambda to delete the shadow state.
         * @param {object} params object contains parameters for the call
         * REQUIRED: 'thingName' the name of the thing
         */
        const thingName = Util.getRequiredParameter(params, 'thingName');
        if (thingName === undefined) {
            callback(new Error('"thingName" is a required parameter.'), null);
            return;
        }

        const payload = '';
        this._shadowOperation('delete', thingName, payload, callback);
    }

    publish(params, callback) {
        /*
         * Publishes state information.
         * @param {object} params object contains parameters for the call
         * REQUIRED: 'topic'   the topic name to be published
         *           'payload' the state information in JSON format
         */
        const topic = Util.getRequiredParameter(params, 'topic');
        if (topic === undefined) {
            callback(new Error('"topic" is a required parameter'), null);
            return;
        }

        const payload = Util.getRequiredParameter(params, 'payload');
        if (payload === undefined) {
            callback(new Error('"payload" is a required parameter'), null);
            return;
        }

        const context = {
            custom: {
                source: MY_FUNCTION_ARN,
                subject: topic,
            },
        };

        const buff = Buffer.from(JSON.stringify(context));
        const clientContext = buff.toString('base64');

        const invokeParams = {
            FunctionName: ROUTER_FUNCTION_ARN,
            InvocationType: 'Event',
            ClientContext: clientContext,
            Payload: payload,
        };

        console.log(`Publishing message on topic "${topic}" with Payload "${payload}"`);

        this.lambda.invoke(invokeParams, (err, data) => {
            if (err) {
                callback(err, null);            // an error occurred
            } else {
                callback(null, data);           // successful response
            }
        });
    }

    _shadowOperation(operation, thingName, payload, callback) {
        const topic = `$aws/things/${thingName}/shadow/${operation}`;
        const context = {
            custom: {
                subject: topic,
            },
        };

        const clientContext = Buffer.from(JSON.stringify(context)).toString('base64');
        const invokeParams = {
            FunctionName: SHADOW_FUNCTION_ARN,
            ClientContext: clientContext,
            Payload: payload,
        };

        console.log(`Calling shadow service on topic "${topic}" with payload "${payload}"`);
        this.lambda.invoke(invokeParams, (err, data) => {
            if (err) {
                callback(err, null);
            } else {
                callback(null, data);
            }
        });
    }
}

module.exports = IotData;
