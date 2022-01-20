this.ckan.module('session-notifier', function ($) {
  return {
    initialize: function () {

      var session_timeout = parseInt(this.options.session_timeout);
      var modal_message = this.options.content;

      setTimeout(function () {
        swal(modal_message, {
          closeOnEsc: true,
          closeOnClickOutside: true,
          icon: "warning",
          buttons: ["לא", "כן"],
        }).then((value) => {
          if (value) {
            window.location.href = '/user/login';
          }
          ;
        });
      }, session_timeout * 1000);
    }
  };
});
