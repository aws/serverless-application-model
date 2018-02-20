'use strict';

Object.defineProperty(exports, "__esModule", {
  value: true
});

var _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; };

var _utils = require('./utils');

var utils = _interopRequireWildcard(_utils);

var _logger = require('./logger');

var _logger2 = _interopRequireDefault(_logger);

var _EventEmitter2 = require('./EventEmitter');

var _EventEmitter3 = _interopRequireDefault(_EventEmitter2);

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function _interopRequireWildcard(obj) { if (obj && obj.__esModule) { return obj; } else { var newObj = {}; if (obj != null) { for (var key in obj) { if (Object.prototype.hasOwnProperty.call(obj, key)) newObj[key] = obj[key]; } } newObj.default = obj; return newObj; } }

function _defaults(obj, defaults) { var keys = Object.getOwnPropertyNames(defaults); for (var i = 0; i < keys.length; i++) { var key = keys[i]; var value = Object.getOwnPropertyDescriptor(defaults, key); if (value && value.configurable && obj[key] === undefined) { Object.defineProperty(obj, key, value); } } return obj; }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return call && (typeof call === "object" || typeof call === "function") ? call : self; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function, not " + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : _defaults(subClass, superClass); }

var Connector = function (_EventEmitter) {
  _inherits(Connector, _EventEmitter);

  function Connector(cache, store, services) {
    var options = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : {};

    _classCallCheck(this, Connector);

    var _this = _possibleConstructorReturn(this, _EventEmitter.call(this));

    _this.cache = cache;
    _this.store = store;
    _this.services = services;
    _this.options = options;
    _this.logger = _logger2.default.create('cacheConnector');

    _this.cache && _this.cache.init && _this.cache.init(services, options.cache, options);
    return _this;
  }

  Connector.prototype.load = function load(languages, namespaces, callback) {
    var _this2 = this;

    if (!this.cache) return callback && callback();
    var options = _extends({}, this.cache.options, this.options.cache);

    if (typeof languages === 'string') languages = this.services.languageUtils.toResolveHierarchy(languages);
    if (typeof namespaces === 'string') namespaces = [namespaces];

    if (options.enabled) {
      this.cache.load(languages, function (err, data) {
        if (err) _this2.logger.error('loading languages ' + languages.join(', ') + ' from cache failed', err);
        if (data) {
          for (var l in data) {
            for (var n in data[l]) {
              if (n === 'i18nStamp') continue;
              var bundle = data[l][n];
              if (bundle) _this2.store.addResourceBundle(l, n, bundle);
            }
          }
        }
        if (callback) callback();
      });
    } else {
      if (callback) callback();
    }
  };

  Connector.prototype.save = function save() {
    if (this.cache && this.options.cache && this.options.cache.enabled) this.cache.save(this.store.data);
  };

  return Connector;
}(_EventEmitter3.default);

exports.default = Connector;