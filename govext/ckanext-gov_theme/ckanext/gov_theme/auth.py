import ckan.logic as logic
import ckan.authz as authz
import ckan.logic.auth as logic_auth
from ckan.common import _

from ckan.logic.auth.create import _check_group_auth, _group_or_org_member_create
import ckan.logic.auth.update as _auth_update
import ckan.logic.auth.create as _auth_create
from ckan.logic.auth.get import group_show, package_show
from ckan.logic.auth import get_resource_object,get_group_object


# update
@logic.auth_allow_anonymous_access
def package_update(context, data_dict):
    user = context.get('user')
    package = logic_auth.get_package_object(context, data_dict)

    if package.owner_org:
        # if there is an owner org then we must have update_dataset
        # permission for that organization
        check1 = authz.has_user_permission_for_group_or_org(
            package.owner_org, user, 'update_dataset'
        )
    else:
        # If dataset is not owned then we can edit if config permissions allow
        if authz.auth_is_anon_user(context):
            check1 = all(authz.check_config_permission(p) for p in (
                'anon_create_dataset',
                'create_dataset_if_not_in_organization',
                'create_unowned_dataset',
                ))
        else:
            check1 = all(authz.check_config_permission(p) for p in (
                'create_dataset_if_not_in_organization',
                'create_unowned_dataset',
                )) or authz.has_user_permission_for_some_org(
                user, 'create_dataset')
    if not check1:
        return {'success': False,
                'msg': _('User %s not authorized to edit package %s') %
                        (str(user), package.id)}
    else:
        check2 = _check_group_auth(context, data_dict)
        if not check2:
            return {'success': False,
                    'msg': _('User %s not authorized to edit these groups') %
                            (str(user))}

    if authz.config.get('ckan.gov_theme.is_back'):
        return {'success': True}
    else:
        return {'success': False}

def package_resource_reorder(context, data_dict):
    ## the action function runs package update so no need to run it twice
    if authz.config.get('ckan.gov_theme.is_back'):
        return {'success': True}
    else:
        return {'success': False}

def resource_update(context, data_dict):
    model = context['model']
    user = context.get('user')
    resource = logic_auth.get_resource_object(context, data_dict)

    # check authentication against package
    pkg = model.Package.get(resource.package_id)
    if not pkg:
        raise logic.NotFound(
            _('No package found for this resource, cannot check auth.')
        )

    pkg_dict = {'id': pkg.id}
    authorized = authz.is_authorized('package_update', context, pkg_dict).get('success')

    if not authorized:
        return {'success': False,
                'msg': _('User %s not authorized to edit resource %s') %
                        (str(user), resource.id)}
    else:
        if authz.config.get('ckan.gov_theme.is_back'):
            return {'success': True}
        else:
            return {'success': False}

def resource_view_update(context, data_dict):
    if authz.config.get('ckan.gov_theme.is_back'):
        return resource_update(context, {'id': data_dict['resource_id']})
    else:
        return {'success': False}

def resource_view_reorder(context, data_dict):
    if authz.config.get('ckan.gov_theme.is_back'):
        return resource_update(context, {'id': data_dict['resource_id']})
    else:
        return {'success': False}

def package_relationship_update(context, data_dict):
    if authz.config.get('ckan.gov_theme.is_back'):
        return authz.is_authorized('package_relationship_create',
                                   context,
                                   data_dict)
    else:
        return {'success': False}

def group_update(context, data_dict):
    group = logic_auth.get_group_object(context, data_dict)
    user = context['user']
    authorized = authz.has_user_permission_for_group_or_org(group.id,
                                                                user,
                                                                'update')
    if not authorized:
        return {'success': False,
                'msg': _('User %s not authorized to edit group %s') %
                        (str(user), group.id)}
    else:
        if authz.config.get('ckan.gov_theme.is_back'):
            return {'success': True}
        else:
            return {'success': False}

def organization_update(context, data_dict):
    group = logic_auth.get_group_object(context, data_dict)
    user = context['user']
    authorized = authz.has_user_permission_for_group_or_org(
        group.id, user, 'update')
    if not authorized:
        return {'success': False,
                'msg': _('User %s not authorized to edit organization %s') %
                        (user, group.id)}
    else:
        if authz.config.get('ckan.gov_theme.is_back'):
            return {'success': True}
        else:
            return {'success': False}


@logic.auth_allow_anonymous_access
def user_update(context, data_dict):
    user = context['user']

    # FIXME: We shouldn't have to do a try ... except here, validation should
    # have ensured that the data_dict contains a valid user id before we get to
    # authorization.
    try:
        user_obj = logic_auth.get_user_object(context, data_dict)
    except logic.NotFound:
        return {'success': False, 'msg': _('User not found')}

    # If the user has a valid reset_key in the db, and that same reset key
    # has been posted in the data_dict, we allow the user to update
    # her account without using her password or API key.
    if user_obj.reset_key and 'reset_key' in data_dict:
        if user_obj.reset_key == data_dict['reset_key']:
            if authz.config.get('ckan.gov_theme.is_back'):
                return {'success': True}
            else:
                return {'success': False}

    if not user:
        return {'success': False,
                'msg': _('Have to be logged in to edit user')}

    if user == user_obj.name:
        # Allow users to update their own user accounts.
        if authz.config.get('ckan.gov_theme.is_back'):
            return {'success': True}
        else:
            return {'success': False}
    else:
        # Don't allow users to update other users' accounts.
        return {'success': False,
                'msg': _('User %s not authorized to edit user %s') %
                        (user, user_obj.id)}

def user_generate_apikey(context, data_dict):
    user = context['user']
    user_obj = logic_auth.get_user_object(context, data_dict)
    if user == user_obj.name:
        # Allow users to update only their own user accounts.
        if authz.config.get('ckan.gov_theme.is_back'):
            return {'success': True}
        else:
            return {'success': False}
    return {'success': False, 'msg': _('User {0} not authorized to update user'
            ' {1}'.format(user, user_obj.id))}

def dashboard_mark_activities_old(context, data_dict):
    if authz.config.get('ckan.gov_theme.is_back'):
        return authz.is_authorized('dashboard_activity_list',
                                   context,
                                   data_dict)
    else:
        return {'success': False}

def bulk_update_private(context, data_dict):
    org_id = data_dict.get('org_id')
    user = context['user']
    authorized = authz.has_user_permission_for_group_or_org(
        org_id, user, 'update')
    if not authorized:
        return {'success': False}
    if authz.config.get('ckan.gov_theme.is_back'):
        return {'success': True}
    else:
        return {'success': False}

def bulk_update_public(context, data_dict):
    org_id = data_dict.get('org_id')
    user = context['user']
    authorized = authz.has_user_permission_for_group_or_org(
        org_id, user, 'update')
    if not authorized:
        return {'success': False}
    if authz.config.get('ckan.gov_theme.is_back'):
        return {'success': True}
    else:
        return {'success': False}

def bulk_update_delete(context, data_dict):
    org_id = data_dict.get('org_id')
    user = context['user']
    authorized = authz.has_user_permission_for_group_or_org(
        org_id, user, 'update')
    if not authorized:
        return {'success': False}
    if authz.config.get('ckan.gov_theme.is_back'):
        return {'success': True}
    else:
        return {'success': False}

# endof update


# create
@logic.auth_allow_anonymous_access
def package_create(context, data_dict=None):
    user = context['user']

    if authz.auth_is_anon_user(context):
        check1 = all(authz.check_config_permission(p) for p in (
            'anon_create_dataset',
            'create_dataset_if_not_in_organization',
            'create_unowned_dataset',
            ))
    else:
        check1 = all(authz.check_config_permission(p) for p in (
            'create_dataset_if_not_in_organization',
            'create_unowned_dataset',
            )) or authz.has_user_permission_for_some_org(
            user, 'create_dataset')

    if not check1:
        return {'success': False, 'msg': _('User %s not authorized to create packages') % user}

    check2 = _check_group_auth(context,data_dict)
    if not check2:
        return {'success': False, 'msg': _('User %s not authorized to edit these groups') % user}

    # If an organization is given are we able to add a dataset to it?
    data_dict = data_dict or {}
    org_id = data_dict.get('owner_org')
    if org_id and not authz.has_user_permission_for_group_or_org(
            org_id, user, 'create_dataset'):
        return {'success': False, 'msg': _('User %s not authorized to add dataset to this organization') % user}

    if authz.config.get('ckan.gov_theme.is_back'):
        return {'success': True}
    else:
        return {'success': False}



def resource_create(context, data_dict):
    model = context['model']
    user = context.get('user')

    package_id = data_dict.get('package_id')
    if not package_id and data_dict.get('id'):
        # This can happen when auth is deferred, eg from `resource_view_create`
        resource = logic_auth.get_resource_object(context, data_dict)
        package_id = resource.package_id

    if not package_id:
        raise logic.NotFound(
            _('No dataset id provided, cannot check auth.')
        )

    # check authentication against package
    pkg = model.Package.get(package_id)
    if not pkg:
        raise logic.NotFound(
            _('No package found for this resource, cannot check auth.')
        )

    pkg_dict = {'id': pkg.id}
    authorized = authz.is_authorized('package_update', context, pkg_dict).get('success')

    if not authorized:
        return {'success': False,
                'msg': _('User %s not authorized to create resources on dataset %s') %
                        (str(user), package_id)}
    else:
        if authz.config.get('ckan.gov_theme.is_back'):
            return {'success': True}
        else:
            return {'success': False}

def resource_view_create(context, data_dict):
    if authz.config.get('ckan.gov_theme.is_back'):
        return resource_create(context, {'id': data_dict['resource_id']})
    else:
        return {'success': False}

def resource_create_default_resource_views(context, data_dict):
    if authz.config.get('ckan.gov_theme.is_back'):
        return resource_create(context, {'id': data_dict['resource']['id']})
    else:
        return {'success': False}

def package_create_default_resource_views(context, data_dict):
    if authz.config.get('ckan.gov_theme.is_back'):
        return authz.is_authorized('package_update', context,data_dict['package'])
    else:
        return {'success': False}

def package_relationship_create(context, data_dict):
    user = context['user']

    id = data_dict['subject']
    id2 = data_dict['object']

    # If we can update each package we can see the relationships
    authorized1 = authz.is_authorized_boolean(
        'package_update', context, {'id': id})
    authorized2 = authz.is_authorized_boolean(
        'package_update', context, {'id': id2})

    if not authorized1 and authorized2:
        return {'success': False, 'msg': _('User %s not authorized to edit these packages') % user}
    else:
        if authz.config.get('ckan.gov_theme.is_back'):
            return {'success': True}
        else:
            return {'success': False}

def group_create(context, data_dict=None):
    user = context['user']
    user = authz.get_user_id_for_username(user, allow_none=True)
    if user and authz.check_config_permission('user_create_groups'):
        if authz.config.get('ckan.gov_theme.is_back'):
            return {'success': True}
        else:
            return {'success': False}
    return {'success': False,
            'msg': _('User %s not authorized to create groups') % user}

def organization_create(context, data_dict=None):
    user = context['user']
    user = authz.get_user_id_for_username(user, allow_none=True)

    if user and authz.check_config_permission('user_create_organizations'):
        if authz.config.get('ckan.gov_theme.is_back'):
            return {'success': True}
        else:
            return {'success': False}
    return {'success': False,
            'msg': _('User %s not authorized to create organizations') % user}

def rating_create(context, data_dict):
    # No authz check in the logic function
    if authz.config.get('ckan.gov_theme.is_back'):
        return {'success': True}
    else:
        return {'success': False}

