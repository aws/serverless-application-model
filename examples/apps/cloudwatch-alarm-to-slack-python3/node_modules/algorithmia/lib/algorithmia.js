var Algorithm, AlgorithmiaClient, Data, algorithmia, defaultApiAddress, exports, http, https, packageJson, url;

https = require('https');

http = require('http');

url = require('url');

packageJson = require('../package.json');

Algorithm = require('./algorithm.js');

Data = require('./data.js');

defaultApiAddress = 'https://api.algorithmia.com';

AlgorithmiaClient = (function() {
  function AlgorithmiaClient(key, address) {
    this.apiAddress = address || process.env.ALGORITHMIA_API || defaultApiAddress;
    key = key || process.env.ALGORITHMIA_API_KEY;
    if (key) {
      if (key.indexOf('Simple ') === 0) {
        this.apiKey = key;
      } else {
        this.apiKey = 'Simple ' + key;
      }
    } else {
      this.apiKey = '';
    }
  }

  AlgorithmiaClient.prototype.algo = function(path) {
    return new Algorithm(this, path);
  };

  AlgorithmiaClient.prototype.file = function(path) {
    return new Data.File(this, path);
  };

  AlgorithmiaClient.prototype.dir = function(path) {
    return new Data.Dir(this, path);
  };

  AlgorithmiaClient.prototype.req = function(path, method, data, cheaders, callback) {
    var dheader, httpRequest, key, options, protocol, val;
    dheader = {
      'User-Agent': 'algorithmia-nodejs/' + packageJson.version + ' (NodeJS ' + process.version + ')'
    };
    if (this.apiKey) {
      dheader['Authorization'] = this.apiKey;
    }
    for (key in cheaders) {
      val = cheaders[key];
      dheader[key] = val;
    }
    options = url.parse(this.apiAddress + path);
    options.method = method;
    options.headers = dheader;
    protocol = options.protocol === 'https:' ? https : http;
    httpRequest = protocol.request(options, function(res) {
      var accept, chunks;
      accept = dheader['Accept'];
      if (accept === 'application/json' || accept === 'text/plain') {
        res.setEncoding('utf8');
      }
      chunks = [];
      res.on('data', function(chunk) {
        return chunks.push(chunk);
      });
      res.on('end', function() {
        var body, buff, ct;
        ct = res.headers['content-type'] || accept;
        if (ct.startsWith('application/json')) {
          buff = chunks.join('');
          body = buff === '' ? {} : JSON.parse(buff);
        } else if (ct.startsWith('text/plain')) {
          body = chunks.join('');
        } else {
          body = Buffer.concat(chunks);
        }
        if (callback) {
          if (res.statusCode < 200 || res.statusCode >= 300) {
            if (!body) {
              body = {};
            }
            if (!body.error) {
              if (res.headers['x-error-message']) {
                body.error = {
                  message: res.headers['x-error-message']
                };
              } else {
                body.error = {
                  message: 'HTTP Response: ' + res.statusCode
                };
              }
            }
          }
          callback(body, res.statusCode);
        }
      });
      return res;
    });
    httpRequest.on('error', function(err) {
      var body;
      body = {
        error: {
          message: err.message
        }
      };
      if (callback) {
        callback(body, 500);
      }
    });
    if (options.method !== 'HEAD') {
      httpRequest.write(data);
    }
    httpRequest.end();
  };

  return AlgorithmiaClient;

})();

algorithmia = function(key, address) {
  return new AlgorithmiaClient(key, address);
};

algorithmia.client = function(key, address) {
  return new AlgorithmiaClient(key, address);
};

algorithmia.algo = function(path) {
  this.defaultClient = this.defaultClient || new AlgorithmiaClient();
  return this.defaultClient.algo(path);
};

algorithmia.file = function(path) {
  this.defaultClient = this.defaultClient || new AlgorithmiaClient();
  return this.defaultClient.file(path);
};

module.exports = exports = algorithmia;
