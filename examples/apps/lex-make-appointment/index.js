'use strict';

/**
 * This code sample demonstrates an implementation of the Lex Code Hook Interface
 * in order to serve a bot which manages dentist appointments.
 * Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
 * as part of the 'MakeAppointment' template.
 *
 * For instructions on how to set up and test this bot, as well as additional samples,
 *  visit the Lex Getting Started documentation.
 */


// --------------- Helpers to build responses which match the structure of the necessary dialog actions -----------------------

function elicitSlot(sessionAttributes, intentName, slots, slotToElicit, message, responseCard) {
    return {
        sessionAttributes,
        dialogAction: {
            type: 'ElicitSlot',
            intentName,
            slots,
            slotToElicit,
            message,
            responseCard,
        },
    };
}

function confirmIntent(sessionAttributes, intentName, slots, message, responseCard) {
    return {
        sessionAttributes,
        dialogAction: {
            type: 'ConfirmIntent',
            intentName,
            slots,
            message,
            responseCard,
        },
    };
}

function close(sessionAttributes, fulfillmentState, message, responseCard) {
    return {
        sessionAttributes,
        dialogAction: {
            type: 'Close',
            fulfillmentState,
            message,
            responseCard,
        },
    };
}

function delegate(sessionAttributes, slots) {
    return {
        sessionAttributes,
        dialogAction: {
            type: 'Delegate',
            slots,
        },
    };
}

// Build a responseCard with a title, subtitle, and an optional set of options which should be displayed as buttons.
function buildResponseCard(title, subTitle, options) {
    let buttons = null;
    if (options != null) {
        buttons = [];
        for (let i = 0; i < Math.min(5, options.length); i++) {
            buttons.push(options[i]);
        }
    }
    return {
        contentType: 'application/vnd.amazonaws.card.generic',
        version: 1,
        genericAttachments: [{
            title,
            subTitle,
            buttons,
        }],
    };
}

// ---------------- Helper Functions --------------------------------------------------

function incrementTimeByThirtyMins(time) {
    if (time.length !== 5) {
        // Not a valid time
    }
    const hour = parseInt(time.substring(0, 2), 10);
    const minute = parseInt(time.substring(3), 10);
    return (minute === 30) ? `${hour + 1}:00` : `${hour}:30`;
}

// Returns a random integer between min (included) and max (excluded)
function getRandomInt(min, max) {
    const minInt = Math.ceil(min);
    const maxInt = Math.floor(max);
    return Math.floor(Math.random() * (maxInt - minInt)) + minInt;
}

/**
 * Helper function which in a full implementation would  feed into a backend API to provide query schedule availability.
 * The output of this function is an array of 30 minute periods of availability, expressed in ISO-8601 time format.
 *
 * In order to enable quick demonstration of all possible conversation paths supported in this example, the function
 * returns a mixture of fixed and randomized results.
 *
 * On Mondays, availability is randomized; otherwise there is no availability on Tuesday / Thursday and availability at
 * 10:00 - 10:30 and 4:00 - 5:00 on Wednesday / Friday.
 */
function getAvailabilities(date) {
    const dayOfWeek = new Date(date).getDay();
    const availabilities = [];
    const availableProbability = 0.3;
    if (dayOfWeek === 1) {
        let startHour = 10;
        while (startHour <= 16) {
            if (Math.random() < availableProbability) {
                // Add an availability window for the given hour, with duration determined by another random number.
                const appointmentType = getRandomInt(1, 4);
                if (appointmentType === 1) {
                    availabilities.push(`${startHour}:00`);
                } else if (appointmentType === 2) {
                    availabilities.push(`${startHour}:30`);
                } else {
                    availabilities.push(`${startHour}:00`);
                    availabilities.push(`${startHour}:30`);
                }
            }
            startHour++;
        }
    }
    if (dayOfWeek === 3 || dayOfWeek === 5) {
        availabilities.push('10:00');
        availabilities.push('16:00');
        availabilities.push('16:30');
    }
    return availabilities;
}

// Helper function to check if the given time and duration fits within a known set of availability windows.
// Duration is assumed to be one of 30, 60 (meaning minutes).  Availabilities is expected to contain entries of the format HH:MM.
function isAvailable(time, duration, availabilities) {
    if (duration === 30) {
        return (availabilities.indexOf(time) !== -1);
    } else if (duration === 60) {
        const secondHalfHourTime = incrementTimeByThirtyMins(time);
        return (availabilities.indexOf(time) !== -1 && availabilities.indexOf(secondHalfHourTime) !== -1);
    }
    // Invalid duration ; throw error.  We should not have reached this branch due to earlier validation.
    throw new Error(`Was not able to understand duration ${duration}`);
}

