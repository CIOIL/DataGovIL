import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import ckan.lib.app_globals as g
from ckan.common import config
import logging
from universal_analytics import Tracker, HTTPRequest
import copy

GLOBAL_KEY_NAME = config.get('ckanext.custom_google_analytics.global_key_name', 'analytics_codes')
GOVIL_GTM_CODE = config.get('ckanext.custom_google_analytics.govil_gtm_code', 'GTM-K7LZ42H')
GOVIL_ANALYTICS_CODE = config.get('ckanext.custom_google_analytics.govil_analytics_code', 'UA-73172242-1')

log = logging.getLogger(__name__)

def get_organization_id_by_package(package_id):
    """ Get the organization id of package using package id

    :param package_id:
    :return: organization id or empty string if not found
    """
    log.info("Google Analytics: get package data from DB, package id : {}".format(package_id))
    try:
        data_dict = {'id': package_id}
        package_data = toolkit.get_action('package_show')(context=None, data_dict=data_dict)
    except logic.NotFound:
        log.error("Google Analytics: FAILED NOT FOUND get package data from DB, package id : {}".format(package_id))
    except logic.NotAuthorized:
        log.error("Google Analytics: FAILED NOT AUTH get package data from DB, package id : {}".format(package_id))
    else:
        if package_data is not None:
            organization_data = package_data.get('organization', None)
            if organization_data is not None:
                return organization_data.get('id', '')


def get_online_analytics_code(organization_id):
    """ Get analytic code from organization extra field
    The method retrieve the value from DB

    :param organization_id:
    :return: analytic code of the organization
    """
    log.info("Google Analytics: get organization data from DB, organization id : {}".format(organization_id))
    try:
        data_dict = {'id': organization_id,
                     'include_datasets': False,
                     'include_dataset_count': False,
                     'include_extras': True,
                     'include_users': False,
                     'include_groups': False,
                     'include_tags': False,
                     'include_followers': False}

        organization_data = toolkit.get_action('organization_show')(context=None, data_dict=data_dict)

    except logic.NotFound:
        log.error("Google Analytics: FAILED NOT FOUND get organization data from DB, organization id : {}".format(organization_id))
    except logic.NotAuthorized:
        log.error("Google Analytics: FAILED NOT AUTH get organization data from DB, organization id : {}".format(organization_id))
    else:
        if organization_data is not None:
            organization_data_extras = organization_data.get('extras', None)
            if organization_data_extras is not None:
                values = [x['value'] for x in organization_data['extras'] if 'organization_id' in x['key']]
                if len(values) > 0:
                    return values[0]

    return ''


def update_analytics_code_by_package_id(package_id):
    """ updating the current organization id and analytic code
    for specific package

    :param package_id: the id of the package belong to the organization
    :return: None
    """
    org_id = get_organization_id_by_package(package_id)
    update_analytics_code_by_organization(org_id)


def update_analytics_code_by_organization(organization_id, force_online=False):
    """ Analytic codes are saved in the app_globals in format of organization_id: analytic code
    dict. if it is the first time for the organization to get the analytic code than it
    retrieves the analytic code from the DB, otherwise it uses the old value from the app_global
    dictionary.

    :param organization_id:
    :param force_online: if set to true, get analytic code from DB and not using cache.
    :return: None
    """
    if hasattr(g.app_globals, GLOBAL_KEY_NAME):
        log.info("Google Analytics: get {} object from APP_GLOBALS".format(GLOBAL_KEY_NAME))
        analytics_obg = getattr(g.app_globals, GLOBAL_KEY_NAME)
        analytics_obg = copy.deepcopy(analytics_obg)

        # updating current organization analytic code
        if analytics_obg.get('curr_org_id') != organization_id:
            if organization_id != '':
                # checks if analytic code for this object was retrieved
                if force_online or organization_id not in analytics_obg.keys():
                    analytics_obg[organization_id] = get_online_analytics_code(organization_id)

                # updating current organization_id
                analytics_obg['curr_org_id'] = organization_id
                analytics_obg['curr_analytics_code'] = analytics_obg[organization_id]
            else:
                analytics_obg['curr_org_id'] = ''
                analytics_obg['curr_analytics_code'] = ''

            g.set_app_global(GLOBAL_KEY_NAME, analytics_obg)

    # init app globals with analytics object for the first time
    else:
        log.info("Google Analytics: init {} object".format(GLOBAL_KEY_NAME))
        online_ga_code = ''
        if organization_id != '':
            online_ga_code = get_online_analytics_code(organization_id)

        analytics_obg = {
            'curr_org_id': organization_id,
            'curr_analytics_code': online_ga_code,
            organization_id: online_ga_code
        }
        g.set_app_global(GLOBAL_KEY_NAME, analytics_obg)


def get_current_analytics_code():
    ''' Get the current organization, after getting the value of the analytic code
    it resets.

    :return:
    '''
    if hasattr(g.app_globals, GLOBAL_KEY_NAME):
        analytics_obj = getattr(g.app_globals, GLOBAL_KEY_NAME)
        analytics_code = analytics_obj['curr_analytics_code']

        # analytics code is for one time use only because any organization
        # has it own code
        if analytics_code != '':
            reset_analytics_code()

        return analytics_code
    else:
        return ''


def reset_analytics_code():
    """ Some pages are not belong to any organization in example, HomePage.
    so we want to reset the analytic code for this page

    :return:
    """
    log.info("Google Analytics: reset organization id")
    update_analytics_code_by_organization('')


def get_govil_gtm_code():
    """ Beyond organization, main site also has gtm code.

    :return:
    """
    return GOVIL_GTM_CODE


def get_govil_analytics_code():
    """ Beyond organization, main site also has analytic code.

    :return:
    """
    return GOVIL_ANALYTICS_CODE

def send_analytic_event_server_side(event_category, event_action, event_label):
    """ Sending event to google analytics with server side code
        for the specific organization and for govil also

    :param event_category: The category of the event (Example: OrganizationTitle~Resource_Download)
    :param event_action: The action of the event (Example: DatasetTitle)
    :param event_label: The label of the event (Example: ResourceName)
    :return: None
    """

    # sending event to organization analytics
    with HTTPRequest() as http:
        tracker = Tracker(get_current_analytics_code(), http)
        tracker.send('event', event_category, event_action, event_label)

    # sending event to govil analytics
    with HTTPRequest() as http:
        tracker = Tracker(get_govil_analytics_code(), http)
        tracker.send('event', event_category, event_action, event_label)
