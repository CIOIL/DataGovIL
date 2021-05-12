import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

from ckanext.gov_redirects import blueprint


class GovRedirectsPlugin(plugins.SingletonPlugin):

    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IBlueprint)

    def get_blueprint(self):
        return blueprint.redirects_blueprint

    # IConfigurer
    def update_config(self, config_):
        pass
