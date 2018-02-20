'use strict';
var attributesHelper = require('./DynamoAttributesHelper');

module.exports = (function () {
    return {
        ':tell': function (speechOutput) {
            if(this.isOverridden()) {
                return;
            }

            this.handler.response = buildSpeechletResponse({
                sessionAttributes: this.attributes,
                output: getSSMLResponse(speechOutput),
                shouldEndSession: true
            });
            this.emit(':responseReady');
        },
        ':ask': function (speechOutput, repromptSpeech) {
            if(this.isOverridden()) {
                return;
            }
            this.handler.response = buildSpeechletResponse({
                sessionAttributes: this.attributes,
                output: getSSMLResponse(speechOutput),
                reprompt: getSSMLResponse(repromptSpeech),
                shouldEndSession: false
            });
            this.emit(':responseReady');
        },
        ':askWithCard': function(speechOutput, repromptSpeech, cardTitle, cardContent, imageObj) {
            if(this.isOverridden()) {
                return;
            }

            this.handler.response = buildSpeechletResponse({
                sessionAttributes: this.attributes,
                output: getSSMLResponse(speechOutput),
                reprompt: getSSMLResponse(repromptSpeech),
                cardTitle: cardTitle,
                cardContent: cardContent,
                cardImage: imageObj,
                shouldEndSession: false
            });
            this.emit(':responseReady');
        },
        ':tellWithCard': function(speechOutput, cardTitle, cardContent, imageObj) {
            if(this.isOverridden()) {
                return;
            }

            this.handler.response = buildSpeechletResponse({
                sessionAttributes: this.attributes,
                output: getSSMLResponse(speechOutput),
                cardTitle: cardTitle,
                cardContent: cardContent,
                cardImage: imageObj,
                shouldEndSession: true
            });
            this.emit(':responseReady');
        },
        ':tellWithLinkAccountCard': function(speechOutput) {
            if(this.isOverridden()) {
                return;
            }

            this.handler.response = buildSpeechletResponse({
                sessionAttributes: this.attributes,
                output: getSSMLResponse(speechOutput),
                cardType: 'LinkAccount',
                shouldEndSession: true
            });
            this.emit(':responseReady');
        },
        ':askWithLinkAccountCard': function(speechOutput, repromptSpeech) {
            if(this.isOverridden()) {
                return;
            }

            this.handler.response = buildSpeechletResponse({
                sessionAttributes: this.attributes,
                output: getSSMLResponse(speechOutput),
                reprompt: getSSMLResponse(repromptSpeech),
                cardType: 'LinkAccount',
                shouldEndSession: false
            });
            this.emit(':responseReady');
        },
        ':tellWithPermissionCard': function(speechOutput, permissions) {
            if(this.isOverridden()) {
                return;
            }

            this.handler.response = buildSpeechletResponse({
                sessionAttributes: this.attributes,
                output: getSSMLResponse(speechOutput),
                permissions: permissions,
                cardType: 'AskForPermissionsConsent',
                shouldEndSession: true
            });
            this.emit(':responseReady');
        },
        ':delegate': function(updatedIntent) {
            if(this.isOverridden()) {
                return;
            }

            this.handler.response = buildSpeechletResponse({
                sessionAttributes: this.attributes,
                directives: getDialogDirectives('Dialog.Delegate', updatedIntent, null),
                shouldEndSession: false
            });
            this.emit(':responseReady');
        },
        ':elicitSlot': function (slotName, speechOutput, repromptSpeech, updatedIntent) {
            if(this.isOverridden()) {
                return;
            }
            this.handler.response = buildSpeechletResponse({
                sessionAttributes: this.attributes,
                output: getSSMLResponse(speechOutput),
                reprompt: getSSMLResponse(repromptSpeech),
                directives: getDialogDirectives('Dialog.ElicitSlot', updatedIntent, slotName),
                shouldEndSession: false
            });
            this.emit(':responseReady');
        },
        ':elicitSlotWithCard': function (slotName, speechOutput, repromptSpeech, cardTitle, cardContent, updatedIntent, imageObj) {
            if(this.isOverridden()) {
                return;
            }
            this.handler.response = buildSpeechletResponse({
                sessionAttributes: this.attributes,
                output: getSSMLResponse(speechOutput),
                reprompt: getSSMLResponse(repromptSpeech),
                cardTitle: cardTitle,
                cardContent: cardContent,
                cardImage: imageObj,
                directives: getDialogDirectives('Dialog.ElicitSlot', updatedIntent, slotName),
                shouldEndSession: false
            });
            this.emit(':responseReady');
        },
        ':confirmSlot': function (slotName, speechOutput, repromptSpeech, updatedIntent) {
            if(this.isOverridden()) {
                return;
            }
            this.handler.response = buildSpeechletResponse({
                sessionAttributes: this.attributes,
                output: getSSMLResponse(speechOutput),
                reprompt: getSSMLResponse(repromptSpeech),
                directives: getDialogDirectives('Dialog.ConfirmSlot', updatedIntent, slotName),
                shouldEndSession: false
            });
            this.emit(':responseReady');
        },
        ':confirmSlotWithCard': function (slotName, speechOutput, repromptSpeech, cardTitle, cardContent, updatedIntent, imageObj) {
            if(this.isOverridden()) {
                return;
            }
            this.handler.response = buildSpeechletResponse({
                sessionAttributes: this.attributes,
                output: getSSMLResponse(speechOutput),
                reprompt: getSSMLResponse(repromptSpeech),
                cardTitle: cardTitle,
                cardContent: cardContent,
                cardImage: imageObj,
                directives: getDialogDirectives('Dialog.ConfirmSlot', updatedIntent, slotName),
                shouldEndSession: false
            });
            this.emit(':responseReady');
        },
        ':confirmIntent': function (speechOutput, repromptSpeech, updatedIntent) {
            if(this.isOverridden()) {
                return;
            }
            this.handler.response = buildSpeechletResponse({
                sessionAttributes: this.attributes,
                output: getSSMLResponse(speechOutput),
                reprompt: getSSMLResponse(repromptSpeech),
                directives: getDialogDirectives('Dialog.ConfirmIntent', updatedIntent, null),
                shouldEndSession: false
            });
            this.emit(':responseReady');
        },
        ':confirmIntentWithCard': function (speechOutput, repromptSpeech, cardTitle, cardContent, updatedIntent, imageObj) {
            if(this.isOverridden()) {
                return;
            }
            this.handler.response = buildSpeechletResponse({
                sessionAttributes: this.attributes,
                output: getSSMLResponse(speechOutput),
                reprompt: getSSMLResponse(repromptSpeech),
                cardTitle: cardTitle,
                cardContent: cardContent,
                cardImage: imageObj,
                directives: getDialogDirectives('Dialog.ConfirmIntent', updatedIntent, null),
                shouldEndSession: false
            });
            this.emit(':responseReady');
        },
        ':responseReady': function () {
            if (this.isOverridden()) {
                return;
            }

            if(this.handler.state) {
                this.handler.response.sessionAttributes.STATE = this.handler.state;
            }

            if (this.handler.dynamoDBTableName) {
                this.emit(':saveState');
            }

            if(typeof this.callback === 'undefined') {
                this.context.succeed(this.handler.response);
            } else {
                this.callback(null, this.handler.response);
            }
        },
        ':saveState': function(forceSave) {
            if (this.isOverridden()) {
                return;
            }

            if(forceSave && this.handler.state){
                this.attributes.STATE = this.handler.state;
            }

            var userId = '';

            // Long-form audio enabled skills use event.context
            if (this.event.context) {
                userId = this.event.context.System.user.userId;
            } else if (this.event.session) {
                userId = this.event.session.user.userId;
            }

            if(this.handler.saveBeforeResponse || forceSave || this.handler.response.response.shouldEndSession) {
                attributesHelper.set(this.handler.dynamoDBTableName, userId, this.attributes, (err) => {
                    if(err) {
                        return this.emit(':saveStateError', err);
                    }
                });
            }
        },
        ':saveStateError': function(err) {
            if(this.isOverridden()) {
                return;
            }
            console.log(`Error saving state: ${err}\n${err.stack}`);
            if(typeof this.callback === 'undefined') {
                this.context.fail(err);
            } else {
                this.callback(err);
            }
        }
    };
})();

