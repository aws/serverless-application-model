'use strict';
exports.handler = function(event, context, callback) {
    let fs = require("fs");
    let path = require("path");

    var image = fs.readFileSync(path.resolve("./AWS_logo_RGB.png"));
    callback(null, {
      statusCode: '200',
      body: Buffer.from(image).toString('base64'),
      isBase64Encoded: true,
      headers: {
        "Content-Type": "image/png"
      }
    });
  };