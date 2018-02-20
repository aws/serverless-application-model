var AlexaLambdaHandler = require('./lib/alexa');

module.exports.handler = AlexaLambdaHandler.LambdaHandler;
module.exports.CreateStateHandler = AlexaLambdaHandler.CreateStateHandler;
module.exports.StateString = AlexaLambdaHandler.StateString;

module.exports.templateBuilders = {
    BodyTemplate1Builder : require('./lib/templateBuilders/bodyTemplate1Builder').BodyTemplate1Builder,
    BodyTemplate2Builder : require('./lib/templateBuilders/bodyTemplate2Builder').BodyTemplate2Builder,
    BodyTemplate3Builder : require('./lib/templateBuilders/bodyTemplate3Builder').BodyTemplate3Builder,
    BodyTemplate6Builder : require('./lib/templateBuilders/bodyTemplate6Builder').BodyTemplate6Builder,
    ListTemplate1Builder : require('./lib/templateBuilders/listTemplate1Builder').ListTemplate1Builder,
    ListTemplate2Builder : require('./lib/templateBuilders/listTemplate2Builder').ListTemplate2Builder,
    ListItemBuilder : require('./lib/templateBuilders/listItemBuilder').ListItemBuilder
};

module.exports.utils = {
    ImageUtils : require('./lib/utils/imageUtils').ImageUtils,
    TextUtils : require('./lib/utils/textUtils').TextUtils
};