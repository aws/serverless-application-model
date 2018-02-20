'use strict';

const TemplateBuilder = require('./templateBuilder').TemplateBuilder;

/**
 * Used to create ListTemplate1 objects
 * 
 * @class ListTemplate1Builder
 * @extends {TemplateBuilder}
 */
class ListTemplate1Builder extends TemplateBuilder {
    constructor() {
        super();
        this.template.type = 'ListTemplate1';
    }

    /**
     * Set the items for the list
     * 
     * @param {any} listItems 
     * @returns 
     * @memberof ListTemplate1Builder
     */
    setListItems(listItems) {
        this.template.listItems = listItems;
        return this;
    }
}

module.exports.ListTemplate1Builder = ListTemplate1Builder;