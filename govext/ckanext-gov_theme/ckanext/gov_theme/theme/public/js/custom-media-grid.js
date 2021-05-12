/* Media Grid
 * Super simple plugin that waits for all the images to be loaded in the media
 * grid and then applies the jQuery.masonry to then
 */
// https://masonry.desandro.com/options.html
this.ckan.module('custom-media-grid', function ($) {
  return {
    initialize: function () {
      var wrapper = this.el;
      wrapper.imagesLoaded(function() {
        wrapper.masonry({
          itemSelector: '.media-item',
          percentPosition: true,
          originLeft: false,
          gutter: 10
        });
      });
    }
  };
});
