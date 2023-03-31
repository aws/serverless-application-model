import { util } from '@aws-appsync/utils';

export function request(ctx) {
  const id = util.autoId();
  const author = ctx.args.author
  const time = "1234567890"
  return dynamodbPutRequest({ key: {id}, values: {"author": author, "time": time}});
}

export function response(ctx) {
  return ctx.result;
}

/**
* Helper function to create a new item
* @returns a PutItem request
*/
function dynamodbPutRequest({key, values}) {
  return {
    operation: 'PutItem',
    key: util.dynamodb.toMapValues(key),
    attributeValues: util.dynamodb.toMapValues(values),
  };
}
