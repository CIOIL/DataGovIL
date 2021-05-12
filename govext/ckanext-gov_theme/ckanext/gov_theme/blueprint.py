from flask import Blueprint
import ckan.lib.base as base

gov_blueprint = Blueprint(u'gov_theme', __name__)

@gov_blueprint.route('/terms')
def terms():
    return base.render('home/terms.html')
