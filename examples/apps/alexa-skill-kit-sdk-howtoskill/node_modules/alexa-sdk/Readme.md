# Alexa Skills Kit SDK for Node.js

Today we're happy to announce the new [alexa-sdk](https://github.com/alexa/alexa-skills-kit-sdk-for-nodejs) for Node.js to help you build skills faster and with less complexity.

Creating an Alexa skill using the [Alexa Skills Kit](http://developer.amazon.com/ask), [Node.js](https://nodejs.org/en/) and [AWS Lambda](https://aws.amazon.com/lambda/) has become one of the most popular ways we see skills created today. The event-driven, non-blocking I/O model of Node.js is well suited for an Alexa skill and Node.js is one of the largest ecosystems of open source libraries in the world. Plus, AWS Lambda is free for the first one million calls per month, which is enough for most developers. Also, when using AWS Lambda you don't need to manage any SSL certificates since the Alexa Skills Kit is a trusted trigger.

While setting up an Alexa skill using AWS Lambda, Node.js and the Alexa Skills Kit has been a simple process, the actual amount of code you have had to write has not. We have seen a large amount of time spent in Alexa skills on handling session attributes, skill state persistence, response building and behavior modeling. With that in mind the Alexa team set out to build an Alexa Skills Kit SDK specifically for Node.js that will help you avoid common hang-ups and focus on your skill's logic instead of boilerplate code.

### Enabling Faster Alexa Skill Development with the Alexa Skills Kit SDK for Node.js (alexa-sdk)

With the new alexa-sdk, our goal is to help you build skills faster while allowing you to avoid unneeded complexity. Today, we are launching the SDK with the following capabilities:

- Hosted as an NPM package allowing simple deployment to any Node.js environment
- Ability to build Alexa responses using built-in events
- Helper events for new sessions and unhandled events that can act as a 'catch-all' events
- Helper functions to build state-machine based Intent handling
  - This makes it possible to define different event handlers based on the current state of the skill
- Simple configuration to enable attribute persistence with DynamoDB
- All speech output is automatically wrapped as SSML
- Lambda event and context objects are fully available via `this.event` and `this.context`
- Ability to override built-in functions giving you more flexibility on how you manage state or build responses. For example, saving state attributes to AWS S3.

### Installing and Working with the Alexa Skills Kit SDK for Node.js (alexa-sdk)

The alexa-sdk is immediately available on [github](https://github.com/alexa/alexa-skills-kit-sdk-for-nodejs) and can be deployed as a node package using the following command from within your Node.js environment:
```bash
npm install --save alexa-sdk
```

In order to start using the alexa-sdk first import the library. To do this within your own project simply create a file named index.js and add the following to it:
```javascript
var Alexa = require('alexa-sdk');

exports.handler = function(event, context, callback){
    var alexa = Alexa.handler(event, context, callback);
};
```
This will import alexa-sdk and set up an `Alexa` object for us to work with. Next, we need to handle the intents for our skill. Alexa-sdk makes it simple to have a function fire an Intent. For example, to create a handler for 'HelloWorldIntent' we simply add the following:
```javascript
var handlers = {

    'HelloWorldIntent': function () {
        this.emit(':tell', 'Hello World!');
    }

};
```
Notice the new syntax above for ':tell'? Alexa-sdk follows a tell/ask response methodology for generating your [outputSpeech response objects](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/alexa-skills-kit-interface-reference#Response%20Format). To ask the user for information we would instead use an `:ask` action. The difference between `:ask` and `:tell` is that after a `:tell` action, the session is ended without waiting for the user to provide more input.
```javascript
this.emit(':ask', 'What would you like to do?', 'Please say that again?');
```
In fact, many of the responses follow this same syntax! Here are some additional examples for common skill responses:
```javascript
var speechOutput = 'Hello world!';
var repromptSpeech = 'Hello again!';

this.emit(':tell', speechOutput);

this.emit(':ask', speechOutput, repromptSpeech);

var cardTitle = 'Hello World Card';
var cardContent = 'This text will be displayed in the companion app card.';

var imageObj = {
    smallImageUrl: 'https://imgs.xkcd.com/comics/standards.png',
    largeImageUrl: 'https://imgs.xkcd.com/comics/standards.png'
};

var permissionArray = ['read::alexa:device:all:address'];

var updatedIntent = this.event.request.intent;

var slotToElicit = "Slot to elicit";

var slotToConfirm = "Slot to confirm";

this.emit(':askWithCard', speechOutput, repromptSpeech, cardTitle, cardContent, imageObj);

this.emit(':tellWithCard', speechOutput, cardTitle, cardContent, imageObj);

this.emit(':tellWithLinkAccountCard', speechOutput);

this.emit(':askWithLinkAccountCard', speechOutput);

this.emit(':tellWithPermissionCard', speechOutput, permissionArray);

this.emit(':delegate', updatedIntent);

this.emit(':elicitSlot', slotToElicit, speechOutput, repromptSpeech, updatedIntent);

this.emit(':elicitSlotWithCard', slotToElicit, speechOutput, repromptSpeech, cardTitle, cardContent, updatedIntent, imageObj);

this.emit(':confirmSlot', slotToConfirm, speechOutput, repromptSpeech, updatedIntent);

this.emit(':confirmSlotWithCard', slotToConfirm, speechOutput, repromptSpeech, cardTitle, cardContent, updatedIntent, imageObj);

this.emit(':confirmIntent', speechOutput, repromptSpeech, updatedIntent);

this.emit(':confirmIntentWithCard', speechOutput, repromptSpeech, cardTitle, cardContent, updatedIntent, imageObj);

this.emit(':responseReady'); // Called after the response is built but before it is returned to the Alexa service. Calls :saveState. Can be overridden.

this.emit(':saveState', false); // Handles saving the contents of this.attributes and the current handler state to DynamoDB and then sends the previously built response to the Alexa service. Override if you wish to use a different persistence provider. The second attribute is optional and can be set to 'true' to force saving.

this.emit(':saveStateError'); // Called if there is an error while saving state. Override to handle any errors yourself.
```
Once we have set up our event handlers we need to register them using the registerHandlers function of the alexa object we just created.
```javascript
  exports.handler = function(event, context, callback) {
      var alexa = Alexa.handler(event, context, callback);
      alexa.registerHandlers(handlers);
  };
```
You can also register multiple handler objects at once:
```javascript
  alexa.registerHandlers(handlers, handlers2, handlers3, ...);
```
The handlers you define can call each other, making it possible to ensure your responses are uniform.  Here is an example where our LaunchRequest and IntentRequest (of HelloWorldIntent) both return the same 'Hello World' message.
```javascript
var handlers = {
    'LaunchRequest': function () {
        this.emit('HelloWorldIntent');
    },

    'HelloWorldIntent': function () {
        this.emit(':tell', 'Hello World!');
    }
 };
```
Once you are done registering all of your intent handler functions, you simply use the execute function from the alexa object to run your skill's logic. The final line would look like this:
```javascript
exports.handler = function(event, context, callback) {
    var alexa = Alexa.handler(event, context, callback);
    alexa.registerHandlers(handlers);
    alexa.execute();
};
```
You can download a full working sample off github. We have also updated the following Node.js sample skills to work with the alexa-sdk: [Fact](https://github.com/alexa/skill-sample-nodejs-fact), [HelloWorld](https://github.com/alexa/skill-sample-nodejs-hello-world), [HighLow](https://github.com/alexa/skill-sample-nodejs-highlowgame), [HowTo](https://github.com/alexa/skill-sample-nodejs-howto) and [Trivia](https://github.com/alexa/skill-sample-nodejs-trivia).

Note: for specifications regarding the ```imgObj``` please see [here](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/providing-home-cards-for-the-amazon-alexa-app).

### Making Skill State Management Simpler

Alexa-sdk will route incoming intents to the correct function handler based on state. State is stored as a string in your session attributes indicating the current state of the skill. You can emulate the built-in intent routing by appending the state string to the intent name when defining your intent handlers, but alexa-sdk helps do that for you.

For example, let's create a simple number-guessing game with 'start' and 'guess' states based on our previous example of handling a `NewSession` event.
```javascript
var states = {
    GUESSMODE: '_GUESSMODE', // User is trying to guess the number.
    STARTMODE: '_STARTMODE'  // Prompt the user to start or restart the game.
};

var newSessionHandlers = {

     // This will short-cut any incoming intent or launch requests and route them to this handler.
    'NewSession': function() {
        if(Object.keys(this.attributes).length === 0) { // Check if it's the first time the skill has been invoked
            this.attributes['endedSessionCount'] = 0;
            this.attributes['gamesPlayed'] = 0;
        }
        this.handler.state = states.STARTMODE;
        this.emit(':ask', 'Welcome to High Low guessing game. You have played '
            + this.attributes['gamesPlayed'].toString() + ' times. Would you like to play?',
            'Say yes to start the game or no to quit.');
    }
};
```
Notice that when a new session is created we simply set the state of our skill into `STARTMODE` using this.handler.state. The skills state will automatically be persisted in your skill's session attributes, and will be optionally persisted across sessions if you set a DynamoDB table.

It is also important point out that `NewSession` is a great catch-all behavior and a good entry point but it is not required. `NewSession` will only be invoked if a handler with that name is defined. Each state you define can have its own `NewSession` handler which will be invoked if you are using the built-in persistence. In the above example we could define different `NewSession` behavior for both `states.STARTMODE` and `states.GUESSMODE` giving us added flexibility.

In order to define intents that will respond to the different states of our skill, we need to use the `Alexa.CreateStateHandler` function. Any intent handlers defined here will only work when the skill is in a specific state, giving us even greater flexibility!

For example, if we are in the `GUESSMODE` state we defined above we want to handle a user responding to a question. This can be done using StateHandlers like this:
```javascript
var guessModeHandlers = Alexa.CreateStateHandler(states.GUESSMODE, {

    'NewSession': function () {
        this.handler.state = '';
        this.emitWithState('NewSession'); // Equivalent to the Start Mode NewSession handler
    },

    'NumberGuessIntent': function() {
        var guessNum = parseInt(this.event.request.intent.slots.number.value);
        var targetNum = this.attributes['guessNumber'];

        console.log('user guessed: ' + guessNum);

        if(guessNum > targetNum){
            this.emit('TooHigh', guessNum);
        } else if( guessNum < targetNum){
            this.emit('TooLow', guessNum);
        } else if (guessNum === targetNum){
            // With a callback, use the arrow function to preserve the correct 'this' context
            this.emit('JustRight', () => {
                this.emit(':ask', guessNum.toString() + 'is correct! Would you like to play a new game?',
                'Say yes to start a new game, or no to end the game.');
            });
        } else {
            this.emit('NotANum');
        }
    },

    'AMAZON.HelpIntent': function() {
        this.emit(':ask', 'I am thinking of a number between zero and one hundred, try to guess and I will tell you' +
            ' if it is higher or lower.', 'Try saying a number.');
    },

    'SessionEndedRequest': function () {
        console.log('session ended!');
        this.attributes['endedSessionCount'] += 1;
        this.emit(':saveState', true); // Be sure to call :saveState to persist your session attributes in DynamoDB
    },

    'Unhandled': function() {
        this.emit(':ask', 'Sorry, I didn\'t get that. Try saying a number.', 'Try saying a number.');
    }

});
```
On the flip side, if I am in `STARTMODE` I can define my `StateHandlers` to be the following:

```javascript
var startGameHandlers = Alexa.CreateStateHandler(states.STARTMODE, {

    'NewSession': function () {
        this.emit('NewSession'); // Uses the handler in newSessionHandlers
    },

    'AMAZON.HelpIntent': function() {
        var message = 'I will think of a number between zero and one hundred, try to guess and I will tell you if it' +
            ' is higher or lower. Do you want to start the game?';
        this.emit(':ask', message, message);
    },

    'AMAZON.YesIntent': function() {
        this.attributes['guessNumber'] = Math.floor(Math.random() * 100);
        this.handler.state = states.GUESSMODE;
        this.emit(':ask', 'Great! ' + 'Try saying a number to start the game.', 'Try saying a number.');
    },

    'AMAZON.NoIntent': function() {
        this.emit(':tell', 'Ok, see you next time!');
    },

    'SessionEndedRequest': function () {
        console.log('session ended!');
        this.attributes['endedSessionCount'] += 1;
        this.emit(':saveState', true);
    },

    'Unhandled': function() {
        var message = 'Say yes to continue, or no to end the game.';
        this.emit(':ask', message, message);
    }
});
```
Take a look at how `AMAZON.YesIntent` and `AMAZON.NoIntent` are not defined in the `guessModeHandlers` object, since it doesn't make sense for a 'yes' or 'no' response in this state. Those intents will be caught by the `Unhandled` handler.

Also, notice the different behavior for `NewSession` and `Unhandled` across both states? In this game, we 'reset' the state by calling a `NewSession` handler defined in the `newSessionHandlers` object. You can also skip defining it and alexa-sdk will call the intent handler for the current state. Just remember to register your State Handlers before you call `alexa.execute()` or they will not be found.

Your attributes will be automatically saved when you end the session, but if the user ends the session you have to emit the `:saveState` event (`this.emit(':saveState', true)`) to force a save. You should do this in your `SessionEndedRequest` handler which is called when the user ends the session by saying 'quit' or timing out. Take a look at the example above.

We have wrapped up the above example into a high/low number guessing game skill you can [download here](https://github.com/alexa/skill-sample-nodejs-highlowgame).

### Persisting Skill Attributes through DynamoDB

Many of you would like to persist your session attribute values into storage for further use. Alexa-sdk integrates directly with [Amazon DynamoDB](https://aws.amazon.com/dynamodb/) (a NoSQL database service) to enable you to do this with a single line of code.

Simply set the name of the DynamoDB table on your alexa object before you call alexa.execute.
```javascript
exports.handler = function (event, context, callback) {
    var alexa = Alexa.handler(event, context, callback);
    alexa.appId = appId;
    alexa.dynamoDBTableName = 'YourTableName'; // That's it!
    alexa.registerHandlers(State1Handlers, State2Handlers);
    alexa.execute();
};
```

Then later on to set a value you simply need to call into the attributes property of the alexa object. No more separate `put` and `get` functions!
```javascript
this.attributes['yourAttribute'] = 'value';
```

You can [create the table manually](http://docs.aws.amazon.com/amazondynamodb/latest/developerguide/SampleData.CreateTables.html) beforehand or simply give your Lambda function DynamoDB [create table permissions](http://docs.aws.amazon.com/amazondynamodb/latest/APIReference/API_CreateTable.html) and it will happen automatically. Just remember it can take a minute or so for the table to be created on the first invocation. If you create the table manually, the Primary Key must be a string value called "userId".

### Generating your own responses

Normally emitting a response event like `this.emit(':tell', speechOutput, repromptSpeech)` will set up the response and send it to Alexa for you, using any speech or card values you pass it. If you want to manually create your own responses, you can use `this.response` to help. `this.response` contains a series of functions, that you can use to set the different properties of the response. This allows you to take advantage of the Alexa Skills Kit's built-in audio player support. Once you've set up your response, you can just call `this.emit(':responseReady')` to send your response to Alexa. The functions within `this.response` are also chainable, so you can use as many as you want in a row.

For example, the below code is equivalent to `this.emit(':ask', 'foo', 'bar');`

```javascript
this.response.speak('foo').listen('bar');
this.emit(':responseReady');
```

Here's the API for using `this.response`:

- `this.response.speak(outputSpeech)`: sets the first speech output of the response to `outputSpeech`.
- `this.response.listen(repromptSpeech)`: sets the reprompt speech of the response to `repromptSpeech` and `shouldEndSession` to false. Unless this function is called, `this.response` will set `shouldEndSession` to true.
- `this.response.cardRenderer(cardTitle, cardContent, cardImage)`: sets the card in the response to have the title `cardTitle`, the content `cardContent`, and the image `cardImage`. `cardImage` can be excluded, but if it's included it must be of the correct image object format, detailed above.
- `this.response.linkAccountCard()`: sets the type of the card to a 'Link Account' card.
- `this.response.audioPlayer(directiveType, behavior, url, token, expectedPreviousToken, offsetInMilliseconds)`: sets the audioPlayer directive using the provided parameters. See the [audioPlayer interface reference](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/custom-audioplayer-interface-reference) for more details. Options for `directiveType` are `'play'`, `'stop'` and `'clearqueue'`. Inputting any other value is equivalent to `'clearqueue'`.
    - If you use `'play'`, you need to include all the parameters after: `behavior, url, token, expectedPreviousToken, offsetInMilliseconds`.
    - If you use `'stop'`, no further parameters are needed.
    - If you use `'clearQueue'`, you only need to include the `behaviour` parameter.
- `this.response.audioPlayerPlay(behavior, url, token, expectedPreviousToken, offsetInMilliseconds)`: sets the audioPlayer directive using the provided parameters, and `AudioPlayer.Play` as the directive type. This will make the audio player play an audio file at a requested URL.
- `this.response.audioPlayerStop()` sets the directive type to `AudioPlayer.Stop`. This will make the audio player stop.
- `this.response.audioPlayerClearQueue(clearBehaviour)` sets the directive type to `AudioPlayer.ClearQueue` and sets the clear behaviour of the directive. Options for this value are `'CLEAR_ENQUEUED'` and `'CLEAR_ALL'`. This will either clear the queue and continue the current stream, or clear the queue and stop the current stream.
.- `this.response.renderTemplate(template)` adds a `Display.RenderTemplate` Directive to the response with the specified template object. See the [Display.RenderTemplate reference](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/display-interface-reference) for more information.
- `this.response.hint(hintText)` adds a `Hint` Directive to the response with the specified hintText. See the [Hint Directive reference](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/display-interface-reference#hint-directive) for more information
- `this.response.playVideo(url, metadata)` adds a `VideoApp.Play` directive.
  - `url (string)` - url to the video source. See the [VideoApp Interface reference](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/videoapp-interface-reference) for details on supported video formats.
  - `metadata ({ title : string, subtitle : string }) [optional]` - specify the title and secondary title to show with the video

When you've set up your response, simply call `this.emit(':responseReady');` to send your response off.

### Tips

- When any of the response events are emitted `:ask`, `:tell`, `:askWithCard`, etc. The lambda context.succeed() method is called, which immediately stops processing of any further background tasks. Any asynchronous jobs that are still will not be completed and any lines of code below the response emit statement will not be executed. This is not the case for non responding events like `:saveState`.
- In order to "transfer" a call from one state handler to another, `this.handler.state` needs to be set to the name of the target state. If the target state is "", then `this.emit("TargetHandlerName")` should be called. For any other states, `this.emitWithState("TargetHandlerName")` must be called instead.
- The contents of the prompt and repompt values get wrapped in SSML tags. This means that any special XML characters within the value need to be escape coded. For example, this.emit(":ask", "I like M&M's") will cause a failure because the `&` character needs to be encoded as `&amp;`. Other characters that need to be encoded include: `<` -> `&lt;`, and `>` -> `&gt;`.

### Adding Multi-Language Support for Skill
Let's take the Hello World example here. Define all user-facing language strings in the following format.
```javascript
var languageStrings = {
    'en-GB': {
        'translation': {
            'SAY_HELLO_MESSAGE' : 'Hello World!'
        }
    },
    'en-US': {
        'translation': {
            'SAY_HELLO_MESSAGE' : 'Hello World!'
        }
    },
    'de-DE': {
        'translation': {
            'SAY_HELLO_MESSAGE' : 'Hallo Welt!'
        }
    }
};
```

To enable string internationalization features in Alexa-sdk, set resources to the object we created above.
```javascript
exports.handler = function(event, context, callback) {
    var alexa = Alexa.handler(event, context);
    alexa.appId = appId;
    // To enable string internationalization (i18n) features, set a resources object.
    alexa.resources = languageStrings;
    alexa.registerHandlers(handlers);
    alexa.execute();
};
```

Once you are done defining and enabling language strings, you can access these strings using the this.t() function. Strings will be rendered in the language that matches the locale of the incoming request.
```javascript
var handlers = {
    'LaunchRequest': function () {
        this.emit('SayHello');
    },
    'HelloWorldIntent': function () {
        this.emit('SayHello');
    },
    'SayHello': function () {
        this.emit(':tell', this.t('SAY_HELLO_MESSAGE'));
    }
};
```
For more infomation about developing and deploying skills in multiple languages, please go [here](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/developing-skills-in-multiple-languages).

### Device ID Support
When a customer enables your Alexa skill, your skill can obtain the customer’s permission to use address data associated with the customer’s Alexa device. You can then use this address data to provide key functionality for the skill, or to enhance the customer experience.

The `deviceId` is now exposed through the context object in each request and can be accessed in any intent handler through `this.event.context.System.device.deviceId`. See the [Address API sample skill](https://github.com/alexa/skill-sample-node-device-address-api) to see how we leveraged the deviceId and the Address API to use a user's device address in a skill.

### Speechcons (Interjections)

[Speechcons](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/speechcon-reference) are special words and phrases that Alexa pronounces more expressively. In order to use them you can just include the SSML markup in the text to emit.

* `this.emit(':tell', 'Sometimes when I look at the Alexa skills you have all taught me, I just have to say, <say-as interpret-as="interjection">Bazinga.</say-as> ');`
* `this.emit(':tell', '<say-as interpret-as="interjection">Oh boy</say-as><break time="1s"/> this is just an example.');`

_Speechcons are supported for English (US), English (UK), and German._

### Dialog Management Support for Skill
The `Dialog` interface provides directives for managing a multi-turn conversation between your skill and the user. You can use the directives to ask the user for the information you need to fulfill their request. See the [Dialog Interface](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/dialog-interface-reference) and [Skill Editor](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/ask-define-the-vui-with-gui) documentation for more information on how to use dialog directives.

You can use `this.event.request.dialogState` to access current `dialogState`.

#### Delegate Directive
Sends Alexa a command to handle the next turn in the dialog with the user. You can use this directive if the skill has a dialog model and the current status of the dialog (`dialogState`) is either `STARTED` or `IN_PROGRESS`. You cannot emit this directive if the `dialogState` is `COMPLETED`.

You can use `this.emit(':delegate')` to send delegate directive response.
```javascript
var handlers = {
    'BookFlightIntent': function () {
        if (this.event.request.dialogState === 'STARTED') {
            var updatedIntent = this.event.request.intent;
            // Pre-fill slots: update the intent object with slot values for which
            // you have defaults, then emit :delegate with this updated intent.
            updatedIntent.slots.SlotName.value = 'DefaultValue';
            this.emit(':delegate', updatedIntent);
        } else if (this.event.request.dialogState !== 'COMPLETED'){
            this.emit(':delegate');
        } else {
            // All the slots are filled (And confirmed if you choose to confirm slot/intent)
            handlePlanMyTripIntent();
        }
    }
};
```

#### Elicit Slot Directive
Sends Alexa a command to ask the user for the value of a specific slot. Specify the name of the slot to elicit in the `slotToElicit`. Provide a prompt to ask the user for the slot value in `speechOutput`.

You can use `this.emit(':elicitSlot', slotToElicit, speechOutput, repromptSpeech, updatedIntent)` or `this.emit(':elicitSlotWithCard', slotToElicit, speechOutput, repromptSpeech, cardTitle, cardContent, updatedIntent, imageObj)` to send elicit slot directive response.

When using `this.emit(':elicitSlotWithCard', slotToElicit, speechOutput, repromptSpeech, cardTitle, cardContent, updatedIntent, imageObj)`, `updatedIntent` and `imageObj` are optional parameters. You can set them to `null` or not pass them.
```javascript
var handlers = {
    'BookFlightIntent': function () {
        var intentObj = this.event.request.intent;
        if (!intentObj.slots.Source.value) {
            var slotToElicit = 'Source';
            var speechOutput = 'Where would you like to fly from?';
            var repromptSpeech = speechOutput;
            this.emit(':elicitSlot', slotToElicit, speechOutput, repromptSpeech);
        } else if (!intentObj.slots.Destination.value) {
            var slotToElicit = 'Destination';
            var speechOutput = 'Where would you like to fly to?';
            var repromptSpeech = speechOutput;
            var cardContent = 'What is the destination?';
            var cardTitle = 'Destination';
            var updatedIntent = intentObj;
            // An intent object representing the intent sent to your skill.
            // You can use this property set or change slot values and confirmation status if necessary.
            var imageObj = {
                smallImageUrl: 'https://imgs.xkcd.com/comics/standards.png',
                largeImageUrl: 'https://imgs.xkcd.com/comics/standards.png'
            };
            this.emit(':elicitSlotWithCard', slotToElicit, speechOutput, repromptSpeech, cardTitle, cardContent, updatedIntent, imageObj);
        } else {
            handlePlanMyTripIntentAllSlotsAreFilled();
        }
    }
};
```

#### Confirm Slot Directive
Sends Alexa a command to confirm the value of a specific slot before continuing with the dialog. Specify the name of the slot to confirm in the `slotToConfirm`. Provide a prompt to ask the user for confirmation in `speechOutput`.

You can use `this.emit(':confirmSlot', slotToConfirm, speechOutput, repromptSpeech, updatedIntent)` or `this.emit(':confirmSlotWithCard', slotToConfirm, speechOutput, repromptSpeech, cardTitle, cardContent, updatedIntent, imageObj)` to send confirm slot directive response.

When using `this.emit(':confirmSlotWithCard', slotToConfirm, speechOutput, repromptSpeech, cardTitle, cardContent, updatedIntent, imageObj)`, `updatedIntent` and `imageObj` are optional parameters. You can set them to `null` or not pass them.
```javascript
var handlers = {
    'BookFlightIntent': function () {
        var intentObj = this.event.request.intent;
        if (intentObj.slots.Source.confirmationStatus !== 'CONFIRMED') {
            if (intentObj.slots.Source.confirmationStatus !== 'DENIED') {
                // Slot value is not confirmed
                var slotToConfirm = 'Source';
                var speechOutput = 'You want to fly from ' + intentObj.slots.Source.value + ', is that correct?';
                var repromptSpeech = speechOutput;
                this.emit(':confirmSlot', slotToConfirm, speechOutput, repromptSpeech);
            } else {
                // Users denies the confirmation of slot value
                var slotToElicit = 'Source';
                var speechOutput = 'Okay, Where would you like to fly from?';
                this.emit(':elicitSlot', slotToElicit, speechOutput, speechOutput);
            }
        } else if (intentObj.slots.Destination.confirmationStatus !== 'CONFIRMED') {
            if (intentObj.slots.Destination.confirmationStatus !== 'DENIED') {
                var slotToConfirm = 'Destination';
                var speechOutput = 'You would like to fly to ' + intentObj.slots.Destination.value + ', is that correct?';
                var repromptSpeech = speechOutput;
                var cardContent = speechOutput;
                var cardTitle = 'Confirm Destination';
                this.emit(':confirmSlotWithCard', slotToConfirm, speechOutput, repromptSpeech, cardTitle, cardContent);
            } else {
                var slotToElicit = 'Destination';
                var speechOutput = 'Okay, Where would you like to fly to?';
                var repromptSpeech = speechOutput;
                this.emit(':elicitSlot', slotToElicit, speechOutput, repromptSpeech);
            }
        } else {
            handlePlanMyTripIntentAllSlotsAreConfirmed();
        }
    }
};
```

#### Confirm Intent Directive
Sends Alexa a command to confirm the all the information the user has provided for the intent before the skill takes action. Provide a prompt to ask the user for confirmation in `speechOutput`. Be sure to repeat back all the values the user needs to confirm in the prompt.

You can use `this.emit(':confirmIntent', speechOutput, repromptSpeech, updatedIntent)` or `this.emit(':confirmIntentWithCard', speechOutput, repromptSpeech, cardTitle, cardContent, updatedIntent, imageObj)` to send confirm intent directive response.

When using `this.emit(':confirmIntentWithCard', speechOutput, repromptSpeech, cardTitle, cardContent, updatedIntent, imageObj)`, `updatedIntent` and `imageObj` are optional parameters. You can set them to `null` or not pass them.
```javascript
var handlers = {
    'BookFlightIntent': function () {
        var intentObj = this.event.request.intent;
        if (intentObj.confirmationStatus !== 'CONFIRMED') {
            if (intentObj.confirmationStatus !== 'DENIED') {
                // Intent is not confirmed
                var speechOutput = 'You would like to book flight from ' + intentObj.slots.Source.value + ' to ' +
                intentObj.slots.Destination.value + ', is that correct?';
                var cardTitle = 'Booking Summary';
                var repromptSpeech = speechOutput;
                var cardContent = speechOutput;
                this.emit(':confirmIntentWithCard', speechOutput, repromptSpeech, cardTitle, cardContent);
            } else {
                // Users denies the confirmation of intent. May be value of the slots are not correct.
                handleIntentConfimationDenial();
            }
        } else {
            handlePlanMyTripIntentAllSlotsAndIntentAreConfirmed();
        }
    }
};
```

### Building Echo Show templates
Template Builders are now included in alexa-sdk in the templateBuilders namespace. These provide a set of helper methods to build the JSON template for the Display.RenderTemplate directive. In the example below we use the BodyTemplate1Builder.

```javascript
const Alexa = require('alexa-sdk');
// utility methods for creating Image and TextField objects
const makePlainText = Alexa.utils.TextUtils.makePlainText;
const makeImage = Alexa.utils.ImageUtils.makeImage;

// ...
'LaunchRequest' : function() {
    const builder = new Alexa.templateBuilders.BodyTemplate1Builder();

    let template = builder.setTitle('My BodyTemplate1')
                          .setBackgroundImage(makeImage('http://url/to/my/img.png'))
                          .setTextContent(makePlainText('Text content'))
                          .build();

    this.response.speak('Rendering a template!')
                 .renderTemplate(template);
    this.emit(':responseReady');
}
```

We've added helper utility methods to build Image and TextField objects. They are located in the `Alexa.utils` namespace.

```javascript
const ImageUtils = require('alexa-sdk').utils.ImageUtils;

// Outputs an image with a single source
ImageUtils.makeImage(url, widthPixels, heightPixels, size, description)
/**
Outputs {
    contentDescription : '<description>'
    sources : [
        {
            url : '<url>',
            widthPixels : '<widthPixels>',
            heightPixels : '<heightPixels>',
            size : '<size>'
        }
    ]
}
*/

ImageUtils.makeImages(imgArr, description)
/**
Outputs {
    contentDescription : '<description>'
    sources : <imgArr> // array of {url, size, widthPixels, heightPixels}
}
*/


const TextUtils = require('alexa-sdk').utils.TextUtils;

TextUtils.makePlainText('my plain text field');
/**
Outputs {
    text : 'my plain text field',
    type : 'PlainText'
}
*/

TextUtils.makeRichText('my rich text field');
/**
Outputs {
    text : 'my rich text field',
    type : 'RichText'
}
*/

```

### Building Multi-modal skills

Sending a Display.RenderTemplate directive to a headless device (like an echo) will result in an invalid directive error being thrown. To check whether a device supports a particular directive, you can check the device's supportedInterfaces property.

```javascript
let handler = {
    'LaunchRequest' : function() {

        this.response.speak('Hello there');

        // Display.RenderTemplate directives can be added to the response
        if (this.event.context.System.device.supportedInterfaces.Display) {
            //... build mytemplate using TemplateBuilder
            this.response.renderTemplate(myTemplate);
        }

        this.emit(':responseReady');
    }
}
```

Similarly for video, you check if VideoPlayer is a supported interface of the device

```javascript
let handler = {
    'PlayVideoIntent' : function() {

        // VideoApp.Play directives can be added to the response
        if (this.event.context.System.device.supportedInterfaces.VideoPlayer) {
            this.response.playVideo('http://path/to/my/video.mp4');
        } else {
            this.response.speak("The video cannot be played on your device. " +
                "To watch this video, try launching the skill from your echo show device.");
        }

        this.emit(':responseReady');
    }
}
```

### Setting up your development environment
 - Requirements
    - Gulp & mocha  ```npm install -g gulp mocha```
    - Run npm install to pull down stuff
    - run gulp to run tests/linter (soon)

### Next Steps

Try extending the HighLow game:

- Have it store your average number of guesses per game
- Add [sound effects](https://developer.amazon.com/public/solutions/alexa/alexa-skills-kit/docs/speech-synthesis-markup-language-ssml-reference#audio)
- Give the player a limited amount of guesses

For more information about getting started with the Alexa Skills Kit, check out the following additional assets:

 [Alexa Dev Chat Podcast](http://bit.ly/alexadevchat)

 [Alexa Training with Big Nerd Ranch](https://developer.amazon.com/public/community/blog/tag/Big+Nerd+Ranch)

 [Alexa Skills Kit (ASK)](https://developer.amazon.com/ask)

 [Alexa Developer Forums](https://forums.developer.amazon.com/forums/category.jspa?categoryID=48)

 [Training for the Alexa Skills Kit](https://developer.amazon.com/alexa-skills-kit/alexa-skills-developer-training)

-Dave ( [@TheDaveDev](http://twitter.com/thedavedev))
