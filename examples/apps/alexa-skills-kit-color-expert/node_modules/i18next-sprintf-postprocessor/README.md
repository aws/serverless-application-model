# Introduction

This is a i18next postProcessor enabling sprintf usage for translations.

# Getting started

Source can be loaded via [npm](https://www.npmjs.com/package/i18next-sprintf-postprocessor), bower or [downloaded](https://github.com/i18next/i18next-sprintf-postprocessor/blob/master/i18nextSprintfPostProcessor.min.js) from this repo.

```
# npm package
$ npm install i18next-sprintf-postprocessor

# bower
$ bower install i18next-sprintf-postprocessor
```

- If you don't use a module loader it will be added to window.i18nextSprintfPostProcessor


Wiring up:

```js
import i18next from 'i18next';
import sprintf from 'i18next-sprintf-postprocessor';

i18next
  .use(sprintf)
  .init(i18nextOptions);
```

# usage sample

```js
// given loaded resources
// translation: {
//   key1: 'The first 4 letters of the english alphabet are: %s, %s, %s and %s',
//   key2: 'Hello %(users[0].name)s, %(users[1].name)s and %(users[2].name)s',
//   key3: 'The last letter of the english alphabet is %s',
//   key3: 'Water freezes at %d degrees'
// }

i18next.t('key1', { postProcess: 'sprintf', sprintf: ['a', 'b', 'c', 'd'] });
// --> 'The first 4 letters of the english alphabet are: a, b, c and d'

i18next.t('key2', { postProcess: 'sprintf', sprintf: { users: [{name: 'Dolly'}, {name: 'Molly'}, {name: 'Polly'}] } });
// --> 'Hello Dolly, Molly and Polly'
```

# Using overloadTranslationOptionHandler

```js
import i18next from 'i18next';
import sprintf from 'i18next-sprintf-postprocessor';

i18next.init({
  overloadTranslationOptionHandler: sprintf.overloadTranslationOptionHandler
});

// given loaded resources
// translation: {
//   key1: 'The first 4 letters of the english alphabet are: %s, %s, %s and %s',
//   key2: 'Hello %(users[0].name)s, %(users[1].name)s and %(users[2].name)s',
//   key3: 'The last letter of the english alphabet is %s',
//   key3: 'Water freezes at %d degrees'
// }

i18next.t('interpolationTest1', 'a', 'b', 'c', 'd');
// --> 'The first 4 letters of the english alphabet are: a, b, c and d'

i18next.t('interpolationTest3', 'z');
// --> 'The last letter of the english alphabet is z'

i18next.t('interpolationTest4', 0);
// --> 'Water freezes at 0 degrees'
```
