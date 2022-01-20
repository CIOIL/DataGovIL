import ckan.plugins.toolkit as toolkit
import ckanext.gov_google_analytics.helpers as analytics_helpers
from ckanext.gov_theme.action import resource_tracking


@toolkit.side_effect_free
@toolkit.chained_action
@toolkit.auth_allow_anonymous_access
def datastore_search(original_action, context, data_dict):
    # if search done, than send analytics event
    try:
        # insure that analytics event sent once
        if context.get('api_version', None) is not None:
            if data_dict.pop('send_analytics_event', True):
                # get the resource metadata
                id_dict = {'id': data_dict.get('resource_id')}
                rsc = toolkit.get_action('resource_show')(context=None, data_dict=id_dict)

                # get the package metadata
                id_dict = {'id': rsc.get('package_id')}
                pack_dict = toolkit.get_action('package_show')(context=None, data_dict=id_dict)

                # update organization_id
                analytics_helpers.update_analytics_code_by_organization(pack_dict['organization']['id'])

                # send analytics event server side
                analytics_helpers.send_analytic_event_server_side(
                    u'{}~{}'.format(pack_dict.get('organization').get('title'), u'Api_Search'),
                    pack_dict.get('title'), rsc.get('name'))

                # update/insert resource api usage count
                resource_tracking(rsc, 'api')

    # analytics event send failed
    except Exception as err:
        pass

    finally:
        return original_action(context, data_dict)
