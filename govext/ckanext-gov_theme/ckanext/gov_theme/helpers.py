import re
import urllib, json
import requests
from ckan.common import _, request, c, config
import ckan.plugins.toolkit as toolkit
import ckan.lib.formatters as formatters
from ckan.lib.helpers import date_str_to_datetime
from markdown import markdown
from ckan.lib.helpers import literal, truncate

from six import text_type, string_types

import logging
log = logging.getLogger(__name__)

def get_config_value(key):
    try:
        value = config.get(key, '')
        return value
    except:
        return ''

def parseBoolString(theString = 'False'):
  return theString[0].upper()== 'T'

def is_back():
    try:
        value = parseBoolString(config.get('ckan.gov_theme.is_back', False))
        return value
    except:
        return False

def getTimeout():
    try:
        # return in milisec
        value = config.get('who.timeout')
        return value
    except:
        return 0

def api_usage_count(id):
    from sqlalchemy import create_engine
    from sqlalchemy.sql import text

    eng = create_engine(config.get('sqlalchemy.url'))
    con = eng.connect()

    sql = "SELECT api_count FROM resource_count WHERE id='" + id + "'"
    ret_val = 0
    try:
        result = con.execute(text(sql))

        if result.rowcount == 1:
            name = result.fetchone()
            ret_val = name._row[0]
            return ret_val
    except:
        print ("Api tracking table problem!!! Check for missing table resource_count ")

    con.close()
    return ret_val

def resource_download_count(id):
    from sqlalchemy import create_engine
    from sqlalchemy.sql import text

    eng = create_engine(config.get('sqlalchemy.url'))
    con = eng.connect()

    sql = "SELECT download_count FROM resource_count WHERE id='" + id + "'"
    ret_val = 0
    try:
        result = con.execute(text(sql))

        if result.rowcount == 1:
            name = result.fetchone()
            ret_val = name._row[0]
            return ret_val
    except:
        print ("Api tracking table problem!!! Check for missing table resource_count ")

    con.close()
    return ret_val

def get_datasets_count():
    q = c.q = request.params.get('q', u'')
    data_dict = {
        'q': q
    }
    query = toolkit.get_action('package_search')(None, data_dict)
    return query['count']

def get_resources_count(organization_id):
    '''Return organization resource count.'''
    from ckanext.gov_theme.action import _get_num_of_resources_for_package as resource_count
    return resource_count(organization_id)[0][0]

def get_organizations_count():
    q = c.q = request.params.get('q', '')

    data_dict_global_results = {
        'q': q
    }
    global_results = toolkit.get_action('organization_list')(None,
                                                data_dict_global_results)

    return len(global_results)

def gui_view_count(id):
    from sqlalchemy import create_engine
    from sqlalchemy.sql import text


    eng = create_engine(config.get('sqlalchemy.url'))
    con = eng.connect()

    sql = "SELECT view_count FROM resource_count WHERE id='" + id + "'"
    ret_val = 0
    try:
        result = con.execute(text(sql))

        if result.rowcount == 1:
            name = result.fetchone()
            ret_val = name._row[0]
            return ret_val
    except:
        print ("tracking_raw's problem!!! Check for missing table resource_count ")

    con.close()
    return ret_val

def tags_count():
    '''Return a sorted list of the groups with the most datasets.'''

    tags_translate = [ _('Transport'), _('Justice'), _('Energy Watter'), _('Environment'), _('Finance Economy'), _('Population'), _('Religion'),   _('Education Culture'),   _('Health Wellness'), _('Accommodation'), _('Tourism') ]

   #/api/action/package_search?fq=tags:"economy"
    tags_counter = []

   #Put the details into a dict.
    for num in range(1,11):
        homepage_tag_num = "homepage_tag"+str(num)
        homepage_tag = config.get(homepage_tag_num)
        homepage_tag_translate = _(homepage_tag)
        homepage_tag_translate.encode('utf-8')
        query = "tags:"+'"'+homepage_tag_translate+'"'
        dataset_dict = {
           'fq': query,
        }

        homepage_tag_icon_num = "homepage_tag_icon"+str(num)
        homepage_tag_icon = config.get(homepage_tag_icon_num)

        # Use the json module to dump the dictionary to a string for posting.
        data_string = urllib.parse.quote(json.dumps(dataset_dict))
  #      package_search_api = config.get('ckan.site_url')+'/api/3/action/package_search?fq='

 #       package_search_api_url = package_search_api + query
