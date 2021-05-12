// define a closure for ckanext-contacts recaptcha functionality, but only if it hasn't been defined
window.contacts_recaptcha = window.contacts_recaptcha || (function() {

    /**
     * Constructor for a recaptcha context.
     *
     * Calling this constructor can start off the async loading of the recaptcha library from
     * Google. Promises are used to ensure that when addToken is called in the future the library
     * has been loaded - see addToken for details.
     *
     * @param key the recaptcha key
     * @param action the recaptcha action to use
     * @constructor
     */
    const RecaptchaContext = function(key, action) {
        let self = this;

        // setup some basic attributes
        self.key = key;
        self.action = action;

        // couple of promises for the script load and the grecaptcha ready check
        self.grecaptcha_load = $.Deferred();
        self.grecaptcha_ready = $.Deferred();

        // only load the grecaptcha script if necessary
        if (!window.grecaptcha) {
            $.getScript('https://www.google.com/recaptcha/api.js?render=' + key, function() {
                self.grecaptcha_load.resolve();
            });
        } else {
            self.grecaptcha_load.resolve();
        }

        // once the recaptcha script is loaded, resolve on ready
        self.grecaptcha_load.then(function() {
            grecaptcha.ready(function() {
                self.grecaptcha_ready.resolve();
            });
        });

        /**
         * Request a recaptcha token from Google and then add it onto the given form element.
         *
         * @param formElement the form element to add the token hidden input element to
         * @returns promise which when resolved provides the token
         */
        self.addToken = function(formElement) {
            let tokenPromise = $.Deferred();

            // once the load and ready promises have been resolved, we can start our work
            $.when(self.grecaptcha_load, self.grecaptcha_ready).then(function() {
                // create a promise for the async call to Google to get a recaptcha token
                let recaptchaPromise = grecaptcha.execute(self.key, {action: self.action});
                // add the token to the form when it's ready
                recaptchaPromise.then(function(token) {
                    self.addTokenToForm(formElement, token);
                });
                // and resolve the token we've returned to the caller, with the token
                recaptchaPromise.then(tokenPromise.resolve);
            });
            return tokenPromise;
        };

        /**
         * Called when we get the token back from Google and adds it in a hidden element to the
         * given form element. If there was already a token on the form then it is replaced, this is
         * essential to ensure we don't submit the same token to Google twice as this will be
         * rejected.
         *
         * @param formElement the form element to add the hidden token input to
         * @param token the recaptcha token
         */
        self.addTokenToForm = function(formElement, token) {
            let input = formElement.find('input[name=g-recaptcha-response]');
            if (input.length === 0) {
                // create an input element so that we can pass the token in the form submission
                input = $('<input type="hidden" name="g-recaptcha-response">');
                // add the input to the form
                formElement.prepend(input);
            }
            input.attr('value', token);
        };

        return self;
    };

    /**
     * Checks whether recaptcha is enabled or not based on whether the key and action passed are
     * valid. This check simply confirms that the two values are truthy and do not equal 'None'.
     * This comes from the get_recaptcha_v3_action and get_recaptcha_v3_key helpers which return
     * None if the config values aren't defined. Because these values then get stringified in the
     * jinja2 templates into html tag attributes they end up here in the javascript as the string
     * 'None'.
     *
     * @param key the key value
     * @param action the action value
     * @returns {boolean}
     */
    const isRecaptchaEnabled = function(key, action) {
        return key && action && key !== 'None' && action !== 'None';
    };

    /**
     * Creates a RecaptchaContext object and returns it if the key and action are valid.
     *
     * @param key
     * @param action
     * @returns {RecaptchaContext|boolean}
     */
    const load = function(key, action) {
        if (isRecaptchaEnabled(key, action)) {
            return new RecaptchaContext(key, action);
        } else {
            return false;
        }
    };

    // return the module interface
    return {
        load: load,
        isRecaptchaEnabled: isRecaptchaEnabled
    };
}());