function createSpeechObject(optionsParam) {
    if (optionsParam && optionsParam.type === 'SSML') {
        return {
            type: optionsParam.type,
            ssml: optionsParam.speech
        };
    } else {
        return {
            type: optionsParam.type || 'PlainText',
            text: optionsParam.speech || optionsParam
        };
    }
}

function buildSpeechletResponse(options) {
    var alexaResponse = {
        shouldEndSession: options.shouldEndSession
    };

    if (options.output) {
        alexaResponse.outputSpeech = createSpeechObject(options.output);
    }

    if (options.reprompt) {
        alexaResponse.reprompt = {
            outputSpeech: createSpeechObject(options.reprompt)
        };
    }

    if (options.directives) {
        alexaResponse.directives = options.directives;
    }

    if (options.cardTitle && options.cardContent) {
        alexaResponse.card = {
            type: 'Simple',
            title: options.cardTitle,
            content: options.cardContent
        };

        if(options.cardImage && (options.cardImage.smallImageUrl || options.cardImage.largeImageUrl)) {
            alexaResponse.card.type = 'Standard';
            alexaResponse.card.image = {};

            delete alexaResponse.card.content;
            alexaResponse.card.text = options.cardContent;

            if(options.cardImage.smallImageUrl) {
                alexaResponse.card.image.smallImageUrl = options.cardImage.smallImageUrl;
            }

            if(options.cardImage.largeImageUrl) {
                alexaResponse.card.image.largeImageUrl = options.cardImage.largeImageUrl;
            }
        }
    } else if (options.cardType === 'LinkAccount') {
        alexaResponse.card = {
            type: 'LinkAccount'
        };
    } else if (options.cardType === 'AskForPermissionsConsent') {
        alexaResponse.card = {
            type: 'AskForPermissionsConsent',
            permissions: options.permissions
        };
    }

    var returnResult = {
        version: '1.0',
        response: alexaResponse
    };

    if (options.sessionAttributes) {
        returnResult.sessionAttributes = options.sessionAttributes;
    }
    return returnResult;
}

// TODO: check for ssml content in card
function getSSMLResponse(message) {
    if (message == null) { // jshint ignore:line
        return null;
    } else {
        return {
            type: 'SSML',
            speech: `<speak> ${message} </speak>`
        };
    }
}

function getDialogDirectives(dialogType, updatedIntent, slotName) {
    let directive = {
        type: dialogType
    };

    if (dialogType === 'Dialog.ElicitSlot') {
        directive.slotToElicit = slotName;
    } else if (dialogType === 'Dialog.ConfirmSlot') {
        directive.slotToConfirm = slotName;
    }

    if (updatedIntent) {
        directive.updatedIntent = updatedIntent;
    }
    return [directive];
}
