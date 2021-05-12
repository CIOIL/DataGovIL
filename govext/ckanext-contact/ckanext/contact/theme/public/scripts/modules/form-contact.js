/*
 * Non-modal contact form. Should be attached to the form itself. The data is sent as a standard
 * POST form submit.
 *
 * Example:
 *
 *   <form data-module="form-contact"> ... </form>
 *
 */
ckan.module('form-contact', function($, _) {
    let self = null;

    return {
        /**
         * Initialisation function for this module, just sets up some variables and sets up the
         * event listeners once the recaptcha library is ready.
         */
        initialize: function() {
            self = this;

            // setup the recaptcha context
            self.context = window.contacts_recaptcha.load(self.options.key, self.options.action);
            if (self.context) {
                // add a callback on the form's submission if the context is created, if it isn't we
                // don't need to hijack the submit functionality on the form and can just let it go
                // through as normal
                self.el.on('submit', self.onSubmit);
            }
        },

        /**
         * Called when the form is submitted. Note that this callback is only attached if a
         * recaptcha context is created, otherwise the default form submit function is used.
         */
        onSubmit: function(event) {
            // stop the form going through
            event.preventDefault();

            // add the token to the form and then submit it when ready
            self.context.addToken(self.el).then(function(token) {
                // remove the listener we added so that we don't create an infinite loop
                self.el.off('submit', self.onSubmit);
                // submit the form as normal
                self.el.submit();
            });
        },
    };
});
