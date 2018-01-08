'use strict';
console.log('Loading hello world function');

exports.handler = function(event, context) {
  const response = {
    version: '1.0',
    response: {
      outputSpeech: {
        type: 'PlainText',
        text: `Hello World!`
      }
    }
  };
  context.succeed(response);
};
