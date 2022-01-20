from flask import Blueprint
import ckan.lib.base as base
import ckanext.gov_theme.views as views

gov_blueprint = Blueprint(u'gov_theme', __name__)


@gov_blueprint.route('/terms')
def terms():
    return base.render('home/terms.html')


@gov_blueprint.route('/dataset/<id>/resource/<resource_id>/download/<filename>')
def download(id, resource_id, package_type='dataset', filename=None):
    return views.download(id, resource_id)


@gov_blueprint.route('/user/logged_in')
def logged_in():
    return views.logged_in()
