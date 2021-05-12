// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

/* ajax_xloader_last_updated
 *
 *  This module is retrieving the resource uploader last updated time (translated).
 *  The interval time is set in the config section 'ckanext.xloader.xloader_last_updated_refresh_interval'
 *
 *  Parameters:
 *    xloader_last_updated_refresh_interval => interval in milliseconds
 */

ckan.module('ajax_xloader_last_updated', function ($) {
  return {
    initialize: function () {
      $.proxyAll(this, /_on/);
      let fetchDataFunc = () => {
        this.sandbox.client.getTemplate('xloader_last_updated_result.html',
                                            this.options,
                                            this._onReceiveSnippet);
      };

      let interval_Id = setInterval(fetchDataFunc,parseInt(this.options.xloader_last_updated_refresh_interval));
    },

    _onReceiveSnippet: function(html) {
      this.el.text($(html).text());
      $(this.el).attr('title',$(html).attr('title'));
    }
  };
});
