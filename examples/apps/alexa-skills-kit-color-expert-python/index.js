/* eslint-disable  func-names */
/* eslint-disable  dot-notation */
/* eslint-disable  new-cap */
/* eslint quote-props: ['error', 'consistent']*/
/**
 * This sample demonstrates a simple skill built with the Amazon Alexa Skills
 * nodejs skill development kit.
 * This sample supports en-US lauguage.
 * The Intent Schema, Custom Slots and Sample Utterances for this skill, as well
 * as testing instructions are located at https://github.com/alexa/skill-sample-nodejs-trivia
 **/

'use strict';

const Alexa = require('alexa-sdk');
const questions = require('./question');

const ANSWER_COUNT = 4; // The number of possible answers per trivia question.
const GAME_LENGTH = 5;  // The number of questions per trivia game.
const GAME_STATES = {
    TRIVIA: '_TRIVIAMODE', // Asking trivia questions.
    START: '_STARTMODE', // Entry point, start the game.
    HELP: '_HELPMODE', // The user is asking for help.
};
const APP_ID = undefined; // TODO replace with your app ID (OPTIONAL)

/**
 * When editing your questions pay attention to your punctuation. Make sure you use question marks or periods.
 * Make sure the first answer is the correct one. Set at least ANSWER_COUNT answers, any extras will be shuffled in.
 */
const languageString = {
    'en': {
        'translation': {
            'QUESTIONS': questions['QUESTIONS_EN_US'],
            'GAME_NAME': 'Reindeer Trivia', // Be sure to change this for your skill.
            'HELP_MESSAGE': 'I will ask you %s multiple choice questions. Respond with the number of the answer. ' +
                'For example, say one, two, three, or four. To start a new game at any time, say, start game. ',
            'REPEAT_QUESTION_MESSAGE': 'To repeat the last question, say, repeat. ',
            'ASK_MESSAGE_START': 'Would you like to start playing?',
            'HELP_REPROMPT': 'To give an answer to a question, respond with the number of the answer. ',
            'STOP_MESSAGE': 'Would you like to keep playing?',
            'CANCEL_MESSAGE': 'Ok, let\'s play again soon.',
            'NO_MESSAGE': 'Ok, we\'ll play another time. Goodbye!',
            'TRIVIA_UNHANDLED': 'Try saying a number between 1 and %s',
            'HELP_UNHANDLED': 'Say yes to continue, or no to end the game.',
            'START_UNHANDLED': 'Say start to start a new game.',
            'NEW_GAME_MESSAGE': 'Welcome to %s. ',
            'WELCOME_MESSAGE': 'I will ask you %s questions, try to get as many right as you can. ' +
            'Just say the number of the answer. Let\'s begin. ',
            'ANSWER_CORRECT_MESSAGE': 'correct. ',
            'ANSWER_WRONG_MESSAGE': 'wrong. ',
            'CORRECT_ANSWER_MESSAGE': 'The correct answer is %s: %s. ',
            'ANSWER_IS_MESSAGE': 'That answer is ',
            'TELL_QUESTION_MESSAGE': 'Question %s. %s ',
            'GAME_OVER_MESSAGE': 'You got %s out of %s questions correct. Thank you for playing!',
            'SCORE_IS_MESSAGE': 'Your score is %s. ',
        },
    },
    'en-US': {
        'translation': {
            'QUESTIONS': questions['QUESTIONS_EN_US'],
            'GAME_NAME': 'American Reindeer Trivia', // Be sure to change this for your skill.
        },
    },
    'en-GB': {
        'translation': {
            'QUESTIONS': questions['QUESTIONS_EN_GB'],
            'GAME_NAME': 'British Reindeer Trivia', // Be sure to change this for your skill.
        },
    },
    'de': {
        'translation': {
            'QUESTIONS': questions['QUESTIONS_DE_DE'],
            'GAME_NAME': 'Wissenswertes über Rentiere in Deutsch', // Be sure to change this for your skill.
            'HELP_MESSAGE': 'Ich stelle dir %s Multiple-Choice-Fragen. Antworte mit der Zahl, die zur richtigen Antwort gehört. ' +
                'Sage beispielsweise eins, zwei, drei oder vier. Du kannst jederzeit ein neues Spiel beginnen, sage einfach „Spiel starten“. ',
            'REPEAT_QUESTION_MESSAGE': 'Wenn die letzte Frage wiederholt werden soll, sage „Wiederholen“ ',
            'ASK_MESSAGE_START': 'Möchten Sie beginnen?',
            'HELP_REPROMPT': 'Wenn du eine Frage beantworten willst, antworte mit der Zahl, die zur richtigen Antwort gehört. ',
            'STOP_MESSAGE': 'Möchtest du weiterspielen?',
            'CANCEL_MESSAGE': 'OK, dann lass uns bald mal wieder spielen.',
            'NO_MESSAGE': 'OK, spielen wir ein andermal. Auf Wiedersehen!',
            'TRIVIA_UNHANDLED': 'Sagt eine Zahl beispielsweise zwischen 1 und %s',
            'HELP_UNHANDLED': 'Sage ja, um fortzufahren, oder nein, um das Spiel zu beenden.',
            'START_UNHANDLED': 'Du kannst jederzeit ein neues Spiel beginnen, sage einfach „Spiel starten“.',
            'NEW_GAME_MESSAGE': 'Willkommen bei %s. ',
            'WELCOME_MESSAGE': 'Ich stelle dir %s Fragen und du versuchst, so viele wie möglich richtig zu beantworten. ' +
            'Sage einfach die Zahl, die zur richtigen Antwort passt. Fangen wir an. ',
            'ANSWER_CORRECT_MESSAGE': 'Richtig. ',
            'ANSWER_WRONG_MESSAGE': 'Falsch. ',
            'CORRECT_ANSWER_MESSAGE': 'Die richtige Antwort ist %s: %s. ',
            'ANSWER_IS_MESSAGE': 'Diese Antwort ist ',
            'TELL_QUESTION_MESSAGE': 'Frage %s. %s ',
            'GAME_OVER_MESSAGE': 'Du hast %s von %s richtig beantwortet. Danke fürs Mitspielen!',
            'SCORE_IS_MESSAGE': 'Dein Ergebnis ist %s. ',
        },
    },
};

