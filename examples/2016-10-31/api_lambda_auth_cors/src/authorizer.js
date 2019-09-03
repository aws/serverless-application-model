// adapted from ../../api_lambda_token_auth/src/authorizer.js

exports.handler = async function (event) {
  const token = event.authorizationToken.toLowerCase();
  const methodArn = event.methodArn;

  switch (token) {
    case 'allow':
      // allow the request
      return generateAuthResponse('user123', 'Allow', methodArn);
    case 'deny':
      // return a 403
      return generateAuthResponse('user123', 'Deny', methodArn);
    default:
      // return a 500
      return Promise.reject('Error: Invalid token');
  }
};

/**
 * NOTE: the authorizer caches policies by default across all methods and resources in a stage.
 * If you are exposing more than one method or resource protected by the same authorizer, you may
 * not want to use event.methodArn.
 *
 * If a caller uses the same, valid token to access two URLs, the first call will be successful
 * but the second will fail because the cached policy only contains the ARN of the first method.
 */
function generateAuthResponse(principalId, effect, methodArn) {
  if (!effect || !methodArn) return null;

  return {
    principalId,
    policyDocument: {
      Version: '2012-10-17',
      Statement: [
        {
          Action: 'execute-api:Invoke',
          Effect: effect,
          Resource: methodArn
        }
      ]
    }
  };
}
