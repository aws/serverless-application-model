'use strict';

var EventEmitter = require('events').EventEmitter;
var util = require('util');
var i18n = require('i18next');
var sprintf = require('i18next-sprintf-postprocessor');
var attributesHelper = require('./DynamoAttributesHelper');
var responseHandlers = require('./response');
var _StateString = 'STATE';

function AlexaRequestEmitter() {
    EventEmitter.call(this);
}

util.inherits(AlexaRequestEmitter, EventEmitter);

function alexaRequestHandler(event, context, callback) {
    if (!event.session) {
        event.session = { 'attributes': {} };
    } else if (!event.session['attributes']) {
        event.session['attributes'] = {};
    }

    var handler = new AlexaRequestEmitter();
    handler.setMaxListeners(Infinity);

    Object.defineProperty(handler, '_event', {
        value: event,
        writable: false
    });

    Object.defineProperty(handler, '_context', {
        value: context,
        writable: false
    });

    Object.defineProperty(handler, '_callback', {
        value: callback,
        writable: false
    });

    Object.defineProperty(handler, 'state', {
        value: null,
        writable: true,
        configurable: true
    });

    Object.defineProperty(handler, 'appId', {
        value: null,
        writable: true
    });

    Object.defineProperty(handler, 'response', {
        value: {},
        writable: true
    });

    Object.defineProperty(handler, 'dynamoDBTableName', {
        value: null,
        writable: true
    });

    Object.defineProperty(handler, 'saveBeforeResponse', {
        value: false,
        writable: true
    });

    Object.defineProperty(handler, 'i18n', {
        value: i18n,
        writable: true
    });

    Object.defineProperty(handler, 'locale', {
        value: undefined,
        writable: true
    });

    Object.defineProperty(handler, 'resources', {
        value: undefined,
        writable: true
    });

    Object.defineProperty(handler, 'registerHandlers', {
        value: function() {
            RegisterHandlers.apply(handler, arguments);
        },
        writable: false
    });

    Object.defineProperty(handler, 'execute', {
        value: function() {
            HandleLambdaEvent.call(handler);
        },
        writable: false
    });

    handler.registerHandlers(responseHandlers);

    return handler;
}

function HandleLambdaEvent() {
    this.locale = this._event.request.locale;
    if(this.resources) {
        this.i18n.use(sprintf).init({
            overloadTranslationOptionHandler: sprintf.overloadTranslationOptionHandler,
            returnObjects: true,
            lng: this.locale,
            resources: this.resources
        }, (err, t) => {
            if(err) {
                throw new Error('Error initializing i18next: ' + err);
            }
            ValidateRequest.call(this);
        });
    } else {
        ValidateRequest.call(this);
    }
}

function ValidateRequest() {
    var event = this._event;
    var context = this._context;
    var callback = this._callback;
    var handlerAppId = this.appId;

    var requestAppId = '';
    var userId = '';

    // Long-form audio enabled skills use event.context
    if (event.context) {
        requestAppId = event.context.System.application.applicationId;
        userId = event.context.System.user.userId;
    } else if (event.session) {
        requestAppId = event.session.application.applicationId;
        userId = event.session.user.userId;
    }


    if(!handlerAppId){
        console.log('Warning: Application ID is not set');
    }

    try {
        // Validate that this request originated from authorized source.
        if (handlerAppId && (requestAppId !== handlerAppId)) {
            console.log(`The applicationIds don\'t match: ${requestAppId} and ${handlerAppId}`);
            var error = new Error('Invalid ApplicationId: ' + handlerAppId)
            if(typeof callback === 'undefined') {
                return context.fail(error)
            } else {
                return callback(error);
            }
        }

        if(this.dynamoDBTableName && (!event.session.sessionId || event.session['new']) ) {
            attributesHelper.get(this.dynamoDBTableName, userId, (err, data) => {
                if(err) {
                    var error = new Error('Error fetching user state: ' + err)
                    if(typeof callback === 'undefined') {
                        return context.fail(error)
                    } else {
                        return  callback(error);
                    }
                }

                Object.assign(this._event.session.attributes, data);

                EmitEvent.call(this);
            });
        } else {
            EmitEvent.call(this);
        }
    } catch (e) {
        console.log(`Unexpected exception '${e}':\n${e.stack}`);
        if(typeof callback === 'undefined') {
            return context.fail(e)
        } else {
            return  callback(e);
        }
    }
}

