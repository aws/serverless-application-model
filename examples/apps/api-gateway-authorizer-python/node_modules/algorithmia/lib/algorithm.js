var AlgoResponse, Algorithm, exports;

Algorithm = (function() {
  function Algorithm(client, path) {
    this.client = client;
    this.algo_path = path;
    this.promise = {
      then: (function(_this) {
        return function(callback) {
          return _this.callback = callback;
        };
      })(this)
    };
  }

  Algorithm.prototype.pipe = function(input) {
    var contentType, data;
    data = input;
    if (Buffer.isBuffer(input)) {
      contentType = 'application/octet-stream';
    } else if (typeof input === 'string') {
      contentType = 'text/plain';
    } else {
      contentType = 'application/json';
      data = JSON.stringify(input);
    }
    this.req = this.client.req('/v1/algo/' + this.algo_path, 'POST', data, {
      'Content-Type': contentType
    }, (function(_this) {
      return function(response, status) {
        return typeof _this.callback === "function" ? _this.callback(new AlgoResponse(response, status)) : void 0;
      };
    })(this));
    return this.promise;
  };

  Algorithm.prototype.pipeJson = function(input) {
    if (typeof input !== 'string') {
      throw "Cannot convert " + (typeof input) + " to string";
    }
    this.req = this.client.req('/v1/algo/' + this.algo_path, 'POST', input, {
      'Content-Type': 'application/json'
    }, (function(_this) {
      return function(response, status) {
        return _this.callback(new AlgoResponse(response, status));
      };
    })(this));
    return this.promise;
  };

  return Algorithm;

})();

AlgoResponse = (function() {
  function AlgoResponse(response, status) {
    this.status = status;
    this.result = response.result;
    this.error = response.error;
    this.metadata = response.metadata;
  }

  AlgoResponse.prototype.get = function() {
    if (this.error) {
      throw "" + this.error.message;
    }
    switch (this.metadata.content_type) {
      case "void":
        return null;
      case "text":
      case "json":
        return this.result;
      case "binary":
        return new Buffer(this.result, 'base64');
      default:
        throw "Unknown result content_type: " + this.metadata.content_type + ".";
    }
  };

  return AlgoResponse;

})();

module.exports = exports = Algorithm;
