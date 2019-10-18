/*
 * Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 */
const Buffer = require('buffer').Buffer;

const Lambda = require('./lambda');
const Util = require('./util');
const GreengrassCommon = require('aws-greengrass-common-js');

const KEY_SECRET_ID = 'SecretId';
const KEY_VERSION_ID = 'VersionId';
const KEY_VERSION_STAGE = 'VersionStage';
const KEY_SECRET_ARN = 'ARN';
const KEY_SECRET_NAME = 'Name';
const KEY_CREATED_DATE = 'CreatedDate';

const envVars = GreengrassCommon.envVars;
const SECRETS_MANAGER_FUNCTION_ARN = envVars.SECRETS_MANAGER_FUNCTION_ARN;

class SecretsManager {
    constructor() {
        this.lambda = new Lambda();
    }

    getSecretValue(params, callback) {
        const secretId = Util.getRequiredParameter(params, KEY_SECRET_ID);
        const versionId = Util.getRequiredParameter(params, KEY_VERSION_ID);
        const versionStage = Util.getRequiredParameter(params, KEY_VERSION_STAGE);

        if (secretId === undefined) {
            callback(new Error(`"${KEY_SECRET_ID}" is a required parameter`), null);
            return;
        }
        // TODO: Remove this once we support query by VersionId
        if (versionId !== undefined) {
            callback(new Error('Query by VersionId is not yet supported'), null);
            return;
        }
        if (versionId !== undefined && versionStage !== undefined) {
            callback(new Error('VersionId and VersionStage cannot both be specified at the same time'), null);
            return;
        }

        const getSecretValueRequestBytes =
            SecretsManager._generateGetSecretValueRequestBytes(secretId, versionId, versionStage);

        const invokeParams = {
            FunctionName: SECRETS_MANAGER_FUNCTION_ARN,
            Payload: getSecretValueRequestBytes,
        };

        console.log(`Getting secret value from secrets manager: ${getSecretValueRequestBytes}`);

        this.lambda.invoke(invokeParams, (err, data) => {
            if (err) {
                callback(err, null);                                        // an error occurred
            } else if (SecretsManager._is200Response(data.Payload)) {
                callback(null, data.Payload);                               // successful response
            } else {
                callback(new Error(JSON.stringify(data.Payload)), null);    // error response
            }
        });
    }

    static _generateGetSecretValueRequestBytes(secretId, versionId, versionStage) {
        const request = {
            SecretId: secretId,
        };

        if (versionStage !== undefined) {
            request.VersionStage = versionStage;
        }

        if (versionId !== undefined) {
            request.VersionId = versionId;
        }

        return Buffer.from(JSON.stringify(request));
    }

    static _is200Response(payload) {
        const hasSecretArn = this._stringContains(payload, KEY_SECRET_ARN);
        const hasSecretName = this._stringContains(payload, KEY_SECRET_NAME);
        const hasVersionId = this._stringContains(payload, KEY_VERSION_ID);
        const hasCreatedDate = this._stringContains(payload, KEY_CREATED_DATE);

        return hasSecretArn && hasSecretName && hasVersionId && hasCreatedDate;
    }

    static _stringContains(src, target) {
        return src.indexOf(target) > -1;
    }
}

module.exports = SecretsManager;
