### 3.5.2
- remove the module entry point again will be added in 4.0.0

### 3.5.1
- fix build output add a test file to test the generated build

### 3.5.0
- Setting options on individual translations override, rather than merge global configs [#832](https://github.com/i18next/i18next/issues/832)
- Create an new translator when cloning i18next instance [#834](https://github.com/i18next/i18next/pull/834)
- allows fallbackLng to be an string, an array or an object defining fallbacks for lng, lng-region plus default, eg

  fallbackLng: {
    'de-CH': ['fr', 'it', 'en'],
    'de': ['fr', 'en'],
    'zh-Hans': ['zh-Hant', 'en'],
    'zh-Hant': ['zh-Hans', 'en'],
    'default': ['en']
  }


### 3.4.4
- Fix Interpolator.escapeValue defaulting to undefined in some cases [#826](https://github.com/i18next/i18next/issues/826)

### 3.4.3
- Fix Interpolator formatter exception error propagation due to not reset RegExp indices [#820](https://github.com/i18next/i18next/issues/820)

### 3.4.2
- assert dir function does not crash if no language available

### 3.4.1
- fix issue with format containing formatSeparator for interpolation formatting

### 3.4.0
- adds formatting 'format this: {{var, formatRule}}' having a function on options.interpolation.format: function(value, format, lng) { return value } like suggested here [#774](https://github.com/i18next/i18next/issues/774)

### 3.3.1
- fixed an issue with several unescaped key in the interpolation string [#746](https://github.com/i18next/i18next/pull/746)

### 3.3.0
- allows option `nonExplicitWhitelist` on init [#741](https://github.com/i18next/i18next/pull/741)

### 3.2.0
- adds api function i18next.reloadResources(), i18next.reloadResources(lngs, ns) to trigger a reload of translations

### 3.1.0
- emits missingKey always (like console.log) even if saveMissing is of -> use missingKeyHandler if you only want the trigger only on saveMissing: true

### 3.0.0
- **[BREAKING]** per default i18next uses now the same index as used in gettext for plurals. eg. for arabic suffixes are 0,1,2,3,4,5 instead of 0,1,2,3,11,100. You can enforce old behaviour by setting compatibilityJSON = 'v2' on i18next init.
- **[BREAKING]** AMD export will be unnamed now
- don't call saveMissing if no lng

### 2.5.1
- fixes rtl support [#656](https://github.com/i18next/i18next/pull/656/files)

### 2.5.0
- allow null or empty string as defaultValue
- init option `initImmediate (default: true)` to init without immediate

### 2.4.1
- if passing resources don't immediate loading fixes [#636](https://github.com/i18next/i18next/issues/636)

### 2.4.0
- support now language code variants with scripts and other exotic forms: zh-Hans-MO, sgn-BE-fr, de-AT-1996,...
- trigger of changeLanguage, load of data with a setTimeout to allow other operations meanwhile

### 2.3.5
- Only add language to preload array when new [#613](https://github.com/i18next/i18next/pull/613/files)

### 2.3.4
- get babel 6 output IE compatible: https://jsfiddle.net/jamuhl/2qc7oLf8/

### 2.3.2
- add index to make export compatible again

### 2.3.1
- build /dist/es with included babelhelpers

### 2.3.0
- change build chain to use rollup...allows 'js:next' and reduces build from 45kb to 33kb minified (/lib --> /dist/commonjs folder, new /dist/es for rollup,...)
- fixes detection when using both context and pluralization and context not found. [#851](https://github.com/i18next/i18next/pull/581)

### 2.2.0
- return instance after init for further chaning
- make init optional on backend, cache
- package.json entry points now to /lib not to mangled version...this might be the better solution for most use cases (build chains built on npm, webpack, browserify, node,...)

### 2.1.0
- allow keySeparator, nsSeparator = false to turn that off

### 2.0.26
- extended emitted arguments on 'added' event

### 2.0.24
- fixes unneeded reload of resources that failed to load

### 2.0.23
- fixes returnObjects in case of multiple namespaces

### 2.0.22
- add options for context, pluralSeparator

### 2.0.21
- clear done load request in backendConnector

### 2.0.20
- pass full options to detectors as third arg

### 2.0.19
- do not callback err in backendConnector if no backend is specified

### 2.0.18
- check for fallbackLng exist

### 2.0.17
- adds cimode to options.whitelist if set
- emits failedLoading on load error

### 2.0.16
- adds addResource to i18next API
- fix init of i18next without options, callback

### 2.0.15
- avoid loading of resources for lng=cimode

### 2.0.14
- enhance callback on load from backend...wait for pendings

### 2.0.10
- fixing build chain
- do not post process on nested translation resolve

### 2.0.5
- fixing allow nesting on interpolated nesting vars

### 2.0.4
- don't log lng changed if no lng was detected
- extend result on arrayJoins

### 2.0.1
- assert defaults are arrays where needed
- assert calling lngUtils.toResolveHierarchy does not add undefined as code if called without code param


### 2.0.0
- complete rewrite of i18next codebase

---------


### 1.11.2
- replace forEach loop to support IE8 [PR 461](https://github.com/i18next/i18next/pull/461)

### 1.11.1
- fixes issue in nesting using multiple namespaces and lookups in fallback namespaces
- Fix use of sprintf as shortcutFunction when first argument falsey [PR 453](https://github.com/i18next/i18next/pull/453)

### 1.11.0
- Add nsseparator and keyseparator as options to translation function [PR 446](https://github.com/i18next/i18next/pull/446)
- Resolves issue #448 - TypeScript errors [PR 449](https://github.com/i18next/i18next/pull/449)
- Fixing _deepExtend to handle keys deep existing in source and target [PR 444](https://github.com/i18next/i18next/pull/444)
- `resource` to `resources` in addResources function [PR 440](https://github.com/i18next/i18next/pull/440)
- Runs multiple post processes for missing translations [PR 438](https://github.com/i18next/i18next/pull/438)
- Add support to override Ajax HTTP headers [PR 431](https://github.com/i18next/i18next/pull/431)
- Fixed mnk plural definition [PR 427](https://github.com/i18next/i18next/pull/427)
- Add dir function to return directionality of current language, closes… [PR 413](https://github.com/i18next/i18next/pull/413)

### 1.10.3
- fixes issue where lng get fixed on data-i18n-options
- [SECURITY] merges Reimplement XSS-vulnerable sequential replacement code [PR 443](https://github.com/i18next/i18next/pull/443)

### 1.10.2
- streamline callback(err, t) for case where resStore is passed in

### 1.10.1
- fixes Adds jquery like functionality without the jquery plugin. [PR 403](https://github.com/i18next/i18next/pull/403) by adding it to output

### 1.10.0
- [BREAKING] new callbacks will be node.js conform function(err, t) | Forward the error from sync fetch methods to the init callback function [PR 402](https://github.com/i18next/i18next/pull/402)
- fix fallback lng option during translations [PR 399](https://github.com/i18next/i18next/pull/399)
- Adds jquery like functionality without the jquery plugin. [PR 403](https://github.com/i18next/i18next/pull/403)

### 1.9.1
- fix fallback lng option during translations [PR 399](https://github.com/i18next/i18next/pull/399)
- Adds jquery like functionality without the jquery plugin. [PR 403](https://github.com/i18next/i18next/pull/403)

### 1.9.0
- i18n.noConflict() [PR 371](https://github.com/i18next/i18next/pull/371)
- fix fallback to default namepsace when namespace passed as an option [PR 375](https://github.com/i18next/i18next/pull/375)
- cache option for ajax requests [PR 376](https://github.com/i18next/i18next/pull/376)
- option to show key on value is empty string [PR 379](https://github.com/i18next/i18next/pull/379)
- Add isInitialized method [PR 380](https://github.com/i18next/i18next/pull/380)
- Null check for detectLngFromLocalStorage [PR 384](https://github.com/i18next/i18next/pull/384)
- support for adding timeout in configuration for ajax request [PR 387](https://github.com/i18next/i18next/pull/387)

### 1.8.2
- fixes build of commonjs with jquery file

### 1.8.0
- [BREAKING] adds custom build for commonjs with jquery...default will be without require for jquery
- fixes issue [issue 360](https://github.com/i18next/i18next/issues/360)
- expose applyReplacement on api
- save resources to localStorage when useLocaleStore is true
- add support on key is a number
- added getResourceBundle to API
- allow multiple post-processors
- fallback to singular if no plural is found fixes issue [issue 356](https://github.com/i18next/i18next/issues/356)
- access localstorage always with try catch fixes issue [issue 353](https://github.com/i18next/i18next/issues/353)

### 1.7.7
- fixes issue with stack overflow on t(lng, count)
- fixes empty value fallback when processing secondary ns

### 1.7.6
- fixes lng detection (i18next-client on npm)

### 1.7.5
- adds option to define defaultOptions, which gets merged into t(options) [issue 307](https://github.com/i18next/i18next/issues/307)
- optimization of size added by plural rules
- handle error on json parse when using internal xhr
- fixes plural/singular on count if going on fallbacks eg. fr --> en
- fixes global leak of sync in amd versions
- apply options.lowerCaseLng to fallbackLng too
- added hasResourceBundle(lng, ns) to check if bundle exists
- added experimental i18n.sync.reload --> resets resStore and reloads resources
- catch issues with localStorage quota
- changes detectlanguage to support whitelist entries

### 1.7.4
- add resource bundle gets deep extend flag i18n.addResourceBundle(lng, ns, { 'deep': { 'key2': 'value2' }}, true);
- new functions to add one key value or multiple i18n.addResource(lng, ns, key, value);, i18n.addResources(lng, ns, {'key1': 'value1', 'deep.key2': 'value2'});
- lngWhitelist merged
- override postMissing function
- allow floats for count
- added indefinite functionality for plurals
- optional set replacing vars to replace member to avoid collision with other options
- experimental optional detectLngFromLocalStorage
- fix for norwegian language

### 1.7.3
- solves issue with ie8 not providing .trim function on string -> added to shim
- set data using $(selector).i18n() on data-i18n='[data-someDataAttr]key'
- more bullet proof state handling on failed file load
- corrected latvian plurals based on [issue 231](https://github.com/jamuhl/i18next/issues/231)
- allow array of fallback languages
- allow int in values passed to shortcut sprintf
- setLng to 'cimode' will trigger a CI mode returning 'key' instead of translation

### 1.7.2
- introducing option fallbackOnEmpty -> empty string will fallback
- added function removeResourceBundle(lng, ns) -> removes a resource set
- fixed issue with no option passed to setLng
- added ability to prepend, append content with data-i18n attributes
- introducing objectTreeKeyHandler
- fixes issue with i18n.t(null), i18n.t(undefined) throwing exception
- returnObjectTrees does not mangle arrays, functions, and regexps
- optimized structure for bower support

### 1.7.1
- fixed some typo
- allow translate to take an array of keys - take first found
- allow numbers in object trees

### 1.7.0
- test if initialisation finished before allowing calling t function
- setting option fixLng=true will return t function on init or setLng with the lng fixed for every subsequent call to t
- grab key from content if attr data-i18n has no value
- setting shortcutFunction to 'defaultValue' allows calling i18n.t(key, defaultValue)
- empty string in defaultValue is now valid no longer displaying key
- allow option cookieDomain
- fixes issue #115 out of stack exception in IE8 by recursing _translate in objectTrees

### 1.6.3
- option to parse key if missing
- fixes issue where plural don't get translated if language is passed in t options
- fixes issue where key or defaultValue aren't postProcessed with itself as value
- fixes issue with fallbackLng = false in combination with sendMissingTo = fallback
- fixes namespace fallback loop to only loop if array has really a ns in it

### 1.6.2
- fixes some var typo
- fixes sendMissing to correct namespace
- fixes sendMissing in combination with fallbackNS

### 1.6.1
- PR #106 optionally un/escape interpolated content
- PR #101 automatic gettext like sprintf syntax detection + postprocess injection
- customload will get called on dynamicLoad too
- fixes namespace array settings if loaded resourcebundle or additional namespaces
- lookup of not existend resouces can be fallbacked to other namespaces - see option fallbackNS (array or string if one ns to fallback to)
- defaultValues get postProcessed
- BREAKING: per default null values in resources get translated to fallback. This can be changed by setting option fallbackOnNull to false
- PR #81 added support for passing options to nested resources
- PR #88 added an exists method to check for the existence of a key in the resource store
- fixed issue with null value throws in applyReplacement function
- fixed issue #80 empty string lookup ends in fallback instead of returning result in language
- fixed issue with null value in resources not returning expected value
- optimized tests to use on server (nodejs) too
- allow zepto as drop in replacement for $
- using testacular as runner
- upgraded to grunt 0.4.0
- fixed optional interpolation prefix/suffix not used in plural translation cases
- optimized check if there are multiple keys for the data-i18n attribute to parse

### 1.6.0
- option to specify target to set attributes with jquery function by using 'data-i18n-target attribute'
- function to set new options for nesting functionality
- function to add resources after init
- option to lookup in default namespace if value is not found in given namespace
- option to change interpolation prefix and suffix via translation options
- fixed issue with using ns/keyseparator on plurals, context,...
- fixed issue with posting missing when not using jquery
- post missing in correct lng if lng is given in translation options
- proper usage of deferred object in init function
- fixed issue replacing values in objectTree

### 1.5.10
- BREAKING: fixed plural rules for languages with extended plural forms (more than 2 forms)
- merged pull #61 - custom loader (enables jsonp or other loading custom loading strategies)
- escaping interpolation prefix/suffix for proper regex replace

### 1.5.9
- functions to load additional namespaces after init and to set default namespace to something else
- set if you don't want to read defaultValues from content while using jquery fc
- set dataAttribute to different value
- set cookieName to different value
- some smallbugfixes
- typesafe use of console if in debug mode

### 1.5.8
- disable cookie usage by setting init option useCookie to false
- accept empty string as translation value
- fixed bug in own ajax implementation not using proper sendType
- fixed bug for returning objTree in combination with namespace
- fixed bug in plurals of romanic lngs

### 1.5.7
- pass namespace in t() options
- interpolation nesting
- changable querystring param to look language up from

### 1.5.6
- typesafe check for window, document existance
- runnable under rhino
- seperated amd builds with/without jquery

### 1.5.5
- __BREAKING__ added all plurals: suffixes will new be same as in gettext usage (number indexes key_plural_0|2|3|4|5|7|8|10|11|20|100), additional if needed signature of addRule has changed
- added sprintf as postprocessor -> postProcess = 'sprintf' and sprintf = obj or array
- set default postProcessor on init
- redone build process with grunt
- drop in replacement for jquery each, extend, ajax
- setting fallbackLng to false will stop loading and looking it up
- option to load only current or unspecific language files

### 1.5.0
- pass options to sync._fetchOne, use options for fetching
- support for i18next-webtranslate

### 1.4.1
- post processor
- __BREAKING:__ localStorage defaults to false
- added localStorageExpirationTime for better caching control
- few bug fixes

### 1.4.0
- preload multiple languages
- translate key to other language than current
- fixed issue with namespace usage in combination with context and plurals
- more options to send missing values
- better amd support

### 1.3.4
- set type of ajax request to GET (options sendType: default POST)
- set cookie expiration (options cookieExpirationTime: in minutes)
- read / cache translation options (context, count, ...) in data-attribute (options useDataAttrOptions: default false)

### 1.3.3
- optional return an objectTree from translation
- use jquery promises or callback in initialisation
- rewrote all tests with mocha.js

### 1.3.2
- options to init i18next sync (options -> getAsync = false)
- replace all occurence of replacement string

### 1.3.1
- pass options to selector.i18n() thanks to [@hugojosefson](https://github.com/jamuhl/i18next/pull/10)
- close [issue #8(https://github.com/jamuhl/i18next/issues/8)]: Fail silently when trying to access a path with children
- cleanup
- debug flag (options.debug -> write infos/errors to console)

### 1.2.5
- fix for IE8

### 1.2.4
- added indexOf for non ECMA-262 standard compliant browsers (IE < 9)
- calling i28n() on element with data-i18n attribute will localize it now (i18n now not only works on container elements child)

### 1.2.3

- extended detectLng: switch via qs _setLng=_ or cookie _i18next_
- assert county in locale will be uppercased `en-us` -> `en-US`
- provide option to have locale always lowercased _option lowerCaseLng_
- set lng cookie when set in init function

### 1.2

- support for translation context
- fixed zero count in plurals
- init without options, callback

### 1.1

- support for multiple plural forms
- common.js enabled (for node.js serverside)
- changes to be less dependent on jquery (override it's functions, add to root if no jquery)
- enable it on serverside with node.js [i18next-node](https://github.com/jamuhl/i18next-node)

### 1.0

- support for other attribute translation via _data-i18n_ attribute
- bug fixes
- tests with qunit and sinon

### 0.9

- multi-namespace support
- loading static files or dynamic route
- jquery function for _data-i18n_ attibute
- post missing translations to the server
- graceful fallback en-US -> en -> fallbackLng
- localstorage support
- support for pluralized strings
- insertion of variables into translations
- translation nesting
