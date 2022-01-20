# !/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-contact
# Created by the Natural History Museum in London, UK

import logging
import socket
import re

from ckanext.contact import recaptcha
from ckanext.contact.interfaces import IContact

from ckan import logic
from ckan.lib import mailer
import ckanext.gov_theme.mailer as custom_mailer
from ckan.lib.navl.dictization_functions import unflatten
from ckan.plugins import PluginImplementations, toolkit
from ckantoolkit import _

SMALL_FIELD_MAX_LENGTH = 30
BIG_FIELD_MAX_LENGTH = 300
EMAIL_MIN_LENGTH = 6

log = logging.getLogger(__name__)


def validate(data_dict):
    '''
    Validates the given data and recaptcha if necessary.

    :param data_dict: the request params as a dict
    :return: a 3-tuple of errors, error summaries and a recaptcha error, in the event where no
             issues occur the return is ({}, {}, None)
    '''
    errors = {}
    error_summary = {}
    recaptcha_error = None

    # check the three fields we know about
    for field in (u'email', u'name', u'content'):
        value = data_dict.get(field, None)
        if value is None or value == u'':
            errors[field] = [u'Missing Value']
            error_summary[field] = u'Missing value'
        else:
            error =  eval(f'_validate_{field}_field(value)')
            if error:
                errors[field] = [error]
                error_summary[field] = error

    # only check the recaptcha if there are no errors
    if not errors:
        try:
            expected_action = toolkit.config.get(u'ckanext.contact.recaptcha_v3_action')
            # check the recaptcha value, this only does anything if recaptcha is setup
            recaptcha.check_recaptcha(data_dict.get(u'g-recaptcha-response', None),
                                      expected_action)
        except recaptcha.RecaptchaError as e:
            log.info(u'Recaptcha failed due to "{}"'.format(e))
            recaptcha_error = toolkit._(u'Recaptcha check failed, please try again.')

    return errors, error_summary, recaptcha_error


def submit():
    '''
    Take the data in the request params and send an email using them. If the data is invalid or
    a recaptcha is setup and it fails, don't send the email.

    :return: a dict of details
    '''
    # this variable holds the status of sending the email
    email_success = True

    # pull out the data from the request
    data_dict = logic.clean_dict(
        unflatten(logic.tuplize_dict(logic.parse_params(
            toolkit.request.values))))

    # validate the request params
    errors, error_summary, recaptcha_error = validate(data_dict)

    # if there are not errors and no recaptcha error, attempt to send the email
    if len(errors) == 0 and recaptcha_error is None:

        # Mail title by request type
        if data_dict.get(u'report_type', '') == 'general':
            report_mail_title = u'Contact US - General - Government Data'
        elif data_dict.get(u'report_type', '') == 'dataset_req':
            report_mail_title = u'Contact US - Dataset Request - Government Data'
        else:
            report_mail_title = u'Contact US - Report - Government Data'

        # general content
        body = u'{}\n\nSent by:\nName: {}\nEmail: {}\n'.format(data_dict[u'content'],
                                                               data_dict[u'name'],
                                                               data_dict[u'email'])

        # if report page was from resource page -adding resource data
        if data_dict.get('type','') == 'report_mail':
            report_mail_title = 'Report Broken Link - Government Data'
            body += '\n' + ('Dataset ID') + ': ' + data_dict[u'dataset_id']
            body += '\n' + ('Dataset Title') + ': ' + data_dict[u'dataset_title']
            body += '\n' + ('Dataset Author') + ': ' + data_dict[u'dataset_author']
            body += '\n' + ('Resource ID') + ': ' + data_dict[u'resource_id']
            body += '\n' + ('Resource Title') + ': ' + data_dict[u'resource_title']
            body += '\n' + ('Dataset Author') + ': ' + data_dict[u'dataset_author']
            body += '\n' + ('Organization') + ': ' + data_dict[u'organization_name']
            body += '\n' + ('Link to data') + ': ' + "{}/dataset/{}/resource/{}".format(toolkit.config.get('ckan.site_url', '//localhost:p5'),
                                                                                            data_dict[u'dataset_id'],
                                                                                          data_dict[u'resource_id'])
            body += '\n\n' + (u'Best Regards')
            body += '\n' + (u'Government Data Site')

        mail_dict = {
            u'recipient_email': toolkit.config.get(u'ckanext.contact.mail_to',
                                                   toolkit.config.get(u'email_to')),
            u'recipient_name': toolkit.config.get(u'ckanext.contact.recipient_name',
                                                  toolkit.config.get(u'ckan.site_title')),
            u'subject': report_mail_title,
            u'body': body,
            u'headers': {
                u'reply-to': data_dict[u'email']
                }
            }

        # allow other plugins to modify the mail_dict
        for plugin in PluginImplementations(IContact):
            plugin.mail_alter(mail_dict, data_dict)

        try:
            custom_mailer.mail_recipient(**mail_dict)
        except (mailer.MailerException, socket.error):
            email_success = False

    return {
        u'success': recaptcha_error is None and len(errors) == 0 and email_success,
        u'data': data_dict,
        u'errors': errors,
        u'error_summary': error_summary,
        u'recaptcha_error': recaptcha_error,
        }


