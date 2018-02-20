'use strict';

const TemplateBuilder = require('./templateBuilder').TemplateBuilder;
const TextUtils = require('../utils/textUtils').TextUtils;

/**
 * Used to create BodyTemplate2 objects
 * 
 * @class BodyTemplate2Builder
 * @extends {TemplateBuilder}
 */
class BodyTemplate2Builder extends TemplateBuilder {
    constructor() {
        super();
        this.template.type = 'BodyTemplate2';
    }

    /**
     * Sets the image for the template
     * 
     * @param {Image} image 
     * @returns 
     * @memberof BodyTemplate2Builder
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
     * @returns BodyTemplate2Builder
     * @memberof BodyTemplate2Builder
     */
    setTextContent(primaryText, secondaryText, tertiaryText) {
        this.template.textContent = TextUtils.makeTextContent(primaryText, secondaryText, tertiaryText);
        return this;
    }
}

module.exports.BodyTemplate2Builder = BodyTemplate2Builder;