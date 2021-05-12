#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-contact
# Created by the Natural History Museum in London, UK

from ckan.plugins import interfaces


class IContact(interfaces.Interface):
    '''Hook into contact form'''

    def mail_alter(self, mail_dict, data_dict):
        '''Allow altering of email values
        For example, allow directing contact form dependent on form values

        :param data_dict: form values
        :param mail_dict: dictionary of mail values, used in mailer.mail_recipient
        :returns: altered mail_dict

        '''
        return mail_dict
