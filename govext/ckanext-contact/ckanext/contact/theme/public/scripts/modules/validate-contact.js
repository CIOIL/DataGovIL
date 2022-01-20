/* validate-contact
 *
 * This JavaScript module check if contact us form inputs are validated.
 * Should be attached to the form itself.
 *
 * Example:
 *
 *   <form data-module="validate-contact"> ... </form>
 *
 */
"use strict";

ckan.module('validate-contact', function ($) {
    return {

         /**
         * Initialisation function for this module, just sets up some variables and sets up the
         * event listeners.
         */
        initialize: function() {
          self = this;
          self.el.on("input", this._onInput);
        },

        /**
         * Called when the user enter input in the form.
         * Calls to the appropriate function according to the field name.
         * @private
         */
        _onInput: function(event) {
            const FIELDS = $(this).find("textarea, input").serializeArray();
            for (let field of FIELDS) {
                let element = document.getElementsByName(field.name)[0];
                let functionName = `_${field.name}Validate`
                element.type == 'input' ? self[functionName](element) : self[functionName](element, field.value)
            }
            event.preventDefault();
        },

         /**
         * Check validity for an email address field
         * @param element The element on which the setCustomValidity supposed to run.
         * @private
         */
        _emailValidate: function (element) {
            const  INVALID_MESSAGE = this._("Must contain the following symbols: @. and after the last ." +
                " must have between 2-6 characters");
            self._validate(element, INVALID_MESSAGE);
        },

         /**
         * Check validity for a name field
         * @param element The element on which the setCustomValidity supposed to run.
         * @private
         */
        _nameValidate: function (element) {
            const INVALID_MESSAGE = this._("Must be purely alphabetic characters and these symbols: -\'");
            self._validate(element, INVALID_MESSAGE);
        },

         /**
         * Check validity for a content field
         * @param element The element on which the setCustomValidity supposed to run.
         * @private
         */
        _contentValidate: function (element, value) {
            const INVALID_MESSAGE = this._("Must be purely alphanumeric characters and these symbols: '\"().,?\/");
            const PATTERN = /^[a-zA-Zא-ת0-9\'\"\(\)\.\,\/\?\s]+$/;
            if (! (PATTERN.test(value))) {
                element.setCustomValidity(this._(INVALID_MESSAGE));
                return
            }
            element.setCustomValidity("");
        },

         /**
         * Validates the given data.
         * @param element The element on which the setCustomValidity supposed to run.
         * @private
         */
        _validate: function (element, invalidMessage) {
            if (element.validity.patternMismatch) {
                element.setCustomValidity(this._(invalidMessage));
                return
            }
            element.setCustomValidity("");
        },
    };
});
