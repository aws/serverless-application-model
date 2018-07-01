'use strict'

exports.handler = async (event) => {
  console.log('LOG: Name is ' + event.name)
  return await `Hello ${event.name}`
}
