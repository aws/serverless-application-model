async function handler (event, context) {
  // TODO: Handle message...
  const records = event.Records
  
  console.log(records)
  
  return {}
}

module.exports.handler = handler