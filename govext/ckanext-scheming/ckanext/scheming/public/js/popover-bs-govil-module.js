"use strict";

/* popover_govil
 *
 * This JavaScript module adds a Bootstrap popover with some extra info about a
 * dataset to the HTML element that the module is applied to. Users can click
 * on the HTML element to show the popover.
 */
ckan.module('popover_govil', function ($) {
  return {
    initialize: function () {
      // Add a Bootstrap popover to the HTML element (this.el) that this
      // JavaScript module was initialized on.
      this.el.popover({
                content: this.options.content,
                trigger: 'hover',
                placement: 'top',
                container: '.table'});

    }
  };
});