def _validate_email_field(email):
    '''
    Validate the email field with expected regular expression

    :param email: the given email
    :type email: string
    :return: if the given data is not validate return string represent the error else return None.
    :rtype: string or None
    '''
    email_pattern = re.compile(r'^[\w|\.|\-]+@(?:[\w|\-]+\.)+[a-zA-Z]{2,6}$')
    invalid_message = 'Must contain the following symbols: @. and after the last . must have between 2-6 characters'
    return _validate_data(email, email_pattern, invalid_message, SMALL_FIELD_MAX_LENGTH, EMAIL_MIN_LENGTH)


def _validate_name_field(name):
    '''
    Validate the name field with expected regular expression

    :param name: the given name
    :type name: string
    :return: if the given data is not validate return string represent the error else return None.
    :rtype: string or None
    '''
    name_pattern = re.compile(r'[a-zA-Zא-ת\s\'\-]*$')
    invalid_message = 'Must be purely alphabetic characters and these symbols: -\''
    return _validate_data(name, name_pattern, invalid_message, SMALL_FIELD_MAX_LENGTH)


def _validate_content_field(content):
    '''
    Validate the content field with expected regular expression

    :param content: the given content
    :type content: string
    :return: if the given data is not validate return string represent the error else return None.
    :rtype: string or None
    '''
    content_pattern = re.compile(r'[a-zA-Zא-ת0-9\'\"\(\)\.\,\/\?\s]*$')
    invalid_message = "Must be purely alphanumeric characters and these symbols: '\"().,?\/"
    return _validate_data(content, content_pattern, invalid_message, BIG_FIELD_MAX_LENGTH)


def _validate_data(value, pattern, invalid_message, max_length, min_length=0):
    '''
    Return the given value if it's a valid data, otherwise raise Invalid message.
    If it's a valid data, the given value will be returned unmodified.
    :param value: The given data
    :type value: string
    :param pattern: The expected pattern to validate with
    :type pattern: Pattern[str]
    :param invalid_message: The message to raise if not match by the regular expression
    :type invalid_message: string
    :param max_length: The max length value can be
    :type max_length: int
    :param min_length: The min length value can be, default is zero
    :type min_length: int
    :return: if the given data is not validate return string represent the error else raise error.
    :rtype: string
    '''
    if len(value) < 1:
        return _('Please fill in this field')

    if len(value) < min_length:
        return _('Must be at least %s characters long') % min_length

    if len(value) > max_length:
        return _('Must be a maximum of %i characters long') % max_length

    if not pattern.match(value):
        return _(invalid_message)