function getDuration(appointmentType) {
    const appointmentDurationMap = { cleaning: 30, 'root canal': 60, whitening: 30 };
    return appointmentDurationMap[appointmentType];
}

// Helper function to return the windows of availability of the given duration, when provided a set of 30 minute windows.
function getAvailabilitiesForDuration(duration, availabilities) {
    const durationAvailabilities = [];
    let startTime = '10:00';
    while (startTime !== '17:00') {
        if (availabilities.indexOf(startTime) !== -1) {
            if (duration === 30) {
                durationAvailabilities.push(startTime);
            } else if (availabilities.indexOf(incrementTimeByThirtyMins(startTime)) !== -1) {
                durationAvailabilities.push(startTime);
            }
        }
        startTime = incrementTimeByThirtyMins(startTime);
    }
    return durationAvailabilities;
}

function buildValidationResult(isValid, violatedSlot, messageContent) {
    return {
        isValid,
        violatedSlot,
        message: { contentType: 'PlainText', content: messageContent },
    };
}

function validateBookAppointment(appointmentType, date, time) {
    if (appointmentType && !getDuration(appointmentType)) {
        return buildValidationResult(false, 'AppointmentType', 'I did not recognize that, can I book you a root canal, cleaning, or whitening?');
    }
    if (time) {
        if (time.length !== 5) {
            return buildValidationResult(false, 'Time', 'I did not recognize that, what time would you like to book your appointment?');
        }
        const hour = parseInt(time.substring(0, 2), 10);
        const minute = parseInt(time.substring(3), 10);
        if (isNaN(hour) || isNaN(minute)) {
            return buildValidationResult(false, 'Time', 'I did not recognize that, what time would you like to book your appointment?');
        }
        if (hour < 10 || hour > 16) {
            // Outside of business hours
            return buildValidationResult(false, 'Time', 'Our business hours are ten a.m. to five p.m.  What time works best for you?');
        }
        if ([30, 0].indexOf(minute) === -1) {
            // Must be booked on the hour or half hour
            return buildValidationResult(false, 'Time', 'We schedule appointments every half hour, what time works best for you?');
        }
    }
    if (date) {
        if (new Date(date) < new Date()) {
            return buildValidationResult(false, 'Date', 'Your appointment date is in the past!  Can you try a different date?');
        } else if (new Date(date).getDay() === 0 || new Date(date).getDay() === 6) {
            return buildValidationResult(false, 'Date', 'Our office is not open on the weekends, can you provide a work day?');
        }
    }
    return buildValidationResult(true, null, null);
}

function buildTimeOutputString(time) {
    const hour = parseInt(time.substring(0, 2), 10);
    const minute = time.substring(3);
    if (hour > 12) {
        return `${hour - 12}:${minute} p.m.`;
    } else if (hour === 12) {
        return `12:${minute} p.m.`;
    } else if (hour === 0) {
        return `12:${minute} a.m.`;
    }
    return `${hour}:${minute} a.m.`;
}

// Build a string eliciting for a possible time slot among at least two availabilities.
function buildAvailableTimeString(availabilities) {
    let prefix = 'We have availabilities at ';
    if (availabilities.length > 3) {
        prefix = 'We have plenty of availability, including ';
    }
    prefix += buildTimeOutputString(availabilities[0]);
    if (availabilities.length === 2) {
        return `${prefix} and ${buildTimeOutputString(availabilities[1])}`;
    }
    return `${prefix}, ${buildTimeOutputString(availabilities[1])} and ${buildTimeOutputString(availabilities[2])}`;
}

// Build a list of potential options for a given slot, to be used in responseCard generation.
function buildOptions(slot, appointmentType, date, bookingMap) {
    const dayStrings = ['Sun', 'Mon', 'Tue', 'Wed', 'Thur', 'Fri', 'Sat'];
    if (slot === 'AppointmentType') {
        return [
            { text: 'cleaning (30 min)', value: 'cleaning' },
            { text: 'root canal (60 min)', value: 'root canal' },
            { text: 'whitening (30 min)', value: 'whitening' },
        ];
    } else if (slot === 'Date') {
        // Return the next five weekdays.
        const options = [];
        const potentialDate = new Date();
        while (options.length < 5) {
            potentialDate.setDate(potentialDate.getDate() + 1);
            if (potentialDate.getDay() > 0 && potentialDate.getDay() < 6) {
                options.push({ text: `${potentialDate.getMonth() + 1}-${potentialDate.getDate()} (${dayStrings[potentialDate.getDay()]})`,
                value: potentialDate.toDateString() });
            }
        }
        return options;
    } else if (slot === 'Time') {
        // Return the availabilities on the given date.
        if (!appointmentType || !date) {
            return null;
        }
        let availabilities = bookingMap[`${date}`];
        if (!availabilities) {
            return null;
        }
        availabilities = getAvailabilitiesForDuration(getDuration(appointmentType), availabilities);
        if (availabilities.length === 0) {
            return null;
        }
        const options = [];
        for (let i = 0; i < Math.min(availabilities.length, 5); i++) {
            options.push({ text: buildTimeOutputString(availabilities[i]), value: buildTimeOutputString(availabilities[i]) });
        }
        return options;
    }
}

 // --------------- Functions that control the skill's behavior -----------------------

/**
 * Performs dialog management and fulfillment for booking a dentists appointment.
 *
 * Beyond fulfillment, the implementation for this intent demonstrates the following:
 *   1) Use of elicitSlot in slot validation and re-prompting
 *   2) Use of confirmIntent to support the confirmation of inferred slot values, when confirmation is required
 *      on the bot model and the inferred slot values fully specify the intent.
 */
