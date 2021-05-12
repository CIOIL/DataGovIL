# !/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-contact
# Created by the Natural History Museum in London, UK

import logging

from flask import Blueprint, jsonify

from ckan import logic
from ckan.plugins import toolkit
from ckan.lib.navl.dictization_functions import unflatten
from . import _helpers

log = logging.getLogger(__name__)

blueprint = Blueprint(name=u'contact', import_name=__name__, url_prefix='/contact')


def _context():
    return {
        u'user': toolkit.c.user or toolkit.c.author
        }


@blueprint.before_request
def before_request():
    '''
    This function runs before the request handler to setup a few things. We use it to set
    the
    context dict and the user has check access.

    :param action: the action the user is attempting to perform (i.e. the handler)
    :param env: the environment object
    '''

    try:
        toolkit.check_access(u'send_contact', _context())
    except toolkit.NotAuthorized:
        toolkit.abort(401, toolkit._(u'Not authorized to use contact form'))


@blueprint.route('', methods=['GET', 'POST'])
def form():
    '''
    Form based interaction, if called as a POST request the request params are used to send the
    email, if not then the form template is rendered.

    :return: a page, either the form page or the success page if the email was sent successfully
    '''
    # dict of context values for the template renderer
    extra_vars = {
        u'data': {},
        u'errors': {},
        u'error_summary': {},
        }

    # Contact form GET
    if toolkit.request.method == u'GET':
        # try and use logged in user values for default values
        try:
            extra_vars[u'data'][u'name'] = toolkit.c.userobj.fullname or toolkit.c.userobj.name
            extra_vars[u'data'][u'email'] = toolkit.c.userobj.email
        except AttributeError:
            extra_vars[u'data'][u'name'] = extra_vars[u'data'][u'email'] = None

    elif toolkit.request.method == u'POST':

        data_dict = logic.clean_dict(
            unflatten(logic.tuplize_dict(logic.parse_params(
                toolkit.request.values))))

        # Report form get
        if data_dict.get('type', '') == 'report':
            # try and use logged in user values for default values
            try:
                # resource parameters for report form
                extra_vars[u'data'][u'type'] = data_dict[u'type']
                extra_vars[u'data'][u'dataset_id'] = data_dict[u'dataset_id']
                extra_vars[u'data'][u'dataset_title'] = data_dict[u'dataset_title']
                extra_vars[u'data'][u'dataset_author'] = data_dict[u'dataset_author']
                extra_vars[u'data'][u'resource_id'] = data_dict[u'resource_id']
                extra_vars[u'data'][u'resource_title'] = data_dict[u'resource_title']
                extra_vars[u'data'][u'organization_name'] = data_dict[u'organization_name']

                extra_vars[u'data'][u'name'] = toolkit.c.userobj.fullname or toolkit.c.userobj.name
                extra_vars[u'data'][u'email'] = toolkit.c.userobj.email
            except AttributeError:
                extra_vars[u'data'][u'name'] = extra_vars[u'data'][u'email'] = None

        # Contact form post
        else:
            result = _helpers.submit()
            if result.get(u'success', False):
                return toolkit.render(u'contact/success.html')
            else:
                # the form page isn't setup to handle this error so we need to flash it here for it
                if result[u'recaptcha_error'] is not None:
                    toolkit.h.flash_error(result[u'recaptcha_error'])
                # note that this copies over an recaptcha error key/value present in the submit
                # result
                extra_vars.update(result)

    return toolkit.render(u'contact/form.html', extra_vars=extra_vars)


@blueprint.route('/ajax', methods=['POST'])
def ajax_submit():
    '''
    AJAX form submission.

    :return: json dumped data for the response
    '''
    return jsonify(_helpers.submit())
