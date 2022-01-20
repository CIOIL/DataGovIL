import json
import datetime
import pytz
import re
import logging
import six
from itertools import count

from ckan.common import config
from ckan.lib.navl.dictization_functions import Missing
import ckan.lib.helpers as h
from ckan.model.core import State
import ckanext.scheming.helpers as sh

from ckantoolkit import get_validator, UnknownValidator, missing, Invalid, _

from ckanext.scheming.errors import SchemingException

SMALL_FIELD_MAX_LENGTH = 10
REGULAR_FIELD_MAX_LENGTH = 100
log = logging.getLogger(__name__)
OneOf = get_validator('OneOf')
ignore_missing = get_validator('ignore_missing')
not_empty = get_validator('not_empty')


def scheming_validator(fn):
    """
    Decorate a validator that needs to have the scheming fields
    passed with this function. When generating navl validator lists
    the function decorated will be called passing the field
    and complete schema to produce the actual validator for each field.
    """
    fn.is_a_scheming_validator = True
    return fn


def user_validation(func):
    """
    Return original value if the user is listed in scheming.gov_theme.validation
    else, the value must pass successfully the validation functions before his returning.

    This decorator let us the opportunity to change the field input also to illegal values.
    """
    def wrapper(value, context):
        user = context['user']
        user_exclusion = config.get('scheming.gov_theme.validation', '')
        if user in user_exclusion.split(','):
            if not isinstance(value, six.string_types) or isinstance(value, Missing):
                log.error('Package and resource validation: does not match! TypeError')
                return ''
            return value
        return func(value, context)
    return wrapper


@scheming_validator
def scheming_choices(field, schema):
    """
    Require that one of the field choices values is passed.
    """
    if 'choices' in field:
        return OneOf([c['value'] for c in field['choices']])

    def validator(value):
        if value is missing or not value:
            return value
        choices = sh.scheming_field_choices(field)
        for c in choices:
            if value == c['value']:
                return value
        raise Invalid(_('unexpected choice "%s"') % value)

    return validator


@scheming_validator
def scheming_required(field, schema):
    """
    not_empty if field['required'] else ignore_missing
    """
    if field.get('required'):
        return not_empty
    return ignore_missing


@scheming_validator
def scheming_multiple_choice(field, schema):
    """
    Accept zero or more values from a list of choices and convert
    to a json list for storage:

    1. a list of strings, eg.:

       ["choice-a", "choice-b"]

    2. a single string for single item selection in form submissions:

       "choice-a"
    """
    static_choice_values = None
    if 'choices' in field:
        static_choice_order = [c['value'] for c in field['choices']]
        static_choice_values = set(static_choice_order)

    def validator(key, data, errors, context):
        # if there was an error before calling our validator
        # don't bother with our validation
        if errors[key]:
            return

        value = data[key]
        if value is not missing:
            if isinstance(value, six.string_types):
                value = [value]
            elif not isinstance(value, list):
                errors[key].append(_('expecting list of strings'))
                return
        else:
            value = []

        choice_values = static_choice_values
        if not choice_values:
            choice_order = [c['value'] for c in sh.scheming_field_choices(field)]
            choice_values = set(choice_order)

        selected = set()
        for element in value:
            if element in choice_values:
                selected.add(element)
                continue
            errors[key].append(_('unexpected choice "%s"') % element)

        if not errors[key]:
            data[key] = json.dumps([v for v in
                                    (static_choice_order if static_choice_values else choice_order)
                                    if v in selected])

            if field.get('required') and not selected:
                errors[key].append(_('Select at least one'))

    return validator


def validate_date_inputs(field, key, data, extras, errors, context):
    date_error = _('Date format incorrect')
    time_error = _('Time format incorrect')

    date = None

    def get_input(suffix):
        inpt = key[0] + '_' + suffix
        new_key = (inpt,) + tuple(x for x in key if x != key[0])
        value = extras.get(inpt)
        data[new_key] = value
        errors[new_key] = []

        if value:
            del extras[inpt]

        if field.get('required'):
            not_empty(new_key, data, errors, context)

        return (new_key, value)

    date_key, value = get_input('date')
    value_full = ''

    if value:
        try:
            value_full = value
            date = h.date_str_to_datetime(value)
        except (TypeError, ValueError) as e:
            errors[date_key].append(date_error)

    time_key, value = get_input('time')
    if value:
        if not value_full:
            errors[date_key].append(
                _('Date is required when a time is provided'))
        else:
            try:
                value_full += ' ' + value
                date = h.date_str_to_datetime(value_full)
            except (TypeError, ValueError) as e:
                errors[time_key].append(time_error)

    tz_key, value = get_input('tz')
    if value:
        if value not in pytz.all_timezones:
            errors[tz_key].append('Invalid timezone')
        else:
            if isinstance(date, datetime.datetime):
                date = pytz.timezone(value).localize(date)

    return date


