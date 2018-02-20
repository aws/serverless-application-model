'use strict';

Object.defineProperty(exports, "__esModule", {
  value: true
});

var _extends = Object.assign || function (target) { for (var i = 1; i < arguments.length; i++) { var source = arguments[i]; for (var key in source) { if (Object.prototype.hasOwnProperty.call(source, key)) { target[key] = source[key]; } } } return target; };

var _EventEmitter2 = require('./EventEmitter');

var _EventEmitter3 = _interopRequireDefault(_EventEmitter2);

var _utils = require('./utils');

var utils = _interopRequireWildcard(_utils);

function _interopRequireWildcard(obj) { if (obj && obj.__esModule) { return obj; } else { var newObj = {}; if (obj != null) { for (var key in obj) { if (Object.prototype.hasOwnProperty.call(obj, key)) newObj[key] = obj[key]; } } newObj.default = obj; return newObj; } }

function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { default: obj }; }

function _defaults(obj, defaults) { var keys = Object.getOwnPropertyNames(defaults); for (var i = 0; i < keys.length; i++) { var key = keys[i]; var value = Object.getOwnPropertyDescriptor(defaults, key); if (value && value.configurable && obj[key] === undefined) { Object.defineProperty(obj, key, value); } } return obj; }

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return call && (typeof call === "object" || typeof call === "function") ? call : self; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function, not " + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : _defaults(subClass, superClass); }

var ResourceStore = function (_EventEmitter) {
  _inherits(ResourceStore, _EventEmitter);

  function ResourceStore() {
    var data = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};
    var options = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : { ns: ['translation'], defaultNS: 'translation' };

    _classCallCheck(this, ResourceStore);

    var _this = _possibleConstructorReturn(this, _EventEmitter.call(this));

    _this.data = data;
    _this.options = options;
    return _this;
  }

  ResourceStore.prototype.addNamespaces = function addNamespaces(ns) {
    if (this.options.ns.indexOf(ns) < 0) {
      this.options.ns.push(ns);
    }
  };

  ResourceStore.prototype.removeNamespaces = function removeNamespaces(ns) {
    var index = this.options.ns.indexOf(ns);
    if (index > -1) {
      this.options.ns.splice(index, 1);
    }
  };

  ResourceStore.prototype.getResource = function getResource(lng, ns, key) {
    var options = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : {};

    var keySeparator = options.keySeparator || this.options.keySeparator;
    if (keySeparator === undefined) keySeparator = '.';

    var path = [lng, ns];
    if (key && typeof key !== 'string') path = path.concat(key);
    if (key && typeof key === 'string') path = path.concat(keySeparator ? key.split(keySeparator) : key);

    if (lng.indexOf('.') > -1) {
      path = lng.split('.');
    }

    return utils.getPath(this.data, path);
  };

  ResourceStore.prototype.addResource = function addResource(lng, ns, key, value) {
    var options = arguments.length > 4 && arguments[4] !== undefined ? arguments[4] : { silent: false };

    var keySeparator = this.options.keySeparator;
    if (keySeparator === undefined) keySeparator = '.';

    var path = [lng, ns];
    if (key) path = path.concat(keySeparator ? key.split(keySeparator) : key);

    if (lng.indexOf('.') > -1) {
      path = lng.split('.');
      value = ns;
      ns = path[1];
    }

    this.addNamespaces(ns);

    utils.setPath(this.data, path, value);

    if (!options.silent) this.emit('added', lng, ns, key, value);
  };

  ResourceStore.prototype.addResources = function addResources(lng, ns, resources) {
    for (var m in resources) {
      if (typeof resources[m] === 'string') this.addResource(lng, ns, m, resources[m], { silent: true });
    }
    this.emit('added', lng, ns, resources);
  };

  ResourceStore.prototype.addResourceBundle = function addResourceBundle(lng, ns, resources, deep, overwrite) {
    var path = [lng, ns];
    if (lng.indexOf('.') > -1) {
      path = lng.split('.');
      deep = resources;
      resources = ns;
      ns = path[1];
    }

    this.addNamespaces(ns);

    var pack = utils.getPath(this.data, path) || {};

    if (deep) {
      utils.deepExtend(pack, resources, overwrite);
    } else {
      pack = _extends({}, pack, resources);
    }

    utils.setPath(this.data, path, pack);

    this.emit('added', lng, ns, resources);
  };

  ResourceStore.prototype.removeResourceBundle = function removeResourceBundle(lng, ns) {
    if (this.hasResourceBundle(lng, ns)) {
      delete this.data[lng][ns];
    }
    this.removeNamespaces(ns);

    this.emit('removed', lng, ns);
  };

  ResourceStore.prototype.hasResourceBundle = function hasResourceBundle(lng, ns) {
    return this.getResource(lng, ns) !== undefined;
  };

  ResourceStore.prototype.getResourceBundle = function getResourceBundle(lng, ns) {
    if (!ns) ns = this.options.defaultNS;

    // TODO: COMPATIBILITY remove extend in v2.1.0
    if (this.options.compatibilityAPI === 'v1') return _extends({}, this.getResource(lng, ns));

    return this.getResource(lng, ns);
  };

  ResourceStore.prototype.toJSON = function toJSON() {
    return this.data;
  };

  return ResourceStore;
}(_EventEmitter3.default);

exports.default = ResourceStore;