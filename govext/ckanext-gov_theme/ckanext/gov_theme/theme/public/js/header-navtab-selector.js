"use strict";

this.ckan.module('header-navtab-selector', function ($) {
    return {
      initialize: function () {
        var parentSelector = this.options.parent_selector;
        var cssClassToggle = this.options.css_class_toggle;

        this.el.children(parentSelector).each(function () {
          var currentChildrenHref = $(this).children('a').attr('href')
          if (window.location.pathname === currentChildrenHref ||
          (currentChildrenHref !== "/" && window.location.pathname.includes(currentChildrenHref)
          && window.location.pathname.indexOf(currentChildrenHref) < 1)) {
            $(this).children('div').addClass(cssClassToggle);
            $(this).children('a').css("font-weight", "bold");
          }
        });
      }
    }
  }
);
