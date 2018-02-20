'use strict';

const TextUtils = require('../utils/textUtils').TextUtils;

/**
 * Used to build a list of ListItems for ListTemplate
 * 
 * @class ListItemBuilder
 */
class ListItemBuilder {
    constructor() {
        this.items = [];
    }

    /**
     * Add an item to the list of template
     * 
     * @param {Image} image 
     * @param {string} token 
     * @param {TextField} primaryText 
     * @param {TextField} secondaryText 
     * @param {TextField} tertiaryText 
     * @memberof ListItemBuilder
     */
    addItem(image, token, primaryText, secondaryText, tertiaryText) {
        const item = {};
        item.image = image;
        item.token = token;
        item.textContent = TextUtils.makeTextContent(primaryText, secondaryText, tertiaryText);
        this.items.push(item);
        return this;
    }

    build() {
        return this.items;
    }
}

module.exports.ListItemBuilder = ListItemBuilder;