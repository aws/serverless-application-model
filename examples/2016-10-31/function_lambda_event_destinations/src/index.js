exports.handler = function(event, context, callback) {
  var event_received_at = new Date().toISOString();
  console.log('Event received at: ' + event_received_at);
  console.log('Received event:', JSON.stringify(event, null, 2));

  if (event.Success) {
      console.log("Success");
      context.callbackWaitsForEmptyEventLoop = false;
      callback(null);
  } else {
      console.log("Failure");
      context.callbackWaitsForEmptyEventLoop = false;
      callback(new Error("Failure from event, Success = false, I am failing!"), 'Destination Function Error Thrown');
  }
};      
