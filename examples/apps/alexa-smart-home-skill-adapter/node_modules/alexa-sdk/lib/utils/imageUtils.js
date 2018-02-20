'use strict';

/**
 * Utility functions for creating template image objects
 * 
 * @class ImageUtils
 */
class ImageUtils {

    /**
     * Creates an image object with a single source
     * 
     * These images may be in either JPEG or PNG formats, with the appropriate file extensions.
     * An image cannot be larger than 2 MB
     * You must host the images at HTTPS URLs that are publicly accessible.
     * widthPixels and heightPixels are optional - Do not include them unless they are exactly correct.
     * 
     * By default, for Echo Show, size takes the value X_SMALL. If the other size values are included, 
     * then the order of precedence for displaying images begins with X_LARGE and proceeds downward, 
     * which means that larger images will be downscaled for display on Echo Show if provided.
     * 
     * example : ImageUtils.makeImage('https://url/to/my/img.png', 300, 400, 'SMALL', 'image description')
     * 
     * @static
     * @param {string} url url of the image
     * @param {number} widthPixels (optional) width of the image in pixels
     * @param {number} heightPixels (optional) height of the image in pixels
     * @param {string} size size of the image (X_SMALL, SMALL, MEDIUM, LARGE, X_LARGE)
     * @param {string} description text used to describe the image in a screen reader
     * @returns 
     * @memberof ImageUtils
     */
    static makeImage(url, widthPixels, heightPixels, size, description) {
        var imgObj = { 
            url : url
        };
        
        if (widthPixels && heightPixels) {
            imgObj.widthPixels = widthPixels;
            imgObj.heightPixels = heightPixels;
        }
        
        if (size) {
            imgObj.size = size;
        }

        return ImageUtils.makeImages([imgObj], description);
    }

    /**
     * 
     * Creates an image object with a multiple sources, source images are provided as an array of image objects
     * 
     * These images may be in either JPEG or PNG formats, with the appropriate file extensions.
     * An image cannot be larger than 2 MB
     * You must host the images at HTTPS URLs that are publicly accessible.
     * widthPixels and heightPixels are optional - Do not include them unless they are exactly correct.
     * 
     * By default, for Echo Show, size takes the value X_SMALL. If the other size values are included, 
     * then the order of precedence for displaying images begins with X_LARGE and proceeds downward, 
     * which means that larger images will be downscaled for display on Echo Show if provided.
     * example :
     * let imgArr = [
     *  { 'https://url/to/my/small.png', 300, 400, 'SMALL' },
     *  { 'https://url/to/my/large.png', 900, 1200, 'LARGE' },
     * ]
     *  ImageUtils.makeImage(imgArr, 'image description')
     *
     * @static
     * @param {{url : string, widthPixels : number, heightPixels : number, size : string}[]} imgArr 
     * @param {string} description text used to describe the image in a screen reader
     * @returns 
     * @memberof ImageUtils
     */
    static makeImages(imgArr, description) {
        var image = {};
        if(description) {
            image.contentDescription = description;
        }
        image.sources = imgArr;
        return image;
    }
}

module.exports.ImageUtils = ImageUtils;