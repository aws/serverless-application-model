exports.handler = async event => {
  return {
    statusCode: 200,
    headers: {
      'Access-Control-Allow-Origin': 'http://localhost:8080'
    },
    body: JSON.stringify({
      message: 'hello world'
    })
  };
};
