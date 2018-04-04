function handler (event, context, callback) {
  // TODO: Process logs...
  
  console.log(event)
  
  callback(null, {})
}

module.exports.handler = handler