const newSessionHandlers = {
    'LaunchRequest': function () {
        this.handler.state = GAME_STATES.START;
        this.emitWithState('StartGame', true);
    },
    'AMAZON.StartOverIntent': function () {
        this.handler.state = GAME_STATES.START;
        this.emitWithState('StartGame', true);
    },
    'AMAZON.HelpIntent': function () {
        this.handler.state = GAME_STATES.HELP;
        this.emitWithState('helpTheUser', true);
    },
    'Unhandled': function () {
        const speechOutput = this.t('START_UNHANDLED');
        this.emit(':ask', speechOutput, speechOutput);
    },
};

function populateGameQuestions(translatedQuestions) {
    const gameQuestions = [];
    const indexList = [];
    let index = translatedQuestions.length;

    if (GAME_LENGTH > index) {
        throw new Error('Invalid Game Length.');
    }

    for (let i = 0; i < translatedQuestions.length; i++) {
        indexList.push(i);
    }

    // Pick GAME_LENGTH random questions from the list to ask the user, make sure there are no repeats.
    for (let j = 0; j < GAME_LENGTH; j++) {
        const rand = Math.floor(Math.random() * index);
        index -= 1;

        const temp = indexList[index];
        indexList[index] = indexList[rand];
        indexList[rand] = temp;
        gameQuestions.push(indexList[index]);
    }

    return gameQuestions;
}

/**
 * Get the answers for a given question, and place the correct answer at the spot marked by the
 * correctAnswerTargetLocation variable. Note that you can have as many answers as you want but
 * only ANSWER_COUNT will be selected.
 * */
function populateRoundAnswers(gameQuestionIndexes, correctAnswerIndex, correctAnswerTargetLocation, translatedQuestions) {
    const answers = [];
    const answersCopy = translatedQuestions[gameQuestionIndexes[correctAnswerIndex]][Object.keys(translatedQuestions[gameQuestionIndexes[correctAnswerIndex]])[0]].slice();
    let index = answersCopy.length;

    if (index < ANSWER_COUNT) {
        throw new Error('Not enough answers for question.');
    }

    // Shuffle the answers, excluding the first element which is the correct answer.
    for (let j = 1; j < answersCopy.length; j++) {
        const rand = Math.floor(Math.random() * (index - 1)) + 1;
        index -= 1;

        const swapTemp1 = answersCopy[index];
        answersCopy[index] = answersCopy[rand];
        answersCopy[rand] = swapTemp1;
    }

    // Swap the correct answer into the target location
    for (let i = 0; i < ANSWER_COUNT; i++) {
        answers[i] = answersCopy[i];
    }
    const swapTemp2 = answers[0];
    answers[0] = answers[correctAnswerTargetLocation];
    answers[correctAnswerTargetLocation] = swapTemp2;
    return answers;
}

function isAnswerSlotValid(intent) {
    const answerSlotFilled = intent && intent.slots && intent.slots.Answer && intent.slots.Answer.value;
    const answerSlotIsInt = answerSlotFilled && !isNaN(parseInt(intent.slots.Answer.value, 10));
    return answerSlotIsInt
        && parseInt(intent.slots.Answer.value, 10) < (ANSWER_COUNT + 1)
        && parseInt(intent.slots.Answer.value, 10) > 0;
}

