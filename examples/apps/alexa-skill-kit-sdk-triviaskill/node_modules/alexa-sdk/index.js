var AlexaLambdaHandler = require('./lib/alexa');

module.exports.handler = AlexaLambdaHandler.LambdaHandler;
module.exports.CreateStateHandler = AlexaLambdaHandler.CreateStateHandler;
module.exports.StateString = AlexaLambdaHandler.StateString;