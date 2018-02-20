'use strict';

const TemplateBuilder = require('./templateBuilder').TemplateBuilder;

class ListTemplate2Builder extends TemplateBuilder {
    constructor() {
        super();
        this.template.type = 'ListTemplate2';
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

module.exports.ListTemplate2Builder = ListTemplate2Builder;