'use strict';

const createSSMLSpeechObject = (message) => {
    return {
        type: 'SSML',
        ssml: `<speak> ${message} </speak>`
    };
};

const buildCard = (cardTitle, cardContent, cardImage) => {
   let card = {
        type: CARD_TYPES.SIMPLE,
        title: cardTitle,
        content: cardContent
    };

    if(cardImage && (cardImage.smallImageUrl || cardImage.largeImageUrl)) {
        card.type = CARD_TYPES.STANDARD;
        card.image = {};

        delete card.content;
        card.text = cardContent;

        if(cardImage.smallImageUrl) {
            card.image.smallImageUrl = cardImage.smallImageUrl;
        }

        if(cardImage.largeImageUrl) {
            card.image.largeImageUrl = cardImage.largeImageUrl;
        }
    }

    return card;
};

const CARD_TYPES = {
    STANDARD : 'Standard',
    SIMPLE : 'Simple',
    LINK_ACCOUNT : 'LinkAccount'
};

const HINT_TYPES = {
    PLAIN_TEXT : 'PlainText'
};

const DIRECTIVE_TYPES = {
    AUDIOPLAYER : {
        PLAY : 'AudioPlayer.Play',
        STOP : 'AudioPlayer.Stop',
        CLEAR_QUEUE : 'AudioPlayer.ClearQueue'
    },
    DISPLAY : {
        RENDER_TEMPLATE : 'Display.RenderTemplate'
    },
    HINT : 'Hint',
    VIDEOAPP : {
        LAUNCH : 'VideoApp.Launch'
    }
};

/**
 * Responsible for building JSON responses as per the Alexa skills kit interface
 * https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/alexa-skills-kit-interface-reference#response-body-syntax
 * 
 * @class ResponseBuilder
 */
class ResponseBuilder {
    constructor(alexaHandler) { // property : response
        this._responseObject = alexaHandler.response;
        this._responseObject.version = '1.0';
        this._responseObject.response = {
            shouldEndSession : true
        };
        
        this._responseObject.sessionAttributes = alexaHandler._event.session.attributes;
    }

    /**
     * Have Alexa say the provided speechOutput to the user
     * 
     * @param {string} speechOutput
     * @returns 
     * @memberof ResponseBuilder
     */
    speak(speechOutput) {
        this._responseObject.response.outputSpeech = createSSMLSpeechObject(speechOutput);
        return this;
    }

    /**
     * Have alexa listen for speech from the user. If the user doesn't respond within 8 seconds
     * then have alexa reprompt with the provided reprompt speech
     * @param {string} repromptSpeech
     * @returns 
     * @memberof ResponseBuilder
     */
    listen(repromptSpeech) {
        this._responseObject.response.reprompt = {
            outputSpeech: createSSMLSpeechObject(repromptSpeech)
        };
        this._responseObject.response.shouldEndSession = false;
        return this;
    }

    /**
     * Render a card with the following title, content and image
     * 
     * @param {string} cardTitle 
     * @param {string} cardContent 
     * @param {{smallImageUrl : string, largeImageUrl : string}} cardImage 
     * @returns 
     * @memberof ResponseBuilder
     */
    cardRenderer(cardTitle, cardContent, cardImage) {
        const card = buildCard(cardTitle, cardContent, cardImage);
        this._responseObject.response.card = card;
        return this;
    }

    /**
     * Render a link account card
     * 
     * @returns 
     * @memberof ResponseBuilder
     */
    linkAccountCard() {
        this._responseObject.response.card = {
            type: CARD_TYPES.LINK_ACCOUNT
        };
        return this;
    }

    /**
     * Creates a play, stop or clearQueue audioPlayer directive depending on the directive type passed in.
     * @deprecated - use audioPlayerPlay, audioPlayerStop, audioPlayerClearQueue instead
     * @param {string} directiveType 
     * @param {string} behavior 
     * @param {string} url 
     * @param {string} token 
     * @param {string} expectedPreviousToken 
     * @param {number} offsetInMilliseconds 
     * @returns 
     * @memberof ResponseBuilder
     */
    audioPlayer(directiveType, behavior, url, token, expectedPreviousToken, offsetInMilliseconds) {
        if (directiveType === 'play') {
            return this.audioPlayerPlay(behavior, url, token, expectedPreviousToken, offsetInMilliseconds);
        } else if (directiveType === 'stop') {
            return this.audioPlayerStop();
        } else {
            return this.audioPlayerClearQueue(behavior);
        }
    }

