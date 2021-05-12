"use strict";

/* ajax_xloader_upload_log
 *
 *  This module is showing the upload log of the DataStore using ajax calls.
 *  The interval time is set in the config section 'ckanext.xloader.xloader_upload_log_refresh_interval'
 *
 *  Parameters:
 *    xloader_upload_log_refresh_interval => interval in milliseconds
 */

ckan.module('ajax_xloader_upload_log', function ($) {
  return {
    initialize: function () {

      $.proxyAll(this, /_on/);

      this.sandbox.client.getTemplate('xloader_upload_log_result.html',
        this.options,
        this._onReceiveSnippet);

      let fetchDataFunc = () => {
        this.sandbox.client.getTemplate('xloader_upload_log_result.html',
          this.options,
          this._onReceiveSnippet);

        // Clear the interval
        const xloader_status = $('#xloader_hidden_status_result').text();
        if (xloader_status==='complete' ||
            xloader_status==='error') {
          clearInterval(interval_Id);
        }
      };

      let interval_Id = setInterval(fetchDataFunc, parseInt(this.options.xloader_upload_log_refresh_interval));
    },

    _onReceiveSnippet: function (html) {
      $(this.el).html(html);
      $('a[data-target="popover"]').popover();
    }
  };
});
