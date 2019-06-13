/*
** Adapted from https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-use-lambda-authorizer.html#api-gateway-lambda-authorizer-token-lambda-function-create
** A simple TOKEN authorizer example to demonstrate how to use an authorization token
** to allow or deny a request.In this example, the caller named 'user'is allowed to invoke
** a request if the client - supplied token value is 'allow'.The caller is not allowed to
** invoke the request if the token value is 'deny'.If the token value is 'Unauthorized',
** the function returns the 'Unauthorized' error with an HTTP status code of 401. For any
** other token value, the authorizer returns 'Error: Invalid token' as a 500 error.
*/

exports.handler = async function (event) {
  const token = event.authorizationToken.toLowerCase()
  const methodArn = event.methodArn

  switch (token) {
    case 'allow':
      return generateAuthResponse('user', 'Allow', methodArn)
    case 'deny':
      return generateAuthResponse('user', 'Deny', methodArn)
    default:
      return Promise.reject('Error: Invalid token') // Returns 500 Internal Server Error
  }
}

function generateAuthResponse (principalId, effect, methodArn) {
  // If you need to provide additional information to your integration
  // endpoint (e.g. your Lambda Function), you can add it to `context`
  const context = {
    'stringKey': 'stringval',
    'numberKey': 123,
    'booleanKey': true
  }
  const policyDocument = generatePolicyDocument(effect, methodArn)

  return {
    principalId,
    context,
    policyDocument
  }
}

function generatePolicyDocument (effect, methodArn) {
  if (!effect || !methodArn) return null

  const policyDocument = {
    Version: '2012-10-17',
    Statement: [{
      Action: 'execute-api:Invoke',
      Effect: effect,
      Resource: methodArn
    }]
  }

  return policyDocument
}
