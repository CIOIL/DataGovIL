// Enable JavaScript's strict mode. Strict mode catches some common
// programming errors and throws exceptions, prevents some unsafe actions from
// being taken, and disables some confusing and bad JavaScript features.
"use strict";

/* ajax_xloader_status
 *
 *  This module is retrieving the resource uploader status (translated).
 *  The interval time is set in the config section 'ckanext.xloader.xloader_status_refresh_interval'
 *  If the return status is complete or error the module is clearing the interval.
 *
 *  Parameters:
 *    xloader_status_url_api          => url of the api that return the json result of the status and
 *                                        the translated status
 *
 *    xloader_status_key              => api key for authentication
 *
 *    xloader_status_refresh_interval => interval in milliseconds
 */

ckan.module('ajax_xloader_status', function ($) {
  return {
    initialize: function () {

      const xloader_status_url_api = this.options.xloader_status_url_api;
      const xloader_status_key = this.options.xloader_status_key;

      let fetchDataFunc = () => {
        $.ajax({
          url:      xloader_status_url_api,
          headers:  {"Authorization": xloader_status_key},
          success:   (result) => {

            const json_result = JSON.parse(result);
            $('#xloader_result').text(json_result.translated_status);

            // Update hidden field within the status for other js modules
            $('#xloader_hidden_status_result').text(json_result.status);

            // Clear the interval
            if (json_result.status === 'complete' || json_result.status === 'error' )
              clearInterval(interval_Id);
          },
          error: (jqXHR, exception) => {
            console.log("Error Msg: " + jqXHR.responseText);
          }
        });
      };

      let interval_Id = setInterval(fetchDataFunc,parseInt(this.options.xloader_status_refresh_interval));
    }
  };
});
