'use strict';

const TemplateBuilder = require('./templateBuilder').TemplateBuilder;
const TextUtils = require('../utils/textUtils').TextUtils;

/**
 * Used to create BodyTemplate3 objects
 * 
 * @class BodyTemplate3Builder
 * @extends {TemplateBuilder}
 */
class BodyTemplate3Builder extends TemplateBuilder {
    constructor() {
        super();
        this.template.type = 'BodyTemplate3';
    }

    /**
     * Sets the image for the template
     * 
     * @param {any} image 
     * @returns 
     * @memberof BodyTemplate3Builder
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
     * @returns BodyTemplate3Builder
     * @memberof BodyTemplate3Builder
     */
    setTextContent(primaryText, secondaryText, tertiaryText) {
        this.template.textContent = TextUtils.makeTextContent(primaryText, secondaryText, tertiaryText);
        return this;
    }
}

module.exports.BodyTemplate3Builder = BodyTemplate3Builder;