@logic.auth_allow_anonymous_access
def user_create(context, data_dict=None):
    using_api = 'api_version' in context
    create_user_via_api = authz.check_config_permission(
            'create_user_via_api')
    create_user_via_web = authz.check_config_permission(
            'create_user_via_web')

    if using_api and not create_user_via_api:
        return {'success': False, 'msg': _('User {user} not authorized to '
            'create users via the API').format(user=context.get('user'))}
    if not using_api and not create_user_via_web:
        return {'success': False, 'msg': _('Not authorized to '
            'create users')}
    if authz.config.get('ckan.gov_theme.is_back'):
        return {'success': True}
    else:
        return {'success': False}

def user_invite(context, data_dict):
    data_dict['id'] = data_dict['group_id']

    if authz.config.get('ckan.gov_theme.is_back'):
        return group_member_create(context, data_dict)
    else:
        return {'success': False}

def organization_member_create(context, data_dict):
    if authz.config.get('ckan.gov_theme.is_back'):
        return _group_or_org_member_create(context, data_dict)
    else:
        return {'success': False}

def group_member_create(context, data_dict):
    if authz.config.get('ckan.gov_theme.is_back'):
        return _group_or_org_member_create(context, data_dict)
    else:
        return {'success': False}


def member_create(context, data_dict):
    group = logic_auth.get_group_object(context, data_dict)
    user = context['user']

    # User must be able to update the group to add a member to it
    permission = 'update'
    # However if the user is member of group then they can add/remove datasets
    if not group.is_organization and data_dict.get('object_type') == 'package':
        permission = 'manage_group'

    authorized = authz.has_user_permission_for_group_or_org(group.id,
                                                                user,
                                                                permission)
    if not authorized:
        return {'success': False,
                'msg': _('User %s not authorized to edit group %s') %
                        (str(user), group.id)}
    else:
        if authz.config.get('ckan.gov_theme.is_back'):
            return {'success': True}
        else:
            return {'success': False}

# endof create


# delete
def package_delete(context, data_dict):
    # Defer authorization for package_delete to package_update, as deletions
    # are essentially changing the state field
    if authz.config.get('ckan.gov_theme.is_back'):
        return _auth_update.package_update(context, data_dict)
    else:
        return {'success': False}

def resource_delete(context, data_dict):
    model = context['model']
    user = context.get('user')
    resource = get_resource_object(context, data_dict)

    # check authentication against package
    pkg = model.Package.get(resource.package_id)
    if not pkg:
        raise logic.NotFound(_('No package found for this resource, cannot check auth.'))

    pkg_dict = {'id': pkg.id}
    authorized = package_delete(context, pkg_dict).get('success')

    if not authorized:
        return {'success': False, 'msg': _('User %s not authorized to delete resource %s') % (user, resource.id)}
    else:
        if authz.config.get('ckan.gov_theme.is_back'):
            return {'success': True}
        else:
            return {'success': False}

def resource_view_delete(context, data_dict):

    if context.get('resource'):
        return resource_delete(context, {})
    if context.get('resource_view'):
        return resource_delete(context, {'id': context['resource_view'].resource_id})

    resource_id = data_dict.get('resource_id')
    if not resource_id:
        resource_view = context['model'].ResourceView.get(data_dict['id'])
        if not resource_view:
            raise logic.NotFound(_('Resource view not found, cannot check auth.'))
        resource_id = resource_view.resource_id

    if authz.config.get('ckan.gov_theme.is_back'):
        return resource_delete(context, {'id': resource_id})
    else:
        return {'success': False}



def package_relationship_delete(context, data_dict):
    user = context['user']
    relationship = context['relationship']

    # If you can create this relationship the you can also delete it
    authorized = authz.is_authorized_boolean('package_relationship_create', context, data_dict)
    if not authorized:
        return {'success': False, 'msg': _('User %s not authorized to delete relationship %s') % (user ,relationship.id)}
    else:
        if authz.config.get('ckan.gov_theme.is_back'):
            return {'success': True}
        else:
            return {'success': False}

