'use strict';
console.log('Loading function');

exports.handler = (event, context, callback) => {
    //console.log('Received event:', JSON.stringify(event, null, 2));
    const message = JSON.parse(event.Records[0].Sns.Message);
    
    switch(message.notificationType) {
        case 'Bounce':
            handleBounce(message);
            break;
        case 'Complaint':
            handleComplaint(message);
            break;
        case 'Delivery':
            handleDelivery(message);
            break;
        default:
            callback(`Unknown notification type: ${message.notificationType}`);
    }
};

function handleBounce(message) {
    const messageId = message.mail.messageId;
    const addresses = message.bounce.bouncedRecipients.map((recipient) => recipient.emailAddress);
    const bounceType = message.bounce.bounceType;
    
    console.log(`Message ${messageId} bounced when sending to ${addresses.join(', ')}. Bounce type: ${bounceType}`);
}

function handleComplaint(message) {
    const messageId = message.mail.messageId;
    const addresses = message.complaint.complainedRecipients.map((recipient) => recipient.emailAddress);
  
    console.log(`A complaint was reported by ${addresses.join(', ')} for message ${messageId}.`);
}

function handleDelivery(message) {
    const messageId = message.mail.messageId;
    const deliveryTimestamp = message.delivery.timestamp;
    
    console.log(`Message ${messageId} was delivered successfully at ${deliveryTimestamp}.`);
}
