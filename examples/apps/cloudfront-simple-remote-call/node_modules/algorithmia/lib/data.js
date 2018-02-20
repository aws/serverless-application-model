var Data, Dir, DirListing, File, exports, fs, path,
  extend = function(child, parent) { for (var key in parent) { if (hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; },
  hasProp = {}.hasOwnProperty;

path = require('path');

fs = require('fs');

Data = (function() {
  function Data(client, path) {
    this.client = client;
    this.data_path = path.replace(/data\:\/\//, '');
  }

  Data.prototype.basename = function() {
    return this.data_path.slice(this.data_path.lastIndexOf('/') + 1);
  };

  Data.prototype.parent = function() {
    var offset;
    offset = this.data_path.lastIndexOf('/');
    if (offset >= 0) {
      return new Dir(this.client, 'data://' + this.data_path.slice(0, offset));
    } else {
      return null;
    }
  };

  return Data;

})();

File = (function(superClass) {
  extend(File, superClass);

  function File() {
    return File.__super__.constructor.apply(this, arguments);
  }

  File.prototype.put = function(content, callback) {
    var headers;
    headers = {};
    return this.client.req('/v1/data/' + this.data_path, 'PUT', content, headers, callback);
  };

  File.prototype.get = function(callback) {
    var headers, innerCb;
    headers = {
      'Accept': 'application/octet-stream'
    };
    innerCb = function(response, status) {
      var data, err;
      err = (typeof response === 'object' && (response != null ? response.error : void 0)) ? response.error : null;
      data = err === null ? response : null;
      return callback(err, data);
    };
    return this.client.req('/v1/data/' + this.data_path, 'GET', '', headers, innerCb);
  };

  File.prototype.putString = function(content, callback) {
    var headers;
    headers = {
      'Content-Type': 'text/plain'
    };
    return this.client.req('/v1/data/' + this.data_path, 'PUT', content, headers, callback);
  };

  File.prototype.putJson = function(content, callback) {
    var headers;
    headers = {
      'Content-Type': 'application/json'
    };
    return this.client.req('/v1/data/' + this.data_path, 'PUT', content, headers, callback);
  };

  File.prototype.getString = function(callback) {
    var headers;
    headers = {
      'Accept': 'text/plain'
    };
    return this.client.req('/v1/data/' + this.data_path, 'GET', '', headers, callback);
  };

  File.prototype.getJson = function(callback) {
    var headers;
    headers = {
      'Accept': 'application/json'
    };
    return this.client.req('/v1/data/' + this.data_path, 'GET', '', headers, callback);
  };

  File.prototype.exists = function(callback) {
    var headers;
    headers = {
      'Accept': 'text/plain'
    };
    return this.client.req('/v1/data/' + this.data_path, 'HEAD', '', headers, function(response, status) {
      if (status === 200) {
        return callback(true);
      } else {
        return callback(false, status, response);
      }
    });
  };

  File.prototype["delete"] = function(callback) {
    var headers;
    headers = {
      'Content-Type': 'text/plain'
    };
    return this.client.req('/v1/data/' + this.data_path, 'DELETE', '', headers, callback);
  };

  return File;

})(Data);

Dir = (function(superClass) {
  extend(Dir, superClass);

  function Dir() {
    return Dir.__super__.constructor.apply(this, arguments);
  }

  Dir.prototype.create = function(callback) {
    var content, headers;
    content = {
      name: this.basename()
    };
    headers = {
      'Content-Type': 'application/json'
    };
    return this.client.req('/v1/data/' + this.parent().data_path, 'POST', JSON.stringify(content), headers, callback);
  };

  Dir.prototype.file = function(filename) {
    return new File(this.client, 'data://' + this.data_path + '/' + filename);
  };

  Dir.prototype.putFile = function(filePath, callback) {
    var filename;
    filename = path.basename(filePath);
    return fs.readFile(filePath, (function(_this) {
      return function(err, data) {
        return _this.file(filename).put(data, callback);
      };
    })(this));
  };

  Dir.prototype.iterator = function() {
    var listing;
    listing = new DirListing(this.client, this.data_path);
    return listing.iterator();
  };

  Dir.prototype.forEach = function(callback) {
    var listing;
    listing = new DirListing(this.client, this.data_path);
    return listing.forEach(callback);
  };

  Dir.prototype.forEachFile = function(callback) {
    var listing;
    listing = new DirListing(this.client, this.data_path);
    return listing.forEach(function(err, item) {
      if (item instanceof File) {
        return callback(err, item);
      }
    });
  };

  Dir.prototype.forEachDir = function(callback) {
    var listing;
    listing = new DirListing(this.client, this.data_path);
    return listing.forEach(function(err, item) {
      if (item instanceof Dir) {
        return callback(err, item);
      }
    });
  };

  Dir.prototype.exists = function(callback) {
    var headers;
    headers = {};
    return this.client.req('/v1/data/' + this.data_path, 'GET', '', headers, function(response, status) {
      if (status === 200) {
        return callback(true);
      } else {
        return callback(false, status, response);
      }
    });
  };

  Dir.prototype["delete"] = function(force, callback) {
    var headers, query;
    query = force ? '?force=true' : '';
    headers = {
      'Content-Type': 'text/plain'
    };
    return this.client.req('/v1/data/' + this.data_path + query, 'DELETE', '', headers, callback);
  };

  return Dir;

})(Data);

DirListing = (function() {
  function DirListing(client, path) {
    this.client = client;
    this.data_path = path;
    this.offset = 0;
    this.error = null;
    this.page = null;
  }

  DirListing.prototype.loadNextPage = function(cb) {
    var headers, query;
    headers = {};
    query = this.page === null ? '' : "?marker=" + (encodeURIComponent(this.page.marker));
    return this.client.req('/v1/data/' + this.data_path + query, 'GET', '', headers, (function(_this) {
      return function(response, status) {
        _this.offset = 0;
        if (status === 200) {
          _this.page = response;
          _this.error = null;
        } else {
          _this.page = null;
          _this.error = response.error;
        }
        if (cb) {
          return cb();
        }
      };
    })(this));
  };

  DirListing.prototype.forEach = function(cb) {
    var iter, recurse, thenCb;
    thenCb = null;
    iter = this.iterator();
    recurse = function(err, value) {
      if (value === void 0) {
        if (thenCb) {
          return thenCb();
        }
      } else {
        cb(err, value);
        return iter.next(recurse);
      }
    };
    iter.next(recurse);
    return {
      then: (function(_this) {
        return function(cb) {
          return thenCb = cb;
        };
      })(this)
    };
  };

  DirListing.prototype.iterator = function() {
    return {
      next: (function(_this) {
        return function(cb) {
          var dir, dirCount, file, fileCount, nextResult, ref, ref1;
          if (_this.error) {
            cb(_this.error, void 0);
          } else if (_this.page === null) {
            _this.loadNextPage(function() {
              return _this.iterator().next(cb);
            });
          } else {
            dirCount = ((ref = _this.page.folders) != null ? ref.length : void 0) || 0;
            fileCount = ((ref1 = _this.page.files) != null ? ref1.length : void 0) || 0;
            if (_this.offset < dirCount) {
              dir = _this.page.folders[_this.offset];
              _this.offset++;
              cb(null, new Dir(_this.client, 'data://' + _this.data_path + '/' + dir.name));
            } else if (_this.offset < dirCount + fileCount) {
              file = _this.page.files[_this.offset];
              _this.offset++;
              nextResult = new File(_this.client, 'data://' + _this.data_path + '/' + file.filename);
              nextResult.last_modified = file.last_modified;
              nextResult.size = file.size;
              cb(null, nextResult);
            } else if (_this.page.marker) {
              _this.loadNextPage(function() {
                return _this.iterator().next(cb);
              });
            } else {
              cb(null, void 0);
            }
          }
        };
      })(this)
    };
  };

  return DirListing;

})();

module.exports = exports = {
  File: File,
  Dir: Dir
};
