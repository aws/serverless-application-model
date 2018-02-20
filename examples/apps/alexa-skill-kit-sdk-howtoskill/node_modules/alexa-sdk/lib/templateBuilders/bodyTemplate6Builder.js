'use strict';

const TemplateBuilder = require('./templateBuilder').TemplateBuilder;
const TextUtils = require('../utils/textUtils').TextUtils;

/**
 * Used to create BodyTemplate6 objects
 * 
 * @class BodyTemplate6Builder
 * @extends {TemplateBuilder}
 */
class BodyTemplate6Builder extends TemplateBuilder {
    constructor() {
        super();
        this.template.type = 'BodyTemplate6';
    }

    /**
     * Sets the image for the template
     * 
     * @param {any} image 
     * @returns 
     * @memberof BodyTemplate6Builder
     */
    setImage(image) {
        this.template.image = image;
        return this;
    }

    /**
     * Sets the text content for the template
     * 
     * @param {TextField} primaryText 
     * @param {TextField} secondaryText 
     * @param {TextField} tertiaryText 
     * @returns BodyTemplate6Builder
     * @memberof BodyTemplate6Builder
     */
    setTextContent(primaryText, secondaryText, tertiaryText) {
        this.template.textContent = TextUtils.makeTextContent(primaryText, secondaryText, tertiaryText);
        return this;
    }
}

module.exports.BodyTemplate6Builder = BodyTemplate6Builder;