var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol ? "symbol" : typeof obj; };

import { sprintf, vsprintf } from './sprintf';

export default {
  name: 'sprintf',
  type: 'postProcessor',

  process: function process(value, key, options) {
    if (!options.sprintf) return value;

    if (Object.prototype.toString.apply(options.sprintf) === '[object Array]') {
      return vsprintf(value, options.sprintf);
    } else if (_typeof(options.sprintf) === 'object') {
      return sprintf(value, options.sprintf);
    }

    return value;
  },
  overloadTranslationOptionHandler: function overloadTranslationOptionHandler(args) {
    var values = [];

    for (var i = 1; i < args.length; i++) {
      values.push(args[i]);
    }

    return {
      postProcess: 'sprintf',
      sprintf: values
    };
  }
};