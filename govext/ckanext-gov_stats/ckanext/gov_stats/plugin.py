# encoding: utf-8

from logging import getLogger

import ckan.plugins as p
from ckanext.gov_stats import blueprint

log = getLogger(__name__)


class GovStatsPlugin(p.SingletonPlugin):
    u'''Stats plugin.'''

    p.implements(p.IConfigurer)
    p.implements(p.IBlueprint)

    def get_blueprint(self):
        return blueprint.stats

    def update_config(self, config):
        p.toolkit.add_template_directory(config, u'templates')
        p.toolkit.add_public_directory(config, u'public')
        p.toolkit.add_resource(u'public/ckanext/stats', u'ckanext-gov_stats')