@scheming_validator
def scheming_isodatetime(field, schema):
    def validator(key, data, errors, context):
        value = data[key]
        date = None

        if value:
            if isinstance(value, datetime.datetime):
                return value
            else:
                try:
                    date = h.date_str_to_datetime(value)
                except (TypeError, ValueError) as e:
                    raise Invalid(_('Date format incorrect'))
        else:
            extras = data.get(('__extras',))
            if not extras or (key[0] + '_date' not in extras and
                              key[0] + '_time' not in extras):
                if field.get('required'):
                    not_empty(key, data, errors, context)
            else:
                date = validate_date_inputs(
                    field, key, data, extras, errors, context)

        data[key] = date

    return validator


@scheming_validator
def scheming_isodatetime_tz(field, schema):
    def validator(key, data, errors, context):
        value = data[key]
        date = None

        if value:
            if isinstance(value, datetime.datetime):
                date = sh.scheming_datetime_to_UTC(value)
            else:
                try:
                    date = sh.date_tz_str_to_datetime(value)
                except (TypeError, ValueError) as e:
                    raise Invalid(_('Date format incorrect'))
        else:
            extras = data.get(('__extras',))
            if not extras or (key[0] + '_date' not in extras and
                              key[0] + '_time' not in extras):
                if field.get('required'):
                    not_empty(key, data, errors, context)
            else:
                date = validate_date_inputs(
                    field, key, data, extras, errors, context)
                if isinstance(date, datetime.datetime):
                    date = sh.scheming_datetime_to_UTC(date)

        data[key] = date

    return validator


def scheming_valid_json_object(value, context):
    """Store a JSON object as a serialized JSON string

    It accepts two types of inputs:
        1. A valid serialized JSON string (it must be an object or a list)
        2. An object that can be serialized to JSON

    """
    if not value:
        return
    elif isinstance(value, six.string_types):
        try:
            loaded = json.loads(value)

            if not isinstance(loaded, dict):
                raise Invalid(
                    _('Unsupported value for JSON field: {}').format(value)
                )

            return value
        except (ValueError, TypeError) as e:
            raise Invalid(_('Invalid JSON string: {}').format(e))

    elif isinstance(value, dict):
        try:
            return json.dumps(value)
        except (ValueError, TypeError) as e:
            raise Invalid(_('Invalid JSON object: {}').format(e))
    else:
        raise Invalid(
            _('Unsupported type for JSON field: {}').format(type(value))
        )

    return value


def scheming_load_json(value, context):
    if isinstance(value, six.string_types):
        try:
            return json.loads(value)
        except ValueError:
            return value
    return value


def scheming_multiple_choice_output(value):
    """
    return stored json as a proper list
    """
    if isinstance(value, list):
        return value
    try:
        return json.loads(value)
    except ValueError:
        return [value]


def validators_from_string(s, field, schema):
    """
    convert a schema validators string to a list of validators

    e.g. "if_empty_same_as(name) unicode" becomes:
    [if_empty_same_as("name"), unicode]
    """
    out = []
    parts = s.split()
    for p in parts:
        if '(' in p and p[-1] == ')':
            name, args = p.split('(', 1)
            args = args[:-1].split(',')  # trim trailing ')', break up
            v = get_validator_or_converter(name)(*args)
        else:
            v = get_validator_or_converter(p)
        if getattr(v, 'is_a_scheming_validator', False):
            v = v(field, schema)
        out.append(v)
    return out


def get_validator_or_converter(name):
    """
    Get a validator or converter by name
    """
    if name == 'unicode':
        return six.text_type
    try:
        v = get_validator(name)
        return v
    except UnknownValidator:
        pass
    raise SchemingException('validator/converter not found: %r' % name)


