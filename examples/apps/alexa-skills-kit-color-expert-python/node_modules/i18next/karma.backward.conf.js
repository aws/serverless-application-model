module.exports = function(karma) {
  karma.set({

    frameworks: [ 'mocha', 'expect', 'sinon', 'browserify' ],

    files: [
      //'vendor/external.js',
      'test/backward/**/*.compat.js',
      { pattern: 'test/backward/locales/**/*.json', watched: true, included: false, served: true},
    ],

    proxies: {
      '/locales': 'http://localhost:9877/base/test/backward/locales'
    },

    reporters: [ 'spec' ],

    preprocessors: {
      'test/backward/**/*.compat.js': [ 'browserify' ]
    },

    browsers: [ 'PhantomJS' ],

    port: 9877,

    //logLevel: 'LOG_DEBUG',

    //singleRun: true,
    //autoWatch: false,
    //
    // client: {
    //   mocha: {
    //     reporter: 'spec', // change Karma's debug.html to the mocha web reporter
    //     ui: 'tdd'
    //   }
    // },

    // browserify configuration
    browserify: {
      debug: true,
      transform: [ 'babelify'/*, 'brfs' */]
    }
  });
};
