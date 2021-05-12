# encoding: utf-8

from flask import Blueprint

from ckan.plugins.toolkit import c, render
import ckanext.gov_stats.stats as stats_lib
import ckan.lib.base as base
from ckan.common import config

stats = Blueprint(u'stats', __name__)


@stats.route(u'/stats')
def index():
    if not config.get('ckan.gov_theme.is_back'):
        base.abort(404, 'not found')
    stats = stats_lib.Stats()
    extra_vars = {
        u'top_rated_packages': stats.top_rated_packages(),
        u'largest_groups': stats.largest_groups(),
        u'top_tags': stats.top_tags(),
        u'top_package_creators': stats.top_package_creators(),
        u'raw_packages_by_week': stats.raw_packages_by_week(),
        u'raw_new_datasets': stats.raw_new_datasets(),
        u'raw_all_package_revisions': stats.raw_all_package_revisions(),
        u'most_edited_packages': stats.most_edited_packages(),
        u'path_to_datasets_most_edited_file': stats.path_to_datasets_most_edited_file(),
        u'path_to_modified_resources_file': stats.path_to_modified_resources_file(),
        u'modified_resources': stats.modified_resources(),
        u'path_to_org_resources_file': stats.path_to_org_resources_file(),
        u'org_resources': stats.org_resources(),
        u'xloader_tasks': stats.xloader_tasks()
    }

    return render(u'ckanext/stats/index.html', extra_vars)
