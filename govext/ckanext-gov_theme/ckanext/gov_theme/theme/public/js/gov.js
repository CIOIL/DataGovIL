

$(document).ready(function() {
   //prevent msense accessability element to appear inside iframe
   var windowURL = window.location.href;
   if (windowURL.indexOf('/view/') > -1) {
      setMsenseVisibility('mk-aweb-accessibility-panel-wrapper')
   }


//   $("input[id=field-author_email]").change(function(){
//   jQuery("input[id=field-author]")[0].value = jQuery("input[id=field-author_email]")[0].value;
// });


  if(detectIE()){
    $('html').addClass('ie');
    if(detectIE()=== '11'){
      $('html').addClass('ie11');
    }
    else if(detectIE()=== '10'){
      $('html').addClass('ie10');
    }
  }
    //add auto complete
    // if($('#datasets').length > 0){
    //   addSearchDatasetAutocomplete();
    // }

    //add organization id to
    if($('#field-extras-1-key').length > 0 && $("#content > div.row.wrapper > div > article > header > ul > li.active > a")[0].href.includes("org") > 0 ){
      $('input[id*=field-extras][id*=key]').first().val("organization_id");
    }


    // if($('#organizations').length > 0){
    //   addSearchOrganizationAutocomplete();
    // }
    //
    // if($('#tags').length > 0){
    //   addSearchAutocomplete();
    // }

    //remove text-error link
    if($('.data-viewer-error').length > 0){
      $('.data-viewer-error').find('.text-error a').remove();
      $('.data-viewer-error').find('.btn-large').remove();
    }



});

    function setMsenseVisibility(elem_to_set){
      var style = document.createElement('style');
      style.type = 'text/css';
      style.innerHTML = '.noneImportant { display: none !important; }';
      document.getElementsByTagName('head')[0].appendChild(style);

      // There is delay - we dont know when the accessibility outsource script is loading
      function hideAccessibilityPanel() {
        if (document.getElementById(elem_to_set)) {
          console.log("Success Accessibility");
          document.getElementById(elem_to_set).className = 'noneImportant';
        }
        else{
          setTimeout(hideAccessibilityPanel, 1000);
        }
      }
      hideAccessibilityPanel();

    }


    function detectIE(){
      var ua = window.navigator.userAgent;
      var msie = ua.indexOf('MSIE ');
      if(msie >0 ){
        return "10";
      }

      var trident = ua.indexOf('Trident/');
      if(trident > 0)
      {
        var rv = ua.indexOf('rv:');
        return "11";
      }

      var edge = ua.indexOf('Edge/');
      if(edge >0)
      {
        return parseInt(ua.substring(edge + 5, ua.indexOf('.',edge)), 10);
      }
      //other browser
      return false;
    }

  //   function addSearchAutocomplete(){
  //     try{
  //         var vURL = document.URL;
  //
  //         $("#tags").autocomplete({
  //
  //
  //       //start source
  //       source: function (request, response) {
  //           $.ajax({
  //               url: vURL + "api/2/util/tag/autocomplete",
  //               data: { incomplete: request.term },
  //               dataType:"json",
  //               success: function (data) {
  //                   var transformed = $.map(data, function (el) {
  //
  //                       //array of results
  //                       resultsList = el.Result;
  //
  //                       response($.map (resultsList, function (resultItem , i){
  //                         return {
  //                            value: el.Result[i].Name
  //                         }
  //
  //                       }));
  //
  //
  //                   });
  //               },
  //               error: function (err) {
  //
  //                   response([]);
  //               }
  //           })
  //   }
  //   //end source
  // });
  //
  //     }
  //     catch(err){
  //       txt = "There was an error on gov.js function 'addSearchAutocomplete'.\n\n";
  //       txt += "Error description: " + err.description +"\n\n";
  //       txt += "Click OK to continue.\n\n";
  //       consule.log(txt);
  //     }
  //   }
  //
  //   function addSearchDatasetAutocomplete(){
  //     try{
  //         var getUrl = window.location;
  //
  //         //var getUrl = document.URL;
  //         var baseUrl = getUrl .protocol + "//" + getUrl.host + "/";
  //         //var baseUrl = getBaseUrl();//vURL .protocol + "//" + vURL.host + "/";
  //         $("#datasets").autocomplete({
  //
  //
  //       //start source
  //       source: function (request, response) {
  //           $.ajax({
  //               url: baseUrl + "api/2/util/dataset/autocomplete",
  //               data: { incomplete: request.term },
  //               dataType:"json",
  //               success: function (data) {
  //                   var transformed = $.map(data, function (el) {
  //
  //                       //array of results
  //                       resultsList = el.Result;
  //
  //                       response($.map (resultsList, function (resultItem , i){
  //                         return {
  //                            value: el.Result[i].title
  //                         }
  //
  //                       }));
  //
  //
  //                   });
  //               },
  //               error: function (err) {
  //
  //                   response([]);
  //               }
  //           })
  //   }
  //   //end source
  // });
  //
  //     }
  //     catch(err){
  //       txt = "There was an error on gov.js function 'addSearchDatasetAutocomplete'.\n\n";
  //       txt += "Error description: " + err.description +"\n\n";
  //       txt += "Click OK to continue.\n\n";
  //       consule.log(txt);
  //     }
  //   }
  //
  //   function addSearchOrganizationAutocomplete(){
  //     try{
  //         var getUrl = window.location;
  //
  //         //var getUrl = document.URL;
  //         var baseUrl = getUrl .protocol + "//" + getUrl.host + "/";
  //         //var baseUrl = getBaseUrl();//vURL .protocol + "//" + vURL.host + "/";
  //         $("#organizations").autocomplete({
  //
  //
  //       //start source
  //       source: function (request, response) {
  //           $.ajax({
  //               url: baseUrl + "api/2/util/organization/autocomplete",
  //               data: { q: request.term },
  //               dataType:"json",
  //               success: function (data) {
  //                   var transformed = $.map(data, function (el) {
  //
  //                       //array of results
  //                       resultsList =data;
  //
  //                       response($.map (resultsList, function (resultItem, i ){
  //                         return {
  //                            value: resultsList[i].title
  //                         }
  //
  //                       }));
  //
  //
  //                   });
  //               },
  //               error: function (err) {
  //
  //                   response([]);
  //               }
  //           })
  //   }
  //   //end source
  // });
  //
  //     }
  //     catch(err){
  //       txt = "There was an error on gov.js function 'addSearchDatasetAutocomplete'.\n\n";
  //       txt += "Error description: " + err.description +"\n\n";
  //       txt += "Click OK to continue.\n\n";
  //       consule.log(txt);
  //     }
  //   }

