import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.gov_google_analytics.helpers as analytics_helpers
import ckanext.gov_google_analytics.actions as analytics_actions


class GovGoogleAnalyticsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic',
            'gov_google_analytics')

        # ITemplateHelpers

    def get_helpers(self):
        '''Register the get_organization_code function above as a template
        helper function.

        '''
        return {'get_analytics_code': analytics_helpers.get_current_analytics_code,
                'get_site_code': analytics_helpers.get_govil_gtm_code,
                'reset_analytics_code': analytics_helpers.reset_analytics_code}

        # IActions

    def get_actions(self):
        return {
            'datastore_search': analytics_actions.datastore_search
        }
