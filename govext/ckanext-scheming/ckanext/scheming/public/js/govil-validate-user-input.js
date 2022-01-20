/* validate-user-input
 *
 * This JavaScript module check if user inputs are validated.
 * Should be attached to the form itself.
 *
 * Example:
 *
 *   <form data-module="validate-user-input"> ... </form>
 *
 */
"use strict";

ckan.module('validate-user-input', function ($) {
    return {
         /**
         * Initialisation function for this module, just sets up some variables and sets up the
         * event listeners.
         */
        initialize: function () {
            self = this;
            $(document).on('keyup change', this._onKeyUp);
        },

        /**
         * Called when a user releases a key.
         * @private
         */
        _onKeyUp: function(event) {
            const FIELDS = self.el.find("textarea, input, select").serializeArray();
            for (let field of FIELDS) {
                try {
                    let element = document.getElementsByName(field.name)[0];
                    self._createFuncName(element, field);
                }
                catch (e) {
                  continue
                }
            }
            event.preventDefault();
        },

         /**
         * Create string that represent the function name
         * and calls to the appropriate function.
         * @param element The element on which the action is performed
         * @param field The field that contains the name and value to check
         * @private
         */
        _createFuncName: function (element, field) {
           let functionName = "_";
           for (const [index, value] of field.name.split('_').entries()) {
              if (value == "extras") {
                  functionName += value;
              }
              else if (self.options.is_resource === "True" && field.name === "name") {
                  functionName += 'resourceName';
              }
              else {
                  functionName += ! index ? value : value.charAt(0).toUpperCase() + value.slice(1);
              }
           }
           this[`${functionName}Validate`](element, field.value);
        },

        /**
        * Validate the title field with expected regular expression and max length
        * This field can be left empty only if the name field has validated value.
        * If this field has validated value, check if the name file can be the same as this.
        * @param element The element on which the setCustomValidity supposed to run.
        * @param value The given value for the field.
        * @private
        */
        _titleValidate: function (element, value) {
            const PATTERN = /^[a-zA-Z\u0621-\u064Aא-ת0-9\s\_\-\(\)\"\،\,]+$/;
            const INVALID_MESSAGE = self._('Must be purely alphanumeric characters and these symbols: _-()",');
            if (/^$|[\u0621-\u064Aא-ת\s]+$/.test(value)) {

                // Find slug element value and style to check if the field need to be required
                const SLUG_VALUE = self.el.find('.slug-preview-value')[0].innerText;
                const SLUG_DISPLAY = self.el.find('.slug-preview')[0].style.display;

                if (SLUG_DISPLAY != "none" && (SLUG_VALUE === '<dataset>' || SLUG_VALUE === '<organization>')) {
                    element.setCustomValidity(self._("Please fill in name field."));
                    return
                }
                element.setCustomValidity("");
            }

            else {
                self._validate(element, value, PATTERN, INVALID_MESSAGE, 100);
            }
        },

        /**
        * Validate dataset and organization form name field with expected regular expression, max and min length.
        * @param element The element on which the setCustomValidity supposed to run.
        * @param value The given value for the field.
        * @private
        */
        _nameValidate: function (element, value) {
            const PATTERN = /^[a-zA-Z0-9_\-]+$/;
            const INVALID_MESSAGE = self._('Must be purely alphanumeric characters and these symbols: _-');
            self._validate(element, value, PATTERN, INVALID_MESSAGE, 60, 2);
        },

        /**
        * Validate resource form name field with expected regular expression and max length
        * @param element The element on which the setCustomValidity supposed to run.
        * @param value The given value for the field.
        * @private
        */
        _resourceNameValidate: function (element, value) {
            const PATTERN = /^$|[a-zA-Z\u0621-\u064Aא-ת0-9\s\"\_\/\(\)\،\,\-\.\:\&]+$/;
            const INVALID_MESSAGE = self._('Must be purely alphanumeric characters and these symbols: _-\"./(),');
            self._validate(element, value, PATTERN, INVALID_MESSAGE, 100);
        },

        /**
        * Validate the notes field with function- _contentInputValidate
        * @param element The element on which the setCustomValidity supposed to run.
        * @param value The given value for the field.
        * @private
        */
        _notesValidate: function (element, value) {
            self._contentValidate(element, value)
        },

        /**
        * Validate the remark field with function- _contentInputValidate
        * @param element The element on which the setCustomValidity supposed to run.
        * @param value The given value for the field.
        * @private
        */
        _remarkValidate: function (element, value) {
            self._contentValidate(element, value)
        },

        /**
        * Validate the tag field with expected regular expression, max and min length.
        * For each tag check if validate.
        * @param element The element on which the setCustomValidity supposed to run.
        * @param value The given value for the field.
        * @private
        */
        _tagStringValidate: function (element, value) {
            // find display input element for tags field
            const DISPLAY_TAG_INPUT = self.el.find('#s2id_autogen1')[0];

            if (value) {
                // find the existing tags
                const TAGS = self.el.find("a.select2-search-choice-close");
                // add an event listener for existing tags
                TAGS.on('click', function(event) {
                    if (! self.el.find("a.select2-search-choice-close").length) {
                        DISPLAY_TAG_INPUT.setCustomValidity("");
                        return
                    }
                    // find tags field current value
                    const VALUE = self.el.find("#field-tag_string")[0].value;
                    self._tagValidate(DISPLAY_TAG_INPUT, VALUE)
                    event.preventDefault();
                });


                const PATTERN = /[a-zA-Z\u0621-\u064Aא-ת0-9\'\s]+$/;
                const INVALID_MESSAGE = self._('Must be purely alphanumeric characters and these symbols: \'');

                for (let tag of value.split(',')) {
                    self._validate(DISPLAY_TAG_INPUT, tag, PATTERN, INVALID_MESSAGE, 20, 2);
                    if (DISPLAY_TAG_INPUT.validationMessage != "") {
                        return
                    }
                }
            }
        },

        /**
        * Validate the URL field with expected regular expression and max length
        * @param element The element on which the setCustomValidity supposed to run.
        * @param value The given value for the field.
        * @private
        */
        _urlValidate: function (element, value) {
            const PATTERN = /^$|[\w\.\-\:\/]+$/;
            const INVALID_MESSAGE = self._('Must be purely alphanumeric characters and these symbols: ./-:');
            self._validate(element, value, PATTERN, INVALID_MESSAGE, 100);
        },

        /**
        * Validate the Image URL field.
        * @param element The element on which the setCustomValidity supposed to run.
        * @param value The given value for the field.
        * @private
        */
        _imageUrlValidate: function (element, value) {
            return self._urlValidate(element, value);
        },

        /**
        * Validate the version field with expected regular expression and max length
        * @param element The element on which the setCustomValidity supposed to run.
        * @param value The given value for the field.
        * @private
        */
        _versionValidate: function (element, value) {
            const PATTERN = /^$|[0-9\.]+$/;
            const INVALID_MESSAGE = self._('Must be purely digit and these symbols: .');
            self._validate(element, value, PATTERN, INVALID_MESSAGE, 10);
        },

        /**
        * Validate the resource_ref_number field with expected regular expression and max length
        * @param element The element on which the setCustomValidity supposed to run.
        * @param value TThe given value for the field.
        * @private
        */
        _resourceRefNumberValidate: function (element, value) {
            const PATTERN = /^$|[0-9\-\/]+$/;
            const INVALID_MESSAGE = self._('Must be purely digit and these symbols: -/');
            self._validate(element, value, PATTERN, INVALID_MESSAGE, 10);
            self._gisFormatValidate(element, value);
        },

        /**
        * Validate the resource_desc_spatial_cover
        * @param element The element to check validity for
        * @param value TThe given value for the field.
        * @private
        */
        _resourceDescSpatialCoverValidate: function (element, value) {
            element.setCustomValidity("");
            self._gisFormatValidate(element, value);
        },

        /**
        * Validate the resource_coordinates field with expected regular expression and max length
        * @param element The element on which the setCustomValidity supposed to run.
        * @param value The given value for the field.
        * @private
        */
        _resourceCoordinatesValidate: function (element, value) {
            const PATTERN = /^$|[0-9\.]+$/;
            const INVALID_MESSAGE = self._('Must be purely digit and these symbols: .');
            self._validate(element, value, PATTERN, INVALID_MESSAGE, 15);
            self._gisFormatValidate(element, value);
        },

        /**
        * Validate the resource_geodetic_ref_sys field
        * @param element The element to check validity for
        * @param value TThe given value for the field.
        * @private
        */
        _resourceGeodeticRefSysValidate: function (element, value) {
            element.setCustomValidity("");
            self._gisFormatValidate(element, value);
        },

         /**
         * Validate the  author email address field.
         * @param element The element on which the setCustomValidity supposed to run.
         * @param value The given value for the field.
         * @private
         */
        _authorEmailValidate: function (element, value) {
            const MIN_LENGTH = 6;
            const PATTERN = /[\w\.\-\_]+@(?:[\w\-\_]+\.)+[a-zA-Z]{2,6}$/;
            self._emailValidate(element, value, PATTERN, MIN_LENGTH);
        },

         /**
         * Validate the mail box field.
         * @param element The element on which the setCustomValidity supposed to run.
         * @param value The given value for the field.
         * @private
         */
        _mailBoxValidate: function (element, value) {
            const PATTERN = /^$|[\w\.\-\_]+@(?:[\w\-\_]+\.)+[a-zA-Z]{2,6}$/;
            self._emailValidate(element, value, PATTERN);
        },


         /**
         * Validate the email fields with expected regular expression, max and min length
         * @param element The element on which the setCustomValidity supposed to run.
         * @param value The given value for the field.
         * @private
         */
        _emailValidate: function (element, value, pattern, minLength=0) {
            const INVALID_MESSAGE = self._('Must contain the following symbols: @. and after the last . must have between 2-6 characters');
            self._validate(element, value, pattern, INVALID_MESSAGE, 30, minLength);
        },

         /**
         * Validate the format field with expected regular expression and max length
         * @param element The element on which the setCustomValidity supposed to run.
         * @param value The given value for the field.
         * @private
         */
        _formatValidate: function (element, value) {
            const PATTERN = /^$|[a-zA-Z]+$/;
            const INVALID_MESSAGE = self._('Must be only alphabetic characters');
            // Find display input for format field to post an error message if need
            const DISPLAY_INPUT = self.el.find('#s2id_autogen1')[0];
            self._validate(DISPLAY_INPUT, value, PATTERN, INVALID_MESSAGE, 15);
        },

         /**
         * Validate the extras fields with expected regular expression and max length
         * @param element The element on which the setCustomValidity supposed to run.
         * @param value The given value for the field.
         * @private
         */
        _extrasValidate: function (element, value) {
          const PATTERN = /^[A-Z0-9-]+$/;
          const INVALID_MESSAGE = self._("Must be purely alphanumeric characters and these symbols: -");
          self._validate(element, value, PATTERN, INVALID_MESSAGE, 14);
        },

         /**
         * Validate the content fields with expected regular expression and max length
         * @param element The element on which the setCustomValidity supposed to run.
         * @param value The given value for the field.
         * @private
         */
        _contentValidate: function (element, value) {
            const PATTERN = /^$|^[a-zA-Z\u0621-\u064Aא-ת0-9\'\"\(\)\.\،\،\,\/\?\-\%\:\_\₪\s\\\@]+$/;
            const INVALID_MESSAGE = self._("Must be purely alphanumeric characters and these symbols: %%-_'\"().,?₪:\/\\");
            let maxLength;
            // Field 'notes' max length should be 600 for dataset page and 300 for the others
            if (self.el[0].attributes.id.value.includes('dataset') && element.id == 'field-notes') {
                // change max length temporarily to 2000 instead of 600
                maxLength = 2000;
            }
            else {
                maxLength = 300;
            }
            self._validate(element, value, PATTERN, INVALID_MESSAGE, maxLength);
        },

         /**
         * GIS formats validator.
         * GIS fields info required when using GIS formats - GeoJSON and SHP.
         * @param element The GIS field element.
         * @param value The given value for the field.
         * @private
         */
        _gisFormatValidate: function (element, value) {
            // Disable this function temporarily to enable resources with GIS format to add the required fields.
            // if (! value) {
            //     const FORMAT_VALUE = document.getElementsByName('format')[0].value;
            //     const GIS_FORMATS = ['GEOJSON', 'SHP'];
            //     if (GIS_FORMATS.includes(FORMAT_VALUE.toUpperCase())) {
            //         element.setCustomValidity(self._('This field is required when using GIS format'));
            //     }
            // }
        },

         /**
         * Return the given value if valid, otherwise set error message.
         * @param element The element on which the setCustomValidity run.
         * @param value The given value.
         * @param pattern The expected pattern to validate with
         * @param invalidMessage The error message to set if not match by the regular expression
         * @param maxLength The max length for the value
         * @param minLength The min length for the value
         * @private
         */
        _validate: function (element, value, pattern, invalidMessage, maxLength, minLength=0) {
          if (value.length < minLength) {
              element.setCustomValidity(self._("Must be at least %(num)d characters long", {num: minLength}));
          }
          else if (value.length > maxLength) {
              element.setCustomValidity(self._("Must be a maximum of %(num)d characters long", {num: maxLength}));
          }
          else if (! (pattern.test(value))) {
              element.setCustomValidity(invalidMessage);
          }
          else {
              element.setCustomValidity("");
          }
        },
    };
});
