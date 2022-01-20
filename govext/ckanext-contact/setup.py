#!/usr/bin/env python
# encoding: utf-8
#
# This file is part of ckanext-contact
# Created by the Natural History Museum in London, UK

from setuptools import find_packages, setup

__version__ = u'1.1.0-alpha'

with open(u'README.md', u'r') as f:
    __long_description__ = f.read()

setup(
    name=u'ckanext-contact',
    version=__version__,
    description=u'A CKAN extension for adding popup contact forms to pages.',
    long_description=__long_description__,
    classifiers=[
        u'Development Status :: 3 - Alpha',
        u'Framework :: Flask',
        u'Programming Language :: Python :: 2.7'
    ],
    keywords=keywords2',
    author=u'Natural History Museum',
    author_email=u'user@mail2',
    url=u'https://github.com/NaturalHistoryMuseum/ckanext-contact',
    license=u'GNU GPLv3',
    packages=find_packages(exclude=[u'tests']),
    namespace_packages=[u'ckanext', u'ckanext.contact'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'requests>=2.10.0',
        ],

    entry_points='''
        [ckan.plugins]
        contact=ckanext.contact.plugin:ContactPlugin
        [babel.extractors]
        ckan = ckan.lib.extract:extract_ckan
        ''',

    # If you are changing from the default layout of your extension, you may
    # have to change the message extractors, you can read more about babel
    # message extraction at
    # http://babel.pocoo.org/docs/messages/#extraction-method-mapping-and-configuration
    message_extractors={
        'ckanext': [
            ('**.py', 'python', None),
            ('**.js', 'javascript', None),
            ('**/templates/**.html', 'ckan', None),
        ],
    }
    )