@user_validation
def govil_email_validator(value, context):
    '''
    Email field validator
    '''
    email_min_length = 6
    email_pattern = re.compile(r'^[\w\.\-\_]+@(?:[\w\_\-]+\.)+[a-zA-Z]{2,6}$')
    return _mail_validator(value, email_pattern, email_min_length)


@user_validation
def govil_mail_box_validator(value, context):
    '''
    Mail Box field validator
    '''
    mail_pattern = re.compile(r'^(?![\s\S])|[\w\.\-\_]+@(?:[\w\_\-]+\.)+[a-zA-Z]{2,6}$')
    return _mail_validator(value, mail_pattern)


@user_validation
def govil_title_validator(value, context):
    '''
    Title field validator with regular expression and invalid message
    '''
    title_pattern = re.compile(r'[a-zA-Z\u0621-\u064A0-9א-ת\s\_\-\(\)\"\،\,]*$')
    invalid_message = 'Must be purely alphanumeric characters and these symbols: _-()",'
    return _check_validation(value, title_pattern, invalid_message, REGULAR_FIELD_MAX_LENGTH)


@user_validation
def govil_resource_name_validator(value, context):
    '''
    Title field validator for resource with regular expression and invalid message
    '''
    resource_title_pattern = re.compile(r'[a-zA-Z\u0621-\u064A0-9א-ת\s\_\-\"\.\/\(\)\،\,\:\&]*$')
    invalid_message = 'Must be purely alphanumeric characters and these symbols: _-\"./(),'
    return _check_validation(value, resource_title_pattern, invalid_message, REGULAR_FIELD_MAX_LENGTH)


@user_validation
def govil_content_validator(value, context):
    '''
    Content fields validator
    '''
    content_max_length = 300
    return _content_validator(value, content_max_length)


@user_validation
def govil_description_validator(value, context):
    '''
    Description field validator
    '''
    # change max length temporarily to 2000 instead of 600
    description_max_length = 2000
    return _content_validator(value, description_max_length)


@user_validation
def govil_url_validator(value, context):
    '''
    URL field validator with regular expression and invalid message
    '''
    url_max_length = 100
    url_pattern = re.compile(r'[\w\.\/\-\:]*$')
    invalid_message = 'Must be purely alphanumeric characters and these symbols: ./-:'
    clean_url = value.split("/download/")

    if len(clean_url) > 1:
        value = clean_url[1]
    return _check_validation(value, url_pattern, invalid_message, url_max_length)


@user_validation
def govil_package_version_validator(value, context):
    '''
    Package version field validator with regular expression and invalid message
    '''
    package_version_pattern = re.compile(r'[0-9\.]*$')
    invalid_message = 'Must be purely digit and these symbols: .'
    return _check_validation(value, package_version_pattern, invalid_message, SMALL_FIELD_MAX_LENGTH)


@user_validation
def govil_ref_number_validator(value, context):
    '''
    Ref number field validator with regular expression and invalid message
    '''
    ref_number_pattern = re.compile(r'[0-9\-\/]*$')
    invalid_message = 'Must be purely digit and these symbols: -/'
    return _check_validation(value, ref_number_pattern, invalid_message, SMALL_FIELD_MAX_LENGTH)


@user_validation
def govil_coordinates_validator(value, context):
    '''
    Coordinates field validator with regular expression and invalid message
    '''
    coordinates_max_length = 15
    coordinates_pattern = re.compile(r'[0-9\.]*$')
    invalid_message = 'Must be purely digit and these symbols: .'
    return _check_validation(value, coordinates_pattern, invalid_message, coordinates_max_length)


@user_validation
def govil_format_validator(value, context):
    '''
    Format field validator with regular expression and invalid message
    '''
    format_max_length = 15
    format_pattern = re.compile(r'[a-zA-Z]*$')
    invalid_message = 'Must be only alphabetic characters'
    return _check_validation(value, format_pattern, invalid_message, format_max_length)