    /**
     * Creates an AudioPlayer play directive
     * 
     * @param {string} behavior Describes playback behavior. Accepted values:
     * REPLACE_ALL: Immediately begin playback of the specified stream, and replace current and enqueued streams.
     * ENQUEUE: Add the specified stream to the end of the current queue. This does not impact the currently playing stream.
     * REPLACE_ENQUEUED: Replace all streams in the queue. This does not impact the currently playing stream.
     * @param {string} url Identifies the location of audio content at a remote HTTPS location.
     * The audio file must be hosted at an Internet-accessible HTTPS endpoint. HTTPS is required, and the domain hosting the 
     * files must present a valid, trusted SSL certificate. Self-signed certificates cannot be used. 
     * The supported formats for the audio file include AAC/MP4, MP3, HLS, PLS and M3U. Bitrates: 16kbps to 384 kbps.
     * @param {string} token A token that represents the audio stream. This token cannot exceed 1024 characters
     * @param {string} expectedPreviousToken A token that represents the expected previous stream.
     * This property is required and allowed only when the playBehavior is ENQUEUE. This is used to prevent potential race conditions 
     * if requests to progress through a playlist and change tracks occur at the same time.
     * @param {string} offsetInMilliseconds The timestamp in the stream from which Alexa should begin playback. 
     * Set to 0 to start playing the stream from the beginning. Set to any other value to start playback from that associated point in the stream
     * @returns 
     * @memberof ResponseBuilder
     */
    audioPlayerPlay(behavior, url, token, expectedPreviousToken, offsetInMilliseconds) {
        const audioPlayerDirective = {
            type : DIRECTIVE_TYPES.AUDIOPLAYER.PLAY,
            playBehavior: behavior,
            audioItem: {
                stream: {
                    url: url,
                    token: token,
                    expectedPreviousToken: expectedPreviousToken,
                    offsetInMilliseconds: offsetInMilliseconds
                }
            }
        };

        this._addDirective(audioPlayerDirective);
        return this;
    }

    /**
     * Creates an AudioPlayer Stop directive - Stops the current audio Playback
     * 
     * @returns 
     * @memberof ResponseBuilder
     */
    audioPlayerStop() {
        const audioPlayerDirective = {
            'type': DIRECTIVE_TYPES.AUDIOPLAYER.STOP
        };

        this._addDirective(audioPlayerDirective);
        return this;
    }

    /**
     * Creates an AudioPlayer ClearQueue directive - clear the queue without stopping the currently playing stream,
     * or clear the queue and stop any currently playing stream.
     * 
     * @param {string} clearBehavior Describes the clear queue behavior. Accepted values:
     * CLEAR_ENQUEUED: clears the queue and continues to play the currently playing stream
     * CLEAR_ALL: clears the entire playback queue and stops the currently playing stream (if applicable).
     * @returns 
     * @memberof ResponseBuilder
     */
    audioPlayerClearQueue(clearBehavior) {
        const audioPlayerDirective = {
            type : DIRECTIVE_TYPES.AUDIOPLAYER.CLEAR_QUEUE,
            clearBehavior : clearBehavior
        };

        this._addDirective(audioPlayerDirective);
        return this;
    }

    /**
     * Creates a Display RenderTemplate Directive
     * 
     * Use a template builder to generate a template object
     * 
     * @param {Template} template 
     * @returns 
     * @memberof ResponseBuilder
     */
    renderTemplate(template) {
        const templateDirective = {
            type : DIRECTIVE_TYPES.DISPLAY.RENDER_TEMPLATE,
            template : template
        };

        this._addDirective(templateDirective);
        return this;
    }

    /**
     * Creates a hint directive - show a hint on the screen of the echo show
     * 
     * @param {string} hintText text to show on the hint
     * @param {string} hintType (optional) Default value : PlainText
     * @returns 
     * @memberof ResponseBuilder
     */
    hint(hintText, hintType) {
        if(!hintType) {
            hintType = HINT_TYPES.PLAIN_TEXT;
        }

        const hintDirective = {
            type : DIRECTIVE_TYPES.HINT,
            hint : {
                type : hintType,
                text : hintText
            }
        };

        this._addDirective(hintDirective);
        return this;
    }

    /**
     * Creates a VideoApp play directive to play a video
     * 
     * @param {string} source Identifies the location of video content at a remote HTTPS location.
     * The video file must be hosted at an Internet-accessible HTTPS endpoint.
     * @param {{title : string, subtitle : string}} metadata (optional) Contains an object that provides the 
     * information that can be displayed on VideoApp.
     * @returns 
     * @memberof ResponseBuilder
     */
    playVideo(source, metadata) {
        const playVideoDirective = {
            type : DIRECTIVE_TYPES.VIDEOAPP.LAUNCH,
            videoItem : {
                source : source
            }
        };

        if (playVideoDirective.videoItem.metadata) {
            playVideoDirective.videoItem.metadata = metadata;
        }

        // Note : shouldEndSession flag is not allowed with LaunchVideoApp.Launch Directive
        delete this._responseObject.response.shouldEndSession;
        this._addDirective(playVideoDirective);
        return this;
    }

    /**
     * Helper method for adding directives to responses
     * 
     * @param {object} directive 
     * @memberof ResponseBuilder
     */
    _addDirective(directive) {
        if(!Array.isArray(this._responseObject.response.directives)) {
            this._responseObject.response.directives = [];
        }

        this._responseObject.response.directives.push(directive);
    }
}

module.exports.ResponseBuilder = ResponseBuilder;
module.exports.CARD_TYPES = CARD_TYPES;
module.exports.DIRECTIVE_TYPES = DIRECTIVE_TYPES;
module.exports.HINT_TYPES = HINT_TYPES;