/*
 This blueprint helps in transitioning Node.js v0.10 functions. It can be run in three modes:
  - List: to list all existing Node.js v0.10 functions and their versions in the current region
  - Backup: to publish a version of your current deprecated functions $LATEST version.
  - Upgrade: to upgrade the runtime field of existing Node.js v0.10 functions $LATEST version from ‘nodejs’ to
   ‘node.js4.3’ or ‘node.js6.10’

 Notes:
  - IMPORTANT: This blueprint only upgrades the runtime value of your nodejs v0.10 functions, you should test your
 functions to make sure they behave as expected when operating in the new runtime environment.
  - Creating Node.js v0.10 functions has been turned off since January 2017. When run in Backup mode, this blueprint
 will publish a version of the existing code and configuration of your function. When run in Upgrade mode this
 blueprint will upgrade the value of the runtime of $LATEST version of your function. You can point clients of your
 existing function to the backup version if required while you work on validating the upgrade.
  - If a function fails to backup or upgrade, this Lambda execution will stop and logs will be available in Cloud
 Watch for debugging.
  - If you have a large number of functions in your account, this function may take multiple invokes to upgrade your
 functions.
  - If you receive this error message: "The role defined for the function cannot be assumed by Lambda.", please
 confirm that the function being upgraded has a correct execution role value and that role exists in IAM. Try
 running this blueprint again after the error has been corrected.
  - This blueprint is able to upgrade runtimes for the $LATEST version only. Please follow instructions in the
 documentation to transition other versions.

 Usage:
 1. Create a function using this blueprint.  The functions role should have listFunctions and
 updateFunctionConfiguration privileges in its execution role.
 2. To list all existing Node.js v0.10 functions and their versions in the current region, run the function without any
 change from the console. This displays the functions and versions as a json list both in the output pane on the console
 as well as Cloudwatch logs.
 3. To publish backup versions of your listed functions before upgrading them, make the following changes to the
 function's configuration:
  a. Change the MODE environment variable's value to Backup.
  b. Running this blueprint multiple times in backup mode will add multiple backups to your functions.
 4. To upgrade the runtime field of the listed functions to a newer value, make the following changes to the function’s
 configuration:
  a. Change the MODE environment variable’s value to Upgrade.
  b. Change the TARGET_RUNTIME environment variable’s value to the runtime that you’d like to transition to. Valid
   values are nodejs6.10 || nodejs8.10.
  c. Change the EXCEPTIONS environment variable’s value to a list of function names to exclude them from being
   upgraded. The value should be a comma separated list of function names alone, not ARNs.
  d. Run the function from the console.
 5. Repeat step 4 multiple times if you have a lot of functions that need to be upgraded.
 6. Repeat steps 1-5 for all regions you have Lambda functions in.
 */

'use strict';

const AWS = require('aws-sdk');
const throat = require('throat');

const lambda = new AWS.Lambda();
exports.handler = (event, context, callback) => {
    const memory = { Functions: [], Versions: [] };
    const deprecatedRuntime = 'nodejs';
    const targetRuntime = process.env.TARGET_RUNTIME || 'nodejs6.10';
    const mode = (process.env.MODE || 'list').toLowerCase();
    const list = mode === 'list';
    const upgrade = mode === 'upgrade';
    const backup = mode === 'backup';
    const exceptions = process.env.EXCEPTIONS ? process.env.EXCEPTIONS.split(',') : [];
    console.log(`Blueprint Deprecated Runtime set to ${deprecatedRuntime}`);
    console.log(`Blueprint TARGET_RUNTIME set to ${targetRuntime}`);
    console.log(`Blueprint MODE set to ${process.env.MODE}`);
    console.log(`Blueprint EXCEPTIONS set to ${process.env.EXCEPTIONS}`);

    function report() {
        const formatExample = { DeprecatedFunctionName: ['DeprecatedVersion1', 'DeprecatedVersion2'] };
        const functionNames = memory.Functions.map((fn) => {
            const obj = {};
            obj[`${fn.FunctionName}`] = JSON.stringify(memory.Versions.filter(vs => vs.FunctionName === `${fn.FunctionName}`).map(vs => vs.Version));
            return obj;
        });
        if (functionNames.length) {
            functionNames.unshift(formatExample);
            console.log('Printing deprecated functions and their corresponding deprecated versions.' +
                'The following functions runtimes will be upgraded. Example format: ', functionNames);
        } else {
            console.log('No deprecated functions found.');
        }
    }

    function backupFunctions(functions) {
        return Promise.all(functions.map(throat(1, (fn) => {
            console.log(`Starting backup of function ${fn}`);
            const params = {
                FunctionName: fn,
                Description: 'Node 0.10 Deprecation Blueprint Backup',
            };
            return lambda.publishVersion(params).promise();
        })));
    }

    function upgradeFunctions(functions) {
        return Promise.all(functions.map(throat(1, (fn) => {
            console.log(`Starting runtime upgrade of function ${fn}`);
            const params = {
                FunctionName: fn,
                Runtime: targetRuntime,
            };
            return lambda.updateFunctionConfiguration(params).promise();
        })));
    }

    function getVersions(functions) {
        return Promise.all(functions.map(throat(1, (fn) => {
            const params = {
                FunctionName: fn,
            };
            return lambda.listVersionsByFunction(params).promise();
        })));
    }

    function getFunctions(params) {
        lambda.listFunctions(params, (err, data) => {
            if (err) {
                callback(err, err.stack);
            } else {
                Array.prototype.push.apply(memory.Functions, data.Functions.filter((item) => item.Runtime === deprecatedRuntime &&
                exceptions.indexOf(item.FunctionName) === -1));
                if (data.NextMarker) {
                    const nextListFunctionsParams = {
                        Marker: data.NextMarker,
                        MaxItems: 50,
                    };
                    setTimeout(() => getFunctions(nextListFunctionsParams), 100);
                } else {
                    // retrieved all functions
                    console.log(`Total deprecated functions retreived: ${memory.Functions.length}`);
                    getVersions(memory.Functions.map(fn => fn.FunctionName)).then((versions) => {
                        memory.Versions = versions;
                        if (list) {
                            report();
                            console.log('Report Complete.');
                        } else if (backup) {
                            console.log(`Starting Function Backup Operation for ${memory.Functions.length} deprecated functions.`);
                            backupFunctions(memory.Functions.map(fn => fn.FunctionName))
                                .then(() => {
                                    console.log('Function Backup Operation Complete.  See CloudWatch logs for Errors' +
                                        ' that may have occurred.');
                                })
                                .catch((error) => {
                                    console.log(error);
                                });
                        } else if (upgrade) {
                            console.log(`Starting Function Upgrade Operation for ${memory.Functions.length} deprecated functions.`);
                            upgradeFunctions(memory.Functions.map(fn => fn.FunctionName))
                                .then(() => {
                                    console.log('Function Upgrade Operation Complete.  See CloudWatch logs for Errors' +
                                        ' that may have occurred.');
                                })
                                .catch((error) => {
                                    console.log(error);
                                });
                        } else {
                            console.log('no MODE environment variable specified.');
                        }
                    });
                }
            }
        });
    }
    const starterParams = {
        MaxItems: 50,
    };
    getFunctions(starterParams);
};
