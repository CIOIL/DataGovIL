#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-contact
# Created by the Natural History Museum in London, UK

import functools
from logging import getLogger

from ckanext.contact.auth import send_contact
from ckanext.contact import routes

from ckan.plugins import SingletonPlugin, implements, interfaces, toolkit

log = getLogger(__name__)


class ContactPlugin(SingletonPlugin):
    '''CKAN Contact Extension'''
    implements(interfaces.IBlueprint, inherit=True)
    implements(interfaces.IConfigurer)
    implements(interfaces.IAuthFunctions)
    implements(interfaces.ITemplateHelpers, inherit=True)

    ## IConfigurer
    def update_config(self, config):
        '''

        :param config:

        '''
        toolkit.add_template_directory(config, u'theme/templates')
        toolkit.add_public_directory(config, u'theme/public')
        toolkit.add_resource(u'theme/public', u'ckanext-contact')

    ## IBlueprint
    def get_blueprint(self):
        return routes.blueprints

    ## IAuthFunctions
    def get_auth_functions(self):
        ''' '''
        return {
            u'send_contact': send_contact
            }

    ## ITemplateHelpers
    def get_helpers(self):
        ''' '''
        return {
            u'get_recaptcha_v3_action':
                functools.partial(toolkit.config.get, u'ckanext.contact.recaptcha_v3_action', None),
            u'get_recaptcha_v3_key':
                functools.partial(toolkit.config.get, u'ckanext.contact.recaptcha_v3_key', None)
            }
