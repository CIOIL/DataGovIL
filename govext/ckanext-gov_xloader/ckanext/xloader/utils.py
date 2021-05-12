from ckan.common import _
import ckanext.xloader.helpers as xloader_helpers
import ckan.plugins as p
from ckan.common import config
import json


def resource_data(id, resource_id):

    if p.toolkit.request.method == "POST":
        try:
            p.toolkit.c.pkg_dict = p.toolkit.get_action("xloader_submit")(
                None, {"resource_id": resource_id}
            )
        except p.toolkit.ValidationError:
            pass

        return p.toolkit.redirect_to(
            "xloader.resource_data", id=id, resource_id=resource_id
        )

    try:
        p.toolkit.c.pkg_dict = p.toolkit.get_action("package_show")(None, {"id": id})
        p.toolkit.c.resource = p.toolkit.get_action("resource_show")(
            None, {"id": resource_id}
        )
    except (p.toolkit.ObjectNotFound, p.toolkit.NotAuthorized):
        return p.toolkit.abort(404, p.toolkit._("Resource not found"))

    try:
        xloader_status = p.toolkit.get_action("xloader_status")(
            None, {"resource_id": resource_id}
        )
    except p.toolkit.ObjectNotFound:
        xloader_status = {}
    except p.toolkit.NotAuthorized:
        return p.toolkit.abort(403, p.toolkit._("Not authorized to see this page"))

    return p.toolkit.render(
        "xloader/resource_data.html",
        extra_vars={
            'status': xloader_status,
            'resource': p.toolkit.c.resource,
            'pkg_dict': p.toolkit.c.pkg_dict,
            'xloader_status_key': p.toolkit.c.userobj.apikey,
            'xloader_status_refresh_interval':
                config.get('ckanext.xloader.xloader_status_refresh_interval', 1000),
            'xloader_last_updated_refresh_interval':
                config.get('ckanext.xloader.xloader_last_updated_refresh_interval', 30000),
            'xloader_upload_log_refresh_interval':
                config.get('ckanext.xloader.xloader_upload_log_refresh_interval', 1000)
        },
    )


def xloader_status(resource_id):
    try:
        xloader_status = p.toolkit.get_action('xloader_status')(
            None, {'resource_id': resource_id}
        )

    except p.toolkit.ObjectNotFound:
        xloader_status = {}
    except p.toolkit.NotAuthorized:
        p.toolkit.abort(403, _('Not authorized to see this page'))

    return json.dumps(
        {
            'translated_status': xloader_helpers.xloader_status_description(xloader_status),
            'status': xloader_status.get('status')
        }
    )
