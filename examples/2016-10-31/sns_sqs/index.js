async function handler (event, context) {
  const records = event.Records
  console.log(records)
  return {}
}

module.exports.handler = handler