def group_delete(context, data_dict):
    group = get_group_object(context, data_dict)
    user = context['user']
    if not authz.check_config_permission('user_delete_groups'):
        return {'success': False,
            'msg': _('User %s not authorized to delete groups') % user}
    authorized = authz.has_user_permission_for_group_or_org(
        group.id, user, 'delete')
    if not authorized:
        return {'success': False, 'msg': _('User %s not authorized to delete group %s') % (user ,group.id)}
    else:
        if authz.config.get('ckan.gov_theme.is_back'):
            return {'success': True}
        else:
            return {'success': False}

def organization_delete(context, data_dict):
    group = get_group_object(context, data_dict)
    user = context['user']
    if not authz.check_config_permission('user_delete_organizations'):
        return {'success': False,
            'msg': _('User %s not authorized to delete organizations') % user}
    authorized = authz.has_user_permission_for_group_or_org(
        group.id, user, 'delete')
    if not authorized:
        return {'success': False, 'msg': _('User %s not authorized to delete organization %s') % (user ,group.id)}
    else:
        if authz.config.get('ckan.gov_theme.is_back'):
            return {'success': True}
        else:
            return {'success': False}

def group_member_delete(context, data_dict):
    ## just return true as logic runs through member_delete
    if authz.config.get('ckan.gov_theme.is_back'):
        return {'success': True}
    else:
        return {'success': False}

def organization_member_delete(context, data_dict):
    ## just return true as logic runs through member_delete
    if authz.config.get('ckan.gov_theme.is_back'):
        return {'success': True}
    else:
        return {'success': False}

def member_delete(context, data_dict):
    if authz.config.get('ckan.gov_theme.is_back'):
        return _auth_create.member_create(context, data_dict)
    else:
        return {'success': False}

# endof delete


# get
@logic.auth_allow_anonymous_access
def revision_list(context, data_dict):
    # In our new model everyone can read the revison list
    if authz.config.get('ckan.gov_theme.is_back'):
        return {'success': True}
    else:
        return {'success': False}

@logic.auth_allow_anonymous_access
def group_revision_list(context, data_dict):
    if authz.config.get('ckan.gov_theme.is_back'):
        return group_show(context, data_dict)
    else:
        return {'success': False}

@logic.auth_allow_anonymous_access
def organization_revision_list(context, data_dict):
    if authz.config.get('ckan.gov_theme.is_back'):
        return group_show(context, data_dict)
    else:
        return {'success': False}

@logic.auth_allow_anonymous_access
def package_revision_list(context, data_dict):
    if authz.config.get('ckan.gov_theme.is_back'):
        return package_show(context, data_dict)
    else:
        return {'success': False}

@logic.auth_allow_anonymous_access
def user_list(context, data_dict):
    # Users list is visible by default
    if authz.config.get('ckan.gov_theme.is_back'):
        return {'success': True}
    else:
        return {'success': False}

@logic.auth_allow_anonymous_access
def revision_show(context, data_dict):
    # No authz check in the logic function
    if authz.config.get('ckan.gov_theme.is_back'):
        return {'success': True}
    else:
        return {'success': False}

@logic.auth_allow_anonymous_access
def user_show(context, data_dict):
    # By default, user details can be read by anyone, but some properties like
    # the API key are stripped at the action level if not not logged in.
    if authz.config.get('ckan.gov_theme.is_back'):
        return {'success': True}
    else:
        return {'success': False}

@logic.auth_allow_anonymous_access
def task_status_show(context, data_dict):
    if authz.config.get('ckan.gov_theme.is_back'):
        return {'success': True}
    else:
        return {'success': False}

@logic.auth_allow_anonymous_access
def resource_status_show(context, data_dict):
    if authz.config.get('ckan.gov_theme.is_back'):
        return {'success': True}
    else:
        return {'success': False}



