'use strict';

 /**
  * This sample demonstrates an implementation of the Lex Code Hook Interface
  * in order to serve a sample bot which manages reservations for hotel rooms and car rentals.
  * Bot, Intent, and Slot models which are compatible with this sample can be found in the Lex Console
  * as part of the 'BookTrip' template.
  *
  * For instructions on how to set up and test this bot, as well as additional samples,
  *  visit the Lex Getting Started documentation.
  */

 // --------------- Helpers that build all of the responses -----------------------

function elicitSlot(sessionAttributes, intentName, slots, slotToElicit, message) {
    return {
        sessionAttributes,
        dialogAction: {
            type: 'ElicitSlot',
            intentName,
            slots,
            slotToElicit,
            message,
        },
    };
}

function confirmIntent(sessionAttributes, intentName, slots, message) {
    return {
        sessionAttributes,
        dialogAction: {
            type: 'ConfirmIntent',
            intentName,
            slots,
            message,
        },
    };
}

function close(sessionAttributes, fulfillmentState, message) {
    return {
        sessionAttributes,
        dialogAction: {
            type: 'Close',
            fulfillmentState,
            message,
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

// ---------------- Helper Functions --------------------------------------------------

// Generates a number within a reasonable range that might be expected for a flight.
// The price is fixed for a given pair of locations.
function generateCarPrice(location, days, age, carType) {
    const carTypes = ['economy', 'standard', 'midsize', 'full size', 'minivan', 'luxury'];
    let baseLocationCost = 0;
    for (let i = 0; i < location.length; i++) {
        baseLocationCost += location.toLowerCase().charCodeAt(i) - 97;
    }
    const ageMultiplier = (age < 25) ? 1.10 : 1;
    return days * ((100 + baseLocationCost) + ((carTypes.indexOf(carType) * 50) * ageMultiplier));
}

// Generates a number within a reasonable range that might be expected for a hotel.
// The price is fixed for a pair of location and roomType.
function generateHotelPrice(location, nights, roomType) {
    const roomTypes = ['queen', 'king', 'deluxe'];
    let costOfLiving = 0;
    for (let i = 0; i < location.length; i++) {
        costOfLiving += location.toLowerCase().charCodeAt(i) - 97;
    }
    return nights * (100 + costOfLiving + (100 + roomTypes.indexOf(roomType.toLowerCase())));
}

function isValidCarType(carType) {
    const carTypes = ['economy', 'standard', 'midsize', 'full size', 'minivan', 'luxury'];
    return (carTypes.indexOf(carType.toLowerCase()) > -1);
}

function isValidCity(city) {
    const validCities = ['new york', 'los angeles', 'chicago', 'houston', 'philadelphia', 'phoenix', 'san antonio', 'san diego', 'dallas', 'san jose',
    'austin', 'jacksonville', 'san francisco', 'indianapolis', 'columbus', 'fort worth', 'charlotte', 'detroit', 'el paso', 'seattle', 'denver', 'washington dc',
    'memphis', 'boston', 'nashville', 'baltimore', 'portland'];
    return (validCities.indexOf(city.toLowerCase()) > -1);
}

function isValidRoomType(roomType) {
    const roomTypes = ['queen', 'king', 'deluxe'];
    return (roomTypes.indexOf(roomType.toLowerCase()) > -1);
}

function isValidDate(date) {
    return !(isNaN(Date.parse(date)));
}

function getDayDifference(earlierDate, laterDate) {
    const laterDateInDaysSinceEpoch = new Date(laterDate).getTime() / 86400000;
    const earlierDateInDaysSinceEpoch = new Date(earlierDate).getTime() / 86400000;
    return Number(laterDateInDaysSinceEpoch - earlierDateInDaysSinceEpoch).toFixed(0);
}

function addDays(date, numberOfDays) {
    const newDate = new Date(date);
    newDate.setTime(newDate.getTime() + (86400000 * numberOfDays));
    return `${newDate.getFullYear()}-${newDate.getMonth() + 1}-${newDate.getDate()}`;
}

function buildValidationResult(isValid, violatedSlot, messageContent) {
    return {
        isValid,
        violatedSlot,
        message: { contentType: 'PlainText', content: messageContent },
    };
}

function validateBookCar(slots) {
    const pickUpCity = slots.PickUpCity;
    const pickUpDate = slots.PickUpDate;
    const returnDate = slots.ReturnDate;
    const driverAge = slots.DriverAge;
    const carType = slots.CarType;

    if (pickUpCity && !isValidCity(pickUpCity)) {
        return buildValidationResult(false, 'PickUpCity', `We currently do not support ${pickUpCity} as a valid destination.  Can you try a different city?`);
    }

    if (pickUpDate) {
        if (!isValidDate(pickUpDate)) {
            return buildValidationResult(false, 'PickUpDate', 'I did not understand your departure date.  When would you like to pick up your car rental?');
        }
        if (new Date(pickUpDate) < new Date()) {
            return buildValidationResult(false, 'PickUpDate', 'Your pick up date is in the past!  Can you try a different date?');
        }
    }

    if (returnDate) {
        if (!isValidDate(returnDate)) {
            return buildValidationResult(false, 'ReturnDate', 'I did not understand your return date.  When would you like to return your car rental?');
        }
    }

    if (pickUpDate && returnDate) {
        if (new Date(pickUpDate) >= new Date(returnDate)) {
            return buildValidationResult(false, 'ReturnDate', 'Your return date must be after your pick up date.  Can you try a different return date?');
        }
        if (getDayDifference(pickUpDate, returnDate) > 30) {
            return buildValidationResult(false, 'ReturnDate', 'You can reserve a car for up to thirty days.  Can you try a different return date?');
        }
    }

    if (driverAge != null && driverAge < 18) {
        return buildValidationResult(false, 'DriverAge', 'Your driver must be at least eighteen to rent a car.  Can you provide the age of a different driver?');
    }

    if (carType && !isValidCarType(carType)) {
        return buildValidationResult(false, 'CarType', 'I did not recognize that model.  What type of car would you like to rent?  Popular cars are economy, midsize, or luxury');
    }

    return { isValid: true };
}

function validateHotel(slots) {
    const location = slots.Location;
    const checkInDate = slots.CheckInDate;
    const nights = slots.Nights;
    const roomType = slots.RoomType;

    if (location && !isValidCity(location)) {
        return buildValidationResult(false, 'Location', `We currently do not support ${location} as a valid destination.  Can you try a different city?`);
    }

    if (checkInDate) {
        if (!isValidDate(checkInDate)) {
            return buildValidationResult(false, 'CheckInDate', 'I did not understand your check in date.  When would you like to check in?');
        }
        if (new Date(checkInDate) < new Date()) {
            return buildValidationResult(false, 'CheckInDate', 'Your check in date is in the past!  Can you try a different date?');
        }
    }

    if (nights != null && (nights < 1 || nights > 30)) {
        return buildValidationResult(false, 'Nights', 'You can make a reservations for from one to thirty nights.  How many nights would you like to stay for?');
    }

    if (roomType && !isValidRoomType(roomType)) {
        return buildValidationResult(false, 'RoomType', 'I did not recognize that room type.  Would you like to stay in a queen, king, or deluxe room?');
    }

    return { isValid: true };
}

/**
 * Performs dialog management and fulfillment for booking a hotel.
 *
 * Beyond fulfillment, the implementation for this intent demonstrates the following:
 *   1) Use of elicitSlot in slot validation and re-prompting
 *   2) Use of sessionAttributes to pass information that can be used to guide conversation
 */
function bookHotel(intentRequest, callback) {
    const location = intentRequest.currentIntent.slots.Location;
    const checkInDate = intentRequest.currentIntent.slots.CheckInDate;
    const nights = intentRequest.currentIntent.slots.Nights;
    const roomType = intentRequest.currentIntent.slots.RoomType;
    const sessionAttributes = intentRequest.sessionAttributes;

    // Load confirmation history and track the current reservation.
    const reservation = String(JSON.stringify({ ReservationType: 'Hotel', Location: location, RoomType: roomType, CheckInDate: checkInDate, Nights: nights }));
    sessionAttributes.currentReservation = reservation;

    if (intentRequest.invocationSource === 'DialogCodeHook') {
        // Validate any slots which have been specified.  If any are invalid, re-elicit for their value
        const validationResult = validateHotel(intentRequest.currentIntent.slots);
        if (!validationResult.isValid) {
            const slots = intentRequest.currentIntent.slots;
            slots[`${validationResult.violatedSlot}`] = null;
            callback(elicitSlot(sessionAttributes, intentRequest.currentIntent.name,
            slots, validationResult.violatedSlot, validationResult.message));
            return;
        }

        // Otherwise, let native DM rules determine how to elicit for slots and prompt for confirmation.  Pass price back in sessionAttributes once it can be calculated; otherwise clear any setting from sessionAttributes.
        if (location && checkInDate && nights != null && roomType) {
            // The price of the hotel has yet to be confirmed.
            const price = generateHotelPrice(location, nights, roomType);
            sessionAttributes.currentReservationPrice = price;
        } else {
            delete sessionAttributes.currentReservationPrice;
        }
        sessionAttributes.currentReservation = reservation;
        callback(delegate(sessionAttributes, intentRequest.currentIntent.slots));
        return;
    }

    // Booking the hotel.  In a real application, this would likely involve a call to a backend service.
    console.log(`bookHotel under=${reservation}`);

    delete sessionAttributes.currentReservationPrice;
    delete sessionAttributes.currentReservation;
    sessionAttributes.lastConfirmedReservation = reservation;

    callback(close(sessionAttributes, 'Fulfilled',
    { contentType: 'PlainText', content: 'Thanks, I have placed your reservation.   Please let me know if you would like to book a car rental, or another hotel.' }));
}

/**
 * Performs dialog management and fulfillment for booking a hotel.
 *
 * Beyond fulfillment, the implementation for this intent demonstrates the following:
 *   1) Use of elicitSlot in slot validation and re-prompting
 *   2) Use of confirmIntent to support the confirmation of inferred slot values
 */
function bookCar(intentRequest, callback) {
    const slots = intentRequest.currentIntent.slots;
    const pickUpCity = slots.PickUpCity;
    const pickUpDate = slots.PickUpDate;
    const returnDate = slots.ReturnDate;
    const driverAge = slots.DriverAge;
    const carType = slots.CarType;
    const confirmationStatus = intentRequest.currentIntent.confirmationStatus;
    const sessionAttributes = intentRequest.sessionAttributes;
    const lastConfirmedReservation = sessionAttributes.lastConfirmedReservation ? JSON.parse(sessionAttributes.lastConfirmedReservation) : null;
    const confirmationContext = sessionAttributes.confirmationContext;

    // Load confirmation history and track the current reservation.
    const reservation = String(JSON.stringify({ ReservationType: 'Car', PickUpCity: pickUpCity, PickUpDate: pickUpDate, ReturnDate: returnDate, CarType: carType }));
    sessionAttributes.currentReservation = reservation;

    if (pickUpCity && pickUpDate && returnDate && driverAge != null && carType) {
        // Generate the price of the car in case it is necessary for future steps.
        const price = generateCarPrice(pickUpCity, getDayDifference(pickUpDate, returnDate), driverAge, carType);
        sessionAttributes.currentReservationPrice = price;
    }

    if (intentRequest.invocationSource === 'DialogCodeHook') {
        // Validate any slots which have been specified.  If any are invalid, re-elicit for their value
        const validationResult = validateBookCar(intentRequest.currentIntent.slots);
        if (!validationResult.isValid) {
            slots[`${validationResult.violatedSlot}`] = null;
            callback(elicitSlot(sessionAttributes, intentRequest.currentIntent.name,
            slots, validationResult.violatedSlot, validationResult.message));
            return;
        }

        // Determine if the intent (and current slot settings) has been denied.  The messaging will be different if the user is denying a reservation he initiated or an auto-populated suggestion.
        if (confirmationStatus === 'Denied') {
            // Clear out auto-population flag for subsequent turns.
            delete sessionAttributes.confirmationContext;
            delete sessionAttributes.currentReservation;
            if (confirmationContext === 'AutoPopulate') {
                callback(elicitSlot(sessionAttributes, intentRequest.currentIntent.name, { PickUpCity: null, PickUpDate: null, ReturnDate: null, DriverAge: null, CarType: null }, 'PickUpCity',
                { contentType: 'PlainText', content: 'Where would you like to make your car reservation?' }));
                return;
            }
            callback(delegate(sessionAttributes, intentRequest.currentIntent.slots));
            return;
        }

        if (confirmationStatus === 'None') {
            // If we are currently auto-populating but have not gotten confirmation, keep requesting for confirmation.
            if ((!pickUpCity && !pickUpDate && !returnDate && driverAge == null && !carType) || confirmationContext === 'AutoPopulate') {
                if (lastConfirmedReservation && lastConfirmedReservation.ReservationType === 'Hotel') {
                    //If the user's previous reservation was a hotel - prompt for a rental with auto-populated values to match this reservation.
                    sessionAttributes.confirmationContext = 'AutoPopulate';
                    callback(confirmIntent(sessionAttributes, intentRequest.currentIntent.name,
                        {
                            PickUpCity: lastConfirmedReservation.Location,
                            PickUpDate: lastConfirmedReservation.CheckInDate,
                            ReturnDate: `${addDays(lastConfirmedReservation.CheckInDate, lastConfirmedReservation.Nights)}`,
                            CarType: null,
                            DriverAge: null,
                        },
                        { contentType: 'PlainText', content: `Is this car rental for your ${lastConfirmedReservation.Nights} night stay in ${lastConfirmedReservation.Location} on ${lastConfirmedReservation.CheckInDate}?` }));
                    return;
                }
            }
            // Otherwise, let native DM rules determine how to elicit for slots and/or drive confirmation.
            callback(delegate(sessionAttributes, intentRequest.currentIntent.slots));
            return;
        }

        // If confirmation has occurred, continue filling any unfilled slot values or pass to fulfillment.
        if (confirmationStatus === 'Confirmed') {
            // Remove confirmationContext from sessionAttributes so it does not confuse future requests
            delete sessionAttributes.confirmationContext;
            if (confirmationContext === 'AutoPopulate') {
                if (!driverAge) {
                    callback(elicitSlot(sessionAttributes, intentRequest.currentIntent.name, intentRequest.currentIntent.slots, 'DriverAge',
                    { contentType: 'PlainText', content: 'How old is the driver of this car rental?' }));
                    return;
                } else if (!carType) {
                    callback(elicitSlot(sessionAttributes, intentRequest.currentIntent.name, intentRequest.currentIntent.slots, 'CarType',
                    { contentType: 'PlainText', content: 'What type of car would you like? Popular models are economy, midsize, and luxury.' }));
                    return;
                }
            }
            callback(delegate(sessionAttributes, intentRequest.currentIntent.slots));
            return;
        }
    }

    // Booking the car.  In a real application, this would likely involve a call to a backend service.
    console.log(`bookCar at=${reservation}`);
    delete sessionAttributes.currentReservationPrice;
    delete sessionAttributes.currentReservation;
    sessionAttributes.lastConfirmedReservation = reservation;
    callback(close(sessionAttributes, 'Fulfilled',
    { contentType: 'PlainText', content: 'Thanks, I have placed your reservation.' }));
}

 // --------------- Intents -----------------------

/**
 * Called when the user specifies an intent for this skill.
 */
function dispatch(intentRequest, callback) {
    console.log(`dispatch userId=${intentRequest.userId}, intentName=${intentRequest.currentIntent.name}`);

    const intentName = intentRequest.currentIntent.name;

    // Dispatch to your skill's intent handlers
    if (intentName === 'BookHotel') {
        return bookHotel(intentRequest, callback);
    } else if (intentName === 'BookCar') {
        return bookCar(intentRequest, callback);
    }
    throw new Error(`Intent with name ${intentName} not supported`);
}

// --------------- Main handler -----------------------

// Route the incoming request based on intent.
// The JSON body of the request is provided in the event slot.
exports.handler = (event, context, callback) => {
    try {
        console.log(`event.bot.name=${event.bot.name}`);

        /**
         * Uncomment this if statement and populate with your Lex bot name, alias and / or version as
         * a sanity check to prevent invoking this Lambda function from an undesired source.
         */
        /*
        if (event.bot.name != 'BookTrip') {
             callback('Invalid Bot Name');
        }
        */
        dispatch(event, (response) => callback(null, response));
    } catch (err) {
        callback(err);
    }
};
