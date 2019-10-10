/*
 * Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 */

const Util = require('./util');
const IPCClient = require('aws-greengrass-ipc-sdk-js');
const GreengrassCommon = require('aws-greengrass-common-js');
const logging = require('aws-greengrass-common-js').logging;

const AUTH_TOKEN = GreengrassCommon.envVars.AUTH_TOKEN;

const logger = new logging.LocalWatchLogger();

class Lambda {
    constructor() {
        this.ipc = new IPCClient(AUTH_TOKEN);
    }

    invoke(params, callback) {
        const functionName = Util.getRequiredParameter(params, 'FunctionName');
        if (functionName === undefined) {
            callback(new Error('"FunctionName" is a required parameter'), null);
            return;
        }

        let arnFields;
        try {
            arnFields = new GreengrassCommon.FunctionArnFields(functionName);
        } catch (e) {
            callback(new Error(`FunctionName is malformed: ${e}`), null);
            return;
        }

        let invocationType;
        if (params.InvocationType === undefined || params.InvocationType === null) {
            invocationType = 'RequestResponse';
        } else {
            invocationType = params.InvocationType;
        }

        if (invocationType !== 'Event' && invocationType !== 'RequestResponse') {
            callback(new Error(`InvocationType '${invocationType}' is incorrect, should be 'Event' or 'RequestResponse'`), null);
            return;
        }

        const clientContext = params.ClientContext ? params.ClientContext : '';
        const payload = params.Payload;
        const qualifier = params.Qualifier;

        if (!Util.isValidQualifier(qualifier)) {
            callback(new Error(`Qualifier '${qualifier}' is incorrect`), null);
            return;
        }

        const qualifierInternal = arnFields.qualifier;

        // generate the right full function arn with qualifier
        if (qualifierInternal && qualifier && qualifierInternal !== qualifier) {
            callback(new Error(`Qualifier '${qualifier}' does not match the version in FunctionName`), null);
            return;
        }

        const finalQualifier = qualifierInternal === undefined || qualifierInternal == null ? qualifier : qualifierInternal;

        let functionArn;
        if (typeof GreengrassCommon.buildFunctionArn === 'function') {
            // GGC v1.9.0 or newer
            functionArn = GreengrassCommon.buildFunctionArn(
                arnFields.unqualifiedArn,
                finalQualifier);
        } else {
            // older version of GGC
            throw new Error('Function buildFunctionArn not found. buildFunctionArn is introduced in GGC v1.9.0. ' +
                    'Please check your GGC version.');
        }

        // verify client context is base64 encoded
        if (Object.prototype.hasOwnProperty.call(params, 'ClientContext')) {
            const cxt = params.ClientContext;
            if (!Util.isValidContext(cxt)) {
                callback(new Error('Client Context is invalid'), null);
                return;
            }
        }

        logger.debug(`Invoking local lambda ${functionArn} with payload ${payload} and client context ${clientContext}`);

        this.ipc.postWork(functionArn, payload, clientContext, invocationType, (postWorkErr, invocationId) => {
            if (postWorkErr) {
                logger.error(`Failed to invoke function due to ${postWorkErr}`);
                callback(postWorkErr, null);
                return;
            }

            if (invocationType === 'RequestResponse') {
                this.ipc.getWorkResult(functionArn, invocationId, (getWorkResultErr, body, functionErr, statusCode) => {
                    if (getWorkResultErr) {
                        logger.error(`Failed to get work result due to ${getWorkResultErr}`);
                        callback(getWorkResultErr, null);
                        return;
                    }
                    const data = {
                        FunctionError: functionErr,
                        StatusCode: statusCode,
                        Payload: body,
                    };
                    callback(null, data);
                });
            } else {
                callback(null, invocationId);
            }
        });
    }
}

module.exports = Lambda;
