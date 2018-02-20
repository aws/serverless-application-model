'use strict';

/**
 * Utility methods for building TextField objects
 * 
 * @class TextUtils
 */
class TextUtils {

    /**
     * Creates a plain TextField object with contents : text
     * 
     * @static
     * @param {string} text contents of plain text object
     * @returns 
     * @memberof TextUtils
     */
    static makePlainText(text) {
        return {
            text : text,
            type : 'PlainText'
        };
    }

    /**
     * Creates a rich TextField object with contents : text
     * 
     * @static
     * @param {string} text 
     * @returns 
     * @memberof TextUtils
     */
    static makeRichText(text) {
        return {
            text : text,
            type : 'RichText'
        };
    }

    /**
     * Creates a textContent
     * 
     * @static
     * @param {{type : string, text : string}} primaryText 
     * @param {{type : string, text : string}} secondaryText 
     * @param {{type : string, text : string}} tertiaryText 
     * @returns 
     * @memberof TextUtils
     */
    static makeTextContent(primaryText, secondaryText, tertiaryText) {
        const textContent = {};
        if(primaryText) {
            textContent.primaryText = primaryText;
        }

        if(secondaryText) {
            textContent.secondaryText = secondaryText;
        }

        if(tertiaryText) {
            textContent.tertiaryText = tertiaryText;
        }

        return textContent;
    }
}

module.exports.TextUtils = TextUtils;