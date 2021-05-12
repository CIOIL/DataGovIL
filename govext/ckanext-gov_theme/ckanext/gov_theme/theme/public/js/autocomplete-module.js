/* Media Grid
 * Super simple plugin that waits for all the images to be loaded in the media
 * grid and then applies the jQuery.masonry to then
 */
// https://masonry.desandro.com/options.html
this.ckan.module('autocomplete-module', function ($) {
  return {
    initialize: function () {
      $.proxyAll(this, /_/);

      if ($('#datasets').length > 0) {
        this._addSearchDatasetAutocomplete();
      }

      if ($('#organizations').length > 0) {
        this._addSearchOrganizationAutocomplete();
      }

      if ($('#tags').length > 0) {
        this._addSearchAutocomplete();
      }
    },

    _addSearchAutocomplete: function () {
      try {
        var vURL = document.URL;

        $("#tags").autocomplete({


          //start source
          source: function (request, response) {
            $.ajax({
              url: vURL + "api/2/util/tag/autocomplete",
              data: {incomplete: request.term},
              dataType: "json",
              success: function (data) {
                var transformed = $.map(data, function (ele) {

                  //array of results
                  var resultsList = ele.Result;

                  response($.map(resultsList, function (resultItem, i) {
                    return {
                      value: ele.Result[i].Name
                    }

                  }));


                });
              },
              error: function (err) {

                response([]);
              }
            })
          }
          //end source
        });

      } catch (err) {
        txt = "There was an error on gov.js function 'addSearchAutocomplete'.\n\n";
        txt += "Error description: " + err.description + "\n\n";
        txt += "Click OK to continue.\n\n";
        consule.log(txt);
      }
    },

    _addSearchDatasetAutocomplete: function () {
      try {
        var getUrl = window.location;

        //var getUrl = document.URL;
        var baseUrl = getUrl.protocol + "//" + getUrl.host + "/";
        //var baseUrl = getBaseUrl();//vURL .protocol + "//" + vURL.host + "/";
        $("#datasets").autocomplete({


          //start source
          source: function (request, response) {
            $.ajax({
              url: baseUrl + "api/2/util/dataset/autocomplete",
              data: {incomplete: request.term},
              dataType: "json",
              success: function (data) {
                var transformed = $.map(data, function (ele) {

                  //array of results
                  var resultsList = ele.Result;

                  response($.map(resultsList, function (resultItem, i) {
                    return {
                      value: ele.Result[i].title
                    }

                  }));


                });
              },
              error: function (err) {

                response([]);
              }
            })
          }
          //end source
        });

      } catch (err) {
        txt = "There was an error on gov.js function 'addSearchDatasetAutocomplete'.\n\n";
        txt += "Error description: " + err.description + "\n\n";
        txt += "Click OK to continue.\n\n";
        consule.log(txt);
      }
    },

    _addSearchOrganizationAutocomplete: function () {
      try {
        var getUrl = window.location;

        //var getUrl = document.URL;
        var baseUrl = getUrl.protocol + "//" + getUrl.host + "/";
        //var baseUrl = getBaseUrl();//vURL .protocol + "//" + vURL.host + "/";
        $("#organizations").autocomplete({


          //start source
          source: function (request, response) {
            $.ajax({
              url: baseUrl + "api/2/util/organization/autocomplete",
              data: {q: request.term},
              dataType: "json",
              success: function (data) {
                var transformed = $.map(data, function (ele) {

                  //array of results
                  var resultsList = data;

                  response($.map(resultsList, function (resultItem, i) {
                    return {
                      value: resultsList[i].title
                    }

                  }));


                });
              },
              error: function (err) {

                response([]);
              }
            })
          }
          //end source
        });

      } catch (err) {
        txt = "There was an error on gov.js function 'addSearchDatasetAutocomplete'.\n\n";
        txt += "Error description: " + err.description + "\n\n";
        txt += "Click OK to continue.\n\n";
        consule.log(txt);
      }
    }
  };
});
