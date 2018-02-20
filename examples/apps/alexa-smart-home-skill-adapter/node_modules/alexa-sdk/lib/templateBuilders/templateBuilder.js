'use strict';

class TemplateBuilder {
    constructor() {
        this.template = {};
    }

    /**
     * Sets the title of the template
     * 
     * @param {string} title 
     * @returns 
     * @memberof TemplateBuilder
     */
    setTitle(title) {
        this.template.title = title;
        return this;
    }

    /**
     * Sets the token of the template
     * 
     * @param {string} token 
     * @returns 
     * @memberof TemplateBuilder
     */
    setToken(token) {
        this.template.token = token;
        return this;
    }

    /**
     * Sets the background image of the template
     * 
     * @param {Image} image 
     * @returns 
     * @memberof TemplateBuilder
     */
    setBackgroundImage(image) {
        this.template.backgroundImage = image;
        return this;
    }

    /**
     * Sets the backButton behavior
     * 
     * @param {string} backButtonBehavior 'VISIBLE' or 'HIDDEN'
     * @returns 
     * @memberof TemplateBuilder
     */
    setBackButtonBehavior(backButtonBehavior) {
        this.template.backButton = backButtonBehavior;
        return this;
    }

    /**
     * Builds the template JSON object
     * 
     * @returns 
     * @memberof TemplateBuilder
     */
    build() {
        return this.template;
    }
}

module.exports.TemplateBuilder = TemplateBuilder;