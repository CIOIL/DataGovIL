<img src=".github/nhm-logo.svg" align="left" width="150px" height="100px" hspace="40"/>

# ckanext-contact

[![Travis](https://img.shields.io/travis/NaturalHistoryMuseum/ckanext-contact/master.svg?style=flat-square)](https://travis-ci.org/NaturalHistoryMuseum/ckanext-contact)
[![Coveralls](https://img.shields.io/coveralls/github/NaturalHistoryMuseum/ckanext-contact/master.svg?style=flat-square)](https://coveralls.io/github/NaturalHistoryMuseum/ckanext-contact)
[![CKAN](https://img.shields.io/badge/ckan-2.9.0a-orange.svg?style=flat-square)](https://github.com/ckan/ckan)

_A CKAN extension for adding popup contact forms to pages._


# Overview

Borrows much of the contact form code from [ckanext-surrey](https://github.com/CityofSurrey/ckanext-surrey).

An example can be seen on the Natural History Museum's [Data Portal](https://data.nhm.ac.uk) when clicking "_Contact dataset curator._"

This extension now includes Google's [reCAPTCHA](https://www.google.com/recaptcha) for preventing spam submissions.


# Installation

Path variables used below:
- `$INSTALL_FOLDER` (i.e. where CKAN is installed), e.g. `/usr/lib/ckan/default`
- `$CONFIG_FILE`, e.g. `/etc/ckan/default/development.ini`

1. Clone the repository into the `src` folder:

  ```bash
  cd $INSTALL_FOLDER/src
  git clone https://github.com/NaturalHistoryMuseum/ckanext-contact.git
  ```

2. Activate the virtual env:

  ```bash
  . $INSTALL_FOLDER/bin/activate
  ```

3. Install the requirements from requirements.txt:

  ```bash
  cd $INSTALL_FOLDER/src/ckanext-contact
  pip install -r requirements.txt
  ```

4. Run setup.py:

  ```bash
  cd $INSTALL_FOLDER/src/ckanext-contact
  python setup.py develop
  ```

5. Add 'contact' to the list of plugins in your `$CONFIG_FILE`:

  ```ini
  ckan.plugins = ... contact
  ```


# Configuration

There are no settings that _must_ be provided in your .ini config file, but there are some options:

## Email

Name|Description|Default
--|--|--
`ckanext.contact.mail_to`|Email address to submit to|`email_to`
`ckanext.contact.recipient_name`|Name of the recipient|`ckan.site_title`
`ckanext.contact.subject`|Email subject for the submitted form|'Contact/Question from visitor'

## Recaptcha

Name|Description|Default
--|--|--
`ckanext.contact.recaptcha_v3_key`|API key for the reCAPTCHA service.|False (i.e. disabled)
`ckanext.contact.recaptcha_v3_secret`|API secret for the reCAPTCHA service.|False (i.e. disabled)
`ckanext.contact.recaptcha_v3_action`|`data-module-action` for the form/button|  


# Further Setup

To use reCAPTCHA, you must register a site with the Google [reCAPTCHA](https://www.google.com/recaptcha) service and add your API key and secret in the [configuration](#configuration).

# Usage

Add the following HTML where you want the contact button to appear:

```html+jinja
{% set params = {...} %}

<a class="btn btn-primary" data-module="modal-contact" data-module-template="{{ h.get_contact_form_template_url(params) }}" href="{{ h.url_for('contact.form', **params) }}" title="{{ _('Contact') }}">
    <i class="fas fa-envelope"></i>{{ link_text if link_text else _('CONTACT BUTTON TEXT') }}
</a>

{% resource 'ckanext-contact/main' %}
```

Where `params` is a dict with three entries: package_id, resource_id, record_id (all of which are optional).


# Testing

_Test coverage is currently extremely limited._

To run the tests, use nosetests inside your virtualenv. The `--nocapture` flag will allow you to see the debug statements.
```bash
nosetests --ckan --with-pylons=$TEST_CONFIG_FILE --where=$INSTALL_FOLDER/src/ckanext-contact --nologcapture --nocapture
```