#        log.info("package search url: "+package_search_api_url)
        response = toolkit.get_action(u'package_search')({}, dataset_dict)
        #response = requests.get(package_search_api_url)

        # Use the json module to load CKAN's response into a dictionary.
        #response_dict = json.loads(response.text)
        tag_count = response['count']
        tags_counter.append(dict([('name', homepage_tag_translate), ('icon', homepage_tag_icon), ('count', tag_count)]))

    return tags_counter

def format_resource_items(items):

    ''' Take a resource item list and format nicely with blacklisting etc. '''
    blacklist = ['name', 'description', 'url', 'tracking_summary', 'format', 'position', 'is_local_resource',  'cache_url', 'can_be_previewed', 'hash',
                 'datastore_active', 'on_same_domain', 'mimetype', 'state', 'url_type', 'has_views', 'cache_last_updated', 'mimetype_inner', 'resource_type',
                 '_authentication_token', 'ckan_url', 'datastore_contains_all_records_of_source_file', 'ignore_hash', 'original_url', 'resource_id',
                 'set_url_type', 'task_created', 'package_id', 'id', 'revision_id']
    output = []
    additioanl_fields = ['reference_number', 'demarcation', 'Language', 'spatial_coverage', 'geodetic']
    # regular expressions for detecting types in strings
    reg_ex_datetime = '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d{6})?$'
    reg_ex_int = '^-?\d{1,}$'
    reg_ex_float = '^-?\d{1,}\.\d{1,}$'
    for key, value in items:
        if key in blacklist:
            continue

        # size is treated specially as we want to show in MiB etc
        if key == 'size':
            try:
                # in case of a url
                if value is None:
                    continue
                value = formatters.localised_filesize(int(value))

            except ValueError as e:

                # Sometimes values that can't be converted to ints can sneak
                # into the db. In this case, just leave them as they are.
                pass
        elif isinstance(value, string_types):
            try:
                # check if strings are actually datetime/number etc
                if re.search(reg_ex_datetime, value):
                    datetime_ = date_str_to_datetime(value)
                    value = formatters.localised_nice_date(datetime_)
                elif re.search(reg_ex_float, value):
                    value = formatters.localised_number(float(value))
                elif re.search(reg_ex_int, value) and key not in additioanl_fields:
                    value = formatters.localised_number(int(value))
            except ValueError as e:
                log.info(e.message)
                pass
        elif ((isinstance(value, int) or isinstance(value, float))
                and value not in (True, False)):
            try:
               value = formatters.localised_number(value)
            except ValueError as e:
               log.info(e.message)
               pass
        key = key.replace('_', ' ')
        output.append((key, value))
    return sorted(output, key=lambda x: x[0])


def govil_markdown_extract(package_id, text, extract_length=190):
    ''' return the plain text representation of markdown encoded text.  That
    is the texted without any html tags.  If extract_length is 0 then it
    will not be truncated.'''
    RE_MD_HTML_TAGS = re.compile('<[^><]*>')

    if not text:
        return ''
    plain = RE_MD_HTML_TAGS.sub('', markdown(text))
    if not extract_length or len(plain) < extract_length:
        return literal(plain)

    end_a_tag = '<a data-toggle="collapse"' + \
                  ' onclick="$(\'#short_pack_des_'+package_id+'\').hide()"' + \
                  ' href="#full_pack_des_' + package_id + '"' + \
                  ' role="button"'+ \
                  ' aria-expanded="false"'+ \
                  ' aria-controls="full_pack_des_' + package_id + '">...</a>'

    return literal(
        text_type(
            truncate(
                plain,
                length=extract_length,
                indicator=end_a_tag,
                whole_word=True
            )
        )
    )