function handleUserGuess(userGaveUp) {
    const answerSlotValid = isAnswerSlotValid(this.event.request.intent);
    let speechOutput = '';
    let speechOutputAnalysis = '';
    const gameQuestions = this.attributes.questions;
    let correctAnswerIndex = parseInt(this.attributes.correctAnswerIndex, 10);
    let currentScore = parseInt(this.attributes.score, 10);
    let currentQuestionIndex = parseInt(this.attributes.currentQuestionIndex, 10);
    const correctAnswerText = this.attributes.correctAnswerText;
    const translatedQuestions = this.t('QUESTIONS');

    if (answerSlotValid && parseInt(this.event.request.intent.slots.Answer.value, 10) === this.attributes['correctAnswerIndex']) {
        currentScore++;
        speechOutputAnalysis = this.t('ANSWER_CORRECT_MESSAGE');
    } else {
        if (!userGaveUp) {
            speechOutputAnalysis = this.t('ANSWER_WRONG_MESSAGE');
        }

        speechOutputAnalysis += this.t('CORRECT_ANSWER_MESSAGE', correctAnswerIndex, correctAnswerText);
    }

    // Check if we can exit the game session after GAME_LENGTH questions (zero-indexed)
    if (this.attributes['currentQuestionIndex'] === GAME_LENGTH - 1) {
        speechOutput = userGaveUp ? '' : this.t('ANSWER_IS_MESSAGE');
        speechOutput += speechOutputAnalysis + this.t('GAME_OVER_MESSAGE', currentScore.toString(), GAME_LENGTH.toString());

        this.emit(':tell', speechOutput);
    } else {
        currentQuestionIndex += 1;
        correctAnswerIndex = Math.floor(Math.random() * (ANSWER_COUNT));
        const spokenQuestion = Object.keys(translatedQuestions[gameQuestions[currentQuestionIndex]])[0];
        const roundAnswers = populateRoundAnswers.call(this, gameQuestions, currentQuestionIndex, correctAnswerIndex, translatedQuestions);
        const questionIndexForSpeech = currentQuestionIndex + 1;
        let repromptText = this.t('TELL_QUESTION_MESSAGE', questionIndexForSpeech.toString(), spokenQuestion);

        for (let i = 0; i < ANSWER_COUNT; i++) {
            repromptText += `${i + 1}. ${roundAnswers[i]}. `;
        }

        speechOutput += userGaveUp ? '' : this.t('ANSWER_IS_MESSAGE');
        speechOutput += speechOutputAnalysis + this.t('SCORE_IS_MESSAGE', currentScore.toString()) + repromptText;

        Object.assign(this.attributes, {
            'speechOutput': repromptText,
            'repromptText': repromptText,
            'currentQuestionIndex': currentQuestionIndex,
            'correctAnswerIndex': correctAnswerIndex + 1,
            'questions': gameQuestions,
            'score': currentScore,
            'correctAnswerText': translatedQuestions[gameQuestions[currentQuestionIndex]][Object.keys(translatedQuestions[gameQuestions[currentQuestionIndex]])[0]][0],
        });

        this.emit(':askWithCard', speechOutput, repromptText, this.t('GAME_NAME'), repromptText);
    }
}

const startStateHandlers = Alexa.CreateStateHandler(GAME_STATES.START, {
    'StartGame': function (newGame) {
        let speechOutput = newGame ? this.t('NEW_GAME_MESSAGE', this.t('GAME_NAME')) + this.t('WELCOME_MESSAGE', GAME_LENGTH.toString()) : '';
        // Select GAME_LENGTH questions for the game
        const translatedQuestions = this.t('QUESTIONS');
        const gameQuestions = populateGameQuestions(translatedQuestions);
        // Generate a random index for the correct answer, from 0 to 3
        const correctAnswerIndex = Math.floor(Math.random() * (ANSWER_COUNT));
        // Select and shuffle the answers for each question
        const roundAnswers = populateRoundAnswers(gameQuestions, 0, correctAnswerIndex, translatedQuestions);
        const currentQuestionIndex = 0;
        const spokenQuestion = Object.keys(translatedQuestions[gameQuestions[currentQuestionIndex]])[0];
        let repromptText = this.t('TELL_QUESTION_MESSAGE', '1', spokenQuestion);

        for (let i = 0; i < ANSWER_COUNT; i++) {
            repromptText += `${i + 1}. ${roundAnswers[i]}. `;
        }

        speechOutput += repromptText;

        Object.assign(this.attributes, {
            'speechOutput': repromptText,
            'repromptText': repromptText,
            'currentQuestionIndex': currentQuestionIndex,
            'correctAnswerIndex': correctAnswerIndex + 1,
            'questions': gameQuestions,
            'score': 0,
            'correctAnswerText': translatedQuestions[gameQuestions[currentQuestionIndex]][Object.keys(translatedQuestions[gameQuestions[currentQuestionIndex]])[0]][0],
        });

        // Set the current state to trivia mode. The skill will now use handlers defined in triviaStateHandlers
        this.handler.state = GAME_STATES.TRIVIA;
        this.emit(':askWithCard', speechOutput, repromptText, this.t('GAME_NAME'), repromptText);
    },
});

