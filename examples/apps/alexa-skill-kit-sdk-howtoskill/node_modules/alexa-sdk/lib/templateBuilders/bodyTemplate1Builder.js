'use strict';

const TemplateBuilder = require('./templateBuilder').TemplateBuilder;
const TextUtils = require('../utils/textUtils').TextUtils;

/**
 * Used to create BodyTemplate1 objects
 * 
 * @class BodyTemplate1Builder
 * @extends {TemplateBuilder}
 */
class BodyTemplate1Builder extends TemplateBuilder {
    constructor() {
        super();
        this.template.type = 'BodyTemplate1';
    }

    /**
     * Sets the text content for the template
     * 
     * @param {TextField} primaryText 
     * @param {TextField} secondaryText 
     * @param {TextField} tertiaryText 
     * @returns BodyTemplate1Builder
     * @memberof BodyTemplate1Builder
     */
    setTextContent(primaryText, secondaryText, tertiaryText) {
        this.template.textContent = TextUtils.makeTextContent(primaryText, secondaryText, tertiaryText);
        return this;
    }
}

module.exports.BodyTemplate1Builder = BodyTemplate1Builder;