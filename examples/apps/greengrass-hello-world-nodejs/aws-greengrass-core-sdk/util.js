/*
 * Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
 */

const base64Regex = /^([0-9a-zA-Z+/]{4})*(([0-9a-zA-Z+/]{2}==)|([0-9a-zA-Z+/]{3}=))?$/;
const qualifierRegex = /(|[a-zA-Z0-9$_-]+)/;

exports.getRequiredParameter = function _getRequiredParameter(params, requiredParam) {
    if (!Object.prototype.hasOwnProperty.call(params, requiredParam)) {
        return;
    }
    return params[requiredParam];
};

exports.isValidJSON = function _isValidJSON(str) {
    try {
        JSON.parse(str);
    } catch (e) {
        return false;
    }
    return true;
};

exports.isValidContext = function _isValidContext(context) {
    if (!base64Regex.test(context)) {
        return false;
    }
    try {
        JSON.stringify(context);
    } catch (e) {
        return false;
    }
    return true;
};

exports.isValidQualifier = function _isValidQualifier(qualifier) {
    if (!qualifierRegex.test(qualifier)) {
        return false;
    }
    return true;
};
