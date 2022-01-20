from flask import send_file

from ckan.lib.base import abort
from ckan.lib.helpers import redirect_to
from ckan.lib.uploader import get_resource_uploader
import ckan.lib.helpers as h
from ckan.logic import get_action, NotFound, NotAuthorized
from ckan.common import _, g, request, config

from ckan.views.user import me, login
import ckan.model as model
from ckanext.gov_theme.action import resource_tracking


# ckan.views.resource.py extend
def download(id, resource_id):
    """
    Provides a direct download by either redirecting the user to the url
    stored or downloading an uploaded file directly.
    """
    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'auth_user_obj': g.userobj
    }

    try:
        rsc = get_action(u'resource_show')(context, {u'id': resource_id})

        # analytics section
        pack_dict = get_action('package_show')(context, {'id': id})
        import ckanext.gov_google_analytics.helpers as analytics_helpers
        analytics_helpers.update_analytics_code_by_organization(pack_dict['organization']['id'])
        analytics_helpers.send_analytic_event_server_side(
            u'{}~{}'.format(pack_dict.get('organization').get('title'), u'Resource_Download'),
            pack_dict.get('title'), rsc.get('name'))

        # update/insert resource download count
        resource_tracking(rsc, 'download')

    except (NotFound, NotAuthorized):
        return abort(404, _(u'Resource not found'))

    if rsc.get(u'url_type') == u'upload':
        upload = get_resource_uploader(rsc)
        filepath = upload.get_path(rsc[u'id'])
        resp = send_file(filepath)
        if rsc.get(u'mimetype'):
            resp.headers[u'Content-Type'] = rsc[u'mimetype']
        return resp

    elif u'url' not in rsc:
        return abort(404, _(u'No download is available'))
    return redirect_to(rsc[u'url'])


# ckan.views.user.py extend
def logged_in():
    # redirect if needed
    came_from = request.params.get('came_from', u'')
    if h.url_is_local(came_from):
        return h.redirect_to(str(came_from))

    if g.user:
        return me()
    else:
        if config.get('ckan.recaptcha.login.enabled', 'True') == 'True':
            err = _('Login failed. Bad username, password or captcha.')
        else:
            err = _(u'Login failed. Bad username or password.')
        h.flash_error(err)
        return login()