# ckan.logic.validators.py extend
@user_validation
def govil_name_validator(value, context):
    '''
    Name field validator with regular expression and invalid message
    Most schemas also have their own custom name validator function to apply
    custom validation rules after this function, for example a
    govil_package_name_validator() to check that no package with the given name
    already exists.
    '''
    if not isinstance(value, six.string_types):
        raise Invalid(_('Names must be strings'))

    # check basic textual rules
    if value in ['new', 'edit', 'search']:
        raise Invalid(_('That name cannot be used'))

    name_min_length = 2
    name_max_length = 60
    name_pattern = re.compile(r'[a-zA-Z0-9_\-]*$')
    invalid_message = "Must be purely alphanumeric characters and these symbols: _-"

    return _check_validation(value, name_pattern, invalid_message, name_max_length, name_min_length)


# ckan.logic.validators.py extend
def govil_dataset_name_validator(key, data, errors, context):
    '''
    Custom name validator function to check that no package with the given name already exists.
    '''
    model = context['model']
    session = context['session']
    package = context.get('package')

    query = session.query(model.Package.state).filter_by(name=data[key])
    if package:
        package_id = package.id
    else:
        package_id = data.get(key[:-1] + ('id',))
    if package_id and package_id is not missing:
        query = query.filter(model.Package.id != package_id)
    result = query.first()
    if result and result.state != State.DELETED:
        errors[key].append(_('That URL is already in use.'))


# ckan.logic.validators.py extend
@user_validation
def govil_tag_validator(value, context):
    '''
    Takes a list of tags that is a comma-separated string (in data[key])
    and parses tag names. They are also validated.
    '''
    if isinstance(value, six.string_types):
        tags = [tag.strip() for tag in value.split(',') if tag.strip()]
    else:
        tags = value

    tag_min_length = 2
    tag_max_length = 20
    tag_pattern = re.compile(r'[a-zA-Z\u0621-\u064Aא-ת0-9\'\s]*$')
    invalid_message = "Must be purely alphanumeric characters and these symbols: \'"

    for tag in tags:
        _check_validation(tag, tag_pattern, invalid_message, tag_max_length, tag_min_length)


def _content_validator(value, max_length):
    '''
    Content fields validator with regular expression and invalid message
    '''
    content_pattern = re.compile(r'[a-zA-Z\u0621-\u064Aא-ת0-9\'\"\(\)\.\،\,\/\?\-\%\:\_\₪\s\\\@]*$')
    invalid_message = "Must be purely alphanumeric characters and these symbols: %-_'\"().,?₪:/\\"
    return _check_validation(value, content_pattern, invalid_message, max_length)


def _mail_validator(value, pattern, min_length=0):
    '''
    Mail fields validator with regular expression and invalid message
    '''
    max_length = 30
    invalid_message = 'Must contain the following symbols: @. and after the last . must have between 2-6 characters'
    return _check_validation(value, pattern, invalid_message, max_length, min_length)


def _check_validation(value, pattern, invalid_message, max_length, min_length=0):
    '''
    Return the given value if it's a valid data, otherwise raise Invalid.
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
    :raises ckan.lib.navl.dictization_functions.Invalid: if ``value`` is not a valid value

    '''
    if not isinstance(value, six.string_types) or isinstance(value, Missing):
        log.error('Package and resource validation: does not match! TypeError')
        return ''

    if len(value) < min_length:
        raise Invalid(_('Must be at least %s characters long') % min_length)

    if len(value) > max_length:
        raise Invalid(_('Must be a maximum of %i characters long') % max_length)

    if not pattern.match(value):
        log.error('Package and resource validation: does not match! pattern: {pattern} value:{value} '
                  .format(pattern=pattern, value=value))
        raise Invalid(_(invalid_message))

    return value


def govil_gis_validator_format(key, data, errors, context):
    '''
    GIS formats validator.
    GIS fields info required when using GIS formats - GeoJSON and SHP.
    Raise an invalid error if GIS formats were used and GIS fields info weren't given else return the value.
    :raises ckan.lib.navl.dictization_functions.Invalid: if ``value`` is not a valid value
    '''
    # Disable this function temporarily to enable resources with GIS format to add the required fields.
    pass
    # value = data[key]
    # res_format = data.get(key[:-1] + ('format',), '').upper()
    # GIS_FORMATS = ('GEOJSON', 'SHP')
    #
    # if not value and res_format in GIS_FORMATS:
    #     log.error(f'Resource validation: field {key} is required when using GIS format')
    #     raise Invalid(_('This field is required when using GIS format'))
    #
    # return value