function EmitEvent() {
    this.state = this._event.session.attributes[_StateString] || '';

    var eventString = '';

    if (this._event.session['new'] && this.listenerCount('NewSession' + this.state) === 1) {
        eventString = 'NewSession';
    } else if(this._event.request.type === 'LaunchRequest') {
        eventString = 'LaunchRequest';
    } else if(this._event.request.type === 'IntentRequest') {
        eventString = this._event.request.intent.name;
    } else if (this._event.request.type === 'SessionEndedRequest'){
        eventString = 'SessionEndedRequest';
    } else if (this._event.request.type.substring(0,11) === 'AudioPlayer') {
        eventString = this._event.request.type.substring(12);
    } else if (this._event.request.type.substring(0,18) === 'PlaybackController') {
        eventString = this._event.request.type.substring(19);
    } else if (this._event.request.type === 'Display.ElementSelected') {
        eventString = 'ElementSelected';
    }

    eventString += this.state;

    if(this.listenerCount(eventString) < 1) {
        eventString = 'Unhandled' + this.state;
    }

    if(this.listenerCount(eventString) < 1){
        throw new Error(`No 'Unhandled' function defined for event: ${eventString}`);
    }

    this.emit(eventString);
}

function RegisterHandlers() {
    for(var arg = 0; arg < arguments.length; arg++) {
        var handlerObject = arguments[arg];

        if(!isObject(handlerObject)) {
            throw new Error(`Argument #${arg} was not an Object`);
        }

        var eventNames = Object.keys(handlerObject);

        for(var i = 0; i < eventNames.length; i++) {
            if(typeof(handlerObject[eventNames[i]]) !== 'function') {
                throw new Error(`Event handler for '${eventNames[i]}' was not a function`);
            }

            var eventName = eventNames[i];

            if(handlerObject[_StateString]) {
                eventName += handlerObject[_StateString];
            }

            var localize = function() {
                return this.i18n.t.apply(this.i18n, arguments);
            };

            var handlerContext = {
                on: this.on.bind(this),
                emit: this.emit.bind(this),
                emitWithState: EmitWithState.bind(this),
                state: this.state,
                handler: this,
                i18n: this.i18n,
                locale: this.locale,
                t : localize,
                event: this._event,
                attributes: this._event.session.attributes,
                context: this._context,
                callback : this._callback,
                name: eventName,
                isOverridden:  IsOverridden.bind(this, eventName),
                response: ResponseBuilder(this)
            };

            this.on(eventName, handlerObject[eventNames[i]].bind(handlerContext));
        }
    }
}

function isObject(obj) {
    return (!!obj) && (obj.constructor === Object);
}

function IsOverridden(name) {
    return this.listenerCount(name) > 1;
}