const triviaStateHandlers = Alexa.CreateStateHandler(GAME_STATES.TRIVIA, {
    'AnswerIntent': function () {
        handleUserGuess.call(this, false);
    },
    'DontKnowIntent': function () {
        handleUserGuess.call(this, true);
    },
    'AMAZON.StartOverIntent': function () {
        this.handler.state = GAME_STATES.START;
        this.emitWithState('StartGame', false);
    },
    'AMAZON.RepeatIntent': function () {
        this.emit(':ask', this.attributes['speechOutput'], this.attributes['repromptText']);
    },
    'AMAZON.HelpIntent': function () {
        this.handler.state = GAME_STATES.HELP;
        this.emitWithState('helpTheUser', false);
    },
    'AMAZON.StopIntent': function () {
        this.handler.state = GAME_STATES.HELP;
        const speechOutput = this.t('STOP_MESSAGE');
        this.emit(':ask', speechOutput, speechOutput);
    },
    'AMAZON.CancelIntent': function () {
        this.emit(':tell', this.t('CANCEL_MESSAGE'));
    },
    'Unhandled': function () {
        const speechOutput = this.t('TRIVIA_UNHANDLED', ANSWER_COUNT.toString());
        this.emit(':ask', speechOutput, speechOutput);
    },
    'SessionEndedRequest': function () {
        console.log(`Session ended in trivia state: ${this.event.request.reason}`);
    },
});

const helpStateHandlers = Alexa.CreateStateHandler(GAME_STATES.HELP, {
    'helpTheUser': function (newGame) {
        const askMessage = newGame ? this.t('ASK_MESSAGE_START') : this.t('REPEAT_QUESTION_MESSAGE') + this.t('STOP_MESSAGE');
        const speechOutput = this.t('HELP_MESSAGE', GAME_LENGTH) + askMessage;
        const repromptText = this.t('HELP_REPROMPT') + askMessage;
        this.emit(':ask', speechOutput, repromptText);
    },
    'AMAZON.StartOverIntent': function () {
        this.handler.state = GAME_STATES.START;
        this.emitWithState('StartGame', false);
    },
    'AMAZON.RepeatIntent': function () {
        const newGame = !(this.attributes['speechOutput'] && this.attributes['repromptText']);
        this.emitWithState('helpTheUser', newGame);
    },
    'AMAZON.HelpIntent': function () {
        const newGame = !(this.attributes['speechOutput'] && this.attributes['repromptText']);
        this.emitWithState('helpTheUser', newGame);
    },
    'AMAZON.YesIntent': function () {
        if (this.attributes['speechOutput'] && this.attributes['repromptText']) {
            this.handler.state = GAME_STATES.TRIVIA;
            this.emitWithState('AMAZON.RepeatIntent');
        } else {
            this.handler.state = GAME_STATES.START;
            this.emitWithState('StartGame', false);
        }
    },
    'AMAZON.NoIntent': function () {
        const speechOutput = this.t('NO_MESSAGE');
        this.emit(':tell', speechOutput);
    },
    'AMAZON.StopIntent': function () {
        const speechOutput = this.t('STOP_MESSAGE');
        this.emit(':ask', speechOutput, speechOutput);
    },
    'AMAZON.CancelIntent': function () {
        this.emit(':tell', this.t('CANCEL_MESSAGE'));
    },
    'Unhandled': function () {
        const speechOutput = this.t('HELP_UNHANDLED');
        this.emit(':ask', speechOutput, speechOutput);
    },
    'SessionEndedRequest': function () {
        console.log(`Session ended in help state: ${this.event.request.reason}`);
    },
});

exports.handler = function (event, context) {
    const alexa = Alexa.handler(event, context);
    alexa.appId = APP_ID;
    // To enable string internationalization (i18n) features, set a resources object.
    alexa.resources = languageString;
    alexa.registerHandlers(newSessionHandlers, startStateHandlers, triviaStateHandlers, helpStateHandlers);
    alexa.execute();
};