function makeAppointment(intentRequest, callback) {
    const appointmentType = intentRequest.currentIntent.slots.AppointmentType;
    const date = intentRequest.currentIntent.slots.Date;
    const time = intentRequest.currentIntent.slots.Time;
    const source = intentRequest.invocationSource;
    const outputSessionAttributes = intentRequest.sessionAttributes;
    const bookingMap = JSON.parse(outputSessionAttributes.bookingMap || '{}');

    if (source === 'DialogCodeHook') {
        // Perform basic validation on the supplied input slots.
        const slots = intentRequest.currentIntent.slots;
        const validationResult = validateBookAppointment(appointmentType, date, time);
        if (!validationResult.isValid) {
            slots[`${validationResult.violatedSlot}`] = null;
            callback(elicitSlot(outputSessionAttributes, intentRequest.currentIntent.name,
            slots, validationResult.violatedSlot, validationResult.message,
            buildResponseCard(`Specify ${validationResult.violatedSlot}`, validationResult.message.content,
                buildOptions(validationResult.violatedSlot, appointmentType, date, bookingMap))));
            return;
        }

        if (!appointmentType) {
            callback(elicitSlot(outputSessionAttributes, intentRequest.currentIntent.name,
            intentRequest.currentIntent.slots, 'AppointmentType',
            { contentType: 'PlainText', content: 'What type of appointment would you like to schedule?' },
            buildResponseCard('Specify Appointment Type', 'What type of appointment would you like to schedule?',
                buildOptions('AppointmentType', appointmentType, date, null))));
            return;
        }
        if (appointmentType && !date) {
            callback(elicitSlot(outputSessionAttributes, intentRequest.currentIntent.name,
            intentRequest.currentIntent.slots, 'Date',
            { contentType: 'PlainText', content: `When would you like to schedule your ${appointmentType}?` },
            buildResponseCard('Specify Date', `When would you like to schedule your ${appointmentType}?`,
                buildOptions('Date', appointmentType, date, null))));
            return;
        }

        if (appointmentType && date) {
            // Fetch or generate the availabilities for the given date.
            let bookingAvailabilities = bookingMap[`${date}`];
            if (bookingAvailabilities == null) {
                bookingAvailabilities = getAvailabilities(date);
                bookingMap[`${date}`] = bookingAvailabilities;
                outputSessionAttributes.bookingMap = JSON.stringify(bookingMap);
            }

            const appointmentTypeAvailabilities = getAvailabilitiesForDuration(getDuration(appointmentType), bookingAvailabilities);
            if (appointmentTypeAvailabilities.length === 0) {
                //No availability on this day at all; ask for a new date and time.
                slots.Date = null;
                slots.Time = null;
                callback(elicitSlot(outputSessionAttributes, intentRequest.currentIntent.name, slots, 'Date',
                { contentType: 'PlainText', content: 'We do not have any availability on that date, is there another day which works for you?' },
                buildResponseCard('Specify Date', 'What day works best for you?',
                    buildOptions('Date', appointmentType, date, bookingMap))));
                return;
            }
            let messageContent = `What time on ${date} works for you? `;
            if (time) {
                outputSessionAttributes.formattedTime = buildTimeOutputString(time);
                // Validate that proposed time for the appointment can be booked by first fetching the availabilities for the given day.  To
                // give consistent behavior in the sample, this is stored in sessionAttributes after the first lookup.
                if (isAvailable(time, getDuration(appointmentType), bookingAvailabilities)) {
                    callback(delegate(outputSessionAttributes, slots));
                    return;
                }
                messageContent = 'The time you requested is not available. ';
            }
            if (appointmentTypeAvailabilities.length === 1) {
                // If there is only one availability on the given date, try to confirm it.
                slots.Time = appointmentTypeAvailabilities[0];
                callback(confirmIntent(outputSessionAttributes, intentRequest.currentIntent.name, slots,
                { contentType: 'PlainText', content: `${messageContent}${buildTimeOutputString(appointmentTypeAvailabilities[0])} is our only availability, does that work for you?` },
                buildResponseCard('Confirm Appointment', `Is ${buildTimeOutputString(appointmentTypeAvailabilities[0])} on ${date} okay?`,
                [{ text: 'yes', value: 'yes' }, { text: 'no', value: 'no' }])));
                return;
            }
            const availableTimeString = buildAvailableTimeString(appointmentTypeAvailabilities);
            callback(elicitSlot(outputSessionAttributes, intentRequest.currentIntent.name, slots, 'Time',
            { contentType: 'PlainText', content: `${messageContent}${availableTimeString}` },
            buildResponseCard('Specify Time', 'What time works best for you?',
                buildOptions('Time', appointmentType, date, bookingMap))));
            return;
        }

        callback(delegate(outputSessionAttributes, slots));
        return;
    }

    // Book the appointment.  In a real bot, this would likely involve a call to a backend service.
    const duration = getDuration(appointmentType);
    const bookingAvailabilities = bookingMap[`${date}`];
    if (bookingAvailabilities) {
        // Remove the availability slot for the given date as it has now been booked.
        bookingAvailabilities.splice(bookingAvailabilities.indexOf(time), 1);
        if (duration === 60) {
            const secondHalfHourTime = incrementTimeByThirtyMins(time);
            bookingAvailabilities.splice(bookingAvailabilities.indexOf(secondHalfHourTime), 1);
        }
        bookingMap[`${date}`] = bookingAvailabilities;
        outputSessionAttributes.bookingMap = JSON.stringify(bookingMap);
    } else {
        // This is not treated as an error as this code sample supports functionality either as fulfillment or dialog code hook.
        console.log(`Availabilities for ${date} were null at fulfillment time.  This should have been initialized if this function was configured as the dialog code hook`);
    }

    callback(close(outputSessionAttributes, 'Fulfilled', { contentType: 'PlainText',
       content: `Okay, I have booked your appointment.  We will see you at ${buildTimeOutputString(time)} on ${date}` }));
}

 // --------------- Intents -----------------------

/**
 * Called when the user specifies an intent for this skill.
 */
function dispatch(intentRequest, callback) {
    console.log(`dispatch userId=${intentRequest.userId}, intent=${intentRequest.currentIntent.name}`);

    const name = intentRequest.currentIntent.name;

    // Dispatch to your skill's intent handlers
    if (name === 'MakeAppointment') {
        return makeAppointment(intentRequest, callback);
    }
    throw new Error(`Intent with name ${name} not supported`);
}

// --------------- Main handler -----------------------

// Route the incoming request based on intent.
// The JSON body of the request is provided in the event slot.
exports.handler = (event, context, callback) => {
    try {
        console.log(`event.bot.name=${event.bot.name}`);

        /**
         * Uncomment this if statement and populate with your Lex bot name and / or version as
         * a sanity check to prevent invoking this Lambda function from an undesired Lex bot or
         * bot version.
         */
        /*
        if (event.bot.name !== 'MakeAppointment') {
             callback('Invalid Bot Name');
        }
        */
        dispatch(event, (response) => callback(null, response));
    } catch (err) {
        callback(err);
    }
};