function ResponseBuilder(self) {
    var responseObject = self.response;
    responseObject.version = '1.0';
    responseObject.response = {
        shouldEndSession: true
    };
    responseObject.sessionAttributes = self._event.session.attributes;

    return (function () {
        return {
            'speak': function (speechOutput) {
                responseObject.response.outputSpeech = createSSMLSpeechObject(speechOutput);
                return this;
            },
            'listen': function (repromptSpeech) {
                responseObject.response.reprompt = {
                    outputSpeech: createSSMLSpeechObject(repromptSpeech)
                };
                responseObject.response.shouldEndSession = false;
                return this;
            },
            'cardRenderer': function (cardTitle, cardContent, cardImage) {
                var card = {
                    type: 'Simple',
                    title: cardTitle,
                    content: cardContent
                };

                if(cardImage && (cardImage.smallImageUrl || cardImage.largeImageUrl)) {
                    card.type = 'Standard';
                    card['image'] = {};

                    delete card.content;
                    card.text = cardContent;

                    if(cardImage.smallImageUrl) {
                        card.image['smallImageUrl'] = cardImage.smallImageUrl;
                    }

                    if(cardImage.largeImageUrl) {
                        card.image['largeImageUrl'] = cardImage.largeImageUrl;
                    }
                }

                responseObject.response.card = card;
                return this;
            },
            'linkAccountCard': function () {
                responseObject.response.card = {
                    type: 'LinkAccount'
                };
                return this;
            },
            'audioPlayer': function (directiveType, behavior, url, token, expectedPreviousToken, offsetInMilliseconds) {
                var audioPlayerDirective;
                if (directiveType === 'play') {
                    audioPlayerDirective = {
                        "type": "AudioPlayer.Play",
                        "playBehavior": behavior,
                        "audioItem": {
                            "stream": {
                                "url": url,
                                "token": token,
                                "expectedPreviousToken": expectedPreviousToken,
                                "offsetInMilliseconds": offsetInMilliseconds
                            }
                        }
                    };
                } else if (directiveType === 'stop') {
                    audioPlayerDirective = {
                        "type": "AudioPlayer.Stop"
                    };
                } else {
                    audioPlayerDirective = {
                        "type": "AudioPlayer.ClearQueue",
                        "clearBehavior": behavior
                    };
                }

                responseObject.response.directives = [audioPlayerDirective];
                return this;
            },
            'audioPlayerPlay': function (behavior, url, token, expectedPreviousToken, offsetInMilliseconds) {
                var audioPlayerDirective = {
                    "type": "AudioPlayer.Play",
                    "playBehavior": behavior,
                    "audioItem": {
                        "stream": {
                            "url": url,
                            "token": token,
                            "expectedPreviousToken": expectedPreviousToken,
                            "offsetInMilliseconds": offsetInMilliseconds
                        }
                    }
                };

                responseObject.response.directives = [audioPlayerDirective];
                return this;
            },
            'audioPlayerStop': function () {
                var audioPlayerDirective = {
                    "type": "AudioPlayer.Stop"
                };

                responseObject.response.directives = [audioPlayerDirective];
                return this;
            },
            'audioPlayerClearQueue': function (clearBehavior) {
                var audioPlayerDirective = {
                    "type": "AudioPlayer.ClearQueue",
                    "clearBehavior": clearBehavior
                };

                responseObject.response.directives = [audioPlayerDirective];
                return this;
            }
        }
    })();
}

function createSSMLSpeechObject(message) {
    return {
        type: 'SSML',
        ssml: `<speak> ${message} </speak>`
    };
}

function createStateHandler(state, obj){
    if(!obj) {
        obj = {};
    }

    Object.defineProperty(obj, _StateString, {
        value: state || ''
    });

    return obj;
}

function EmitWithState() {
    if(arguments.length === 0) {
        throw new Error('EmitWithState called without arguments');
    }
    arguments[0] = arguments[0] + this.state;

    if (this.listenerCount(arguments[0]) < 1) {
        arguments[0] = 'Unhandled' + this.state;
    }

    if (this.listenerCount(arguments[0]) < 1) {
        throw new Error(`No 'Unhandled' function defined for event: ${arguments[0]}`);
    }

    this.emit.apply(this, arguments);
}

process.on('uncaughtException', function(err) {
    console.log(`Uncaught exception: ${err}\n${err.stack}`);
    throw err;
});

module.exports.LambdaHandler = alexaRequestHandler;
module.exports.CreateStateHandler = createStateHandler;
module.exports.StateString = _StateString;
