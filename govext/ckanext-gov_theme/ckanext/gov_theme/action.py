import logging
from ckan.common import config
import ckan.model.misc as misc
import ckan.logic as logic
import ckan.lib.dictization
import ckan.logic.action
import ckan.logic.schema
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.lib.dictization.model_save as model_save
import ckan.lib.navl.dictization_functions
import ckan.lib.datapreview
from ckan import authz
from ckan.common import _
from ckan.logic.action.delete import _unfollow
import ckan.logic.action.create as _create
import ckan.logic.action.update as _update
import ckan.logic.action.get as _get
import ckan.logic.action.patch as _patch
import ckanext.gov_theme.email_notifications as custom_email_notifications
import ckanext.gov_theme.mailer as custom_mailer
import ckanext.gov_theme.schema as custom_schema

import ckan.lib.plugins as lib_plugins
import ckan.plugins as plugins

from ckanext.gov_theme import file_validators
#from ckanext.gov_theme import custom_uploader

log = logging.getLogger(__name__)

# Define some shortcuts
# Ensure they are module-private so that they don't get loaded as available
# actions in the action API.
_validate = ckan.lib.navl.dictization_functions.validate
_check_access = logic.check_access
_get_action = logic.get_action
ValidationError = logic.ValidationError
NotFound = logic.NotFound

# ckan.logic.create extend
def package_create(context, data_dict):
    '''Create a new dataset (package).

    You must be authorized to create new datasets. If you specify any groups
    for the new dataset, you must also be authorized to edit these groups.

    Plugins may change the parameters of this function depending on the value
    of the ``type`` parameter, see the
    :py:class:`~ckan.plugins.interfaces.IDatasetForm` plugin interface.

    :param name: the name of the new dataset, must be between 2 and 100
        characters long and contain only lowercase alphanumeric characters,
        ``-`` and ``_``, e.g. ``'warandpeace'``
    :type name: string
    :param title: the title of the dataset (optional, default: same as
        ``name``)
    :type title: string
    :param private: If ``True`` creates a private dataset
    :type private: bool
    :param author: the name of the dataset's author (optional)
    :type author: string
    :param author_email: the email address of the dataset's author (optional)
    :type author_email: string
    :param maintainer: the name of the dataset's maintainer (optional)
    :type maintainer: string
    :param maintainer_email: the email address of the dataset's maintainer
        (optional)
    :type maintainer_email: string
    :param license_id: the id of the dataset's license, see
        :py:func:`~ckan.logic.action.get.license_list` for available values
        (optional)
    :type license_id: license id string
    :param notes: a description of the dataset (optional)
    :type notes: string
    :param url: a URL for the dataset's source (optional)
    :type url: string
    :param version: (optional)
    :type version: string, no longer than 100 characters
    :param state: the current state of the dataset, e.g. ``'active'`` or
        ``'deleted'``, only active datasets show up in search results and
        other lists of datasets, this parameter will be ignored if you are not
        authorized to change the state of the dataset (optional, default:
        ``'active'``)
    :type state: string
    :param type: the type of the dataset (optional),
        :py:class:`~ckan.plugins.interfaces.IDatasetForm` plugins
        associate themselves with different dataset types and provide custom
        dataset handling behaviour for these types
    :type type: string
    :param resources: the dataset's resources, see
        :py:func:`resource_create` for the format of resource dictionaries
        (optional)
    :type resources: list of resource dictionaries
    :param tags: the dataset's tags, see :py:func:`tag_create` for the format
        of tag dictionaries (optional)
    :type tags: list of tag dictionaries
    :param extras: the dataset's extras (optional), extras are arbitrary
        (key: value) metadata items that can be added to datasets, each extra
        dictionary should have keys ``'key'`` (a string), ``'value'`` (a
        string)
    :type extras: list of dataset extra dictionaries
    :param relationships_as_object: see :py:func:`package_relationship_create`
        for the format of relationship dictionaries (optional)
    :type relationships_as_object: list of relationship dictionaries
    :param relationships_as_subject: see :py:func:`package_relationship_create`
        for the format of relationship dictionaries (optional)
    :type relationships_as_subject: list of relationship dictionaries
    :param groups: the groups to which the dataset belongs (optional), each
        group dictionary should have one or more of the following keys which
        identify an existing group:
        ``'id'`` (the id of the group, string), or ``'name'`` (the name of the
        group, string),  to see which groups exist
        call :py:func:`~ckan.logic.action.get.group_list`
    :type groups: list of dictionaries
    :param owner_org: the id of the dataset's owning organization, see
        :py:func:`~ckan.logic.action.get.organization_list` or
        :py:func:`~ckan.logic.action.get.organization_list_for_user` for
        available values (optional)
    :type owner_org: string

    :returns: the newly created dataset (unless 'return_id_only' is set to True
              in the context, in which case just the dataset id will
              be returned)
    :rtype: dictionary

    '''
    model = context['model']
    user = context['user']

    if not (data_dict is None):
        try:
            tagVal = data_dict['tags']
            if len(tagVal) == 0 :
                raise logic.ValidationError({
                    'Tags': [_("Missing value")]
                })
        except KeyError as e:
            pass
        try:
            authorEmail = data_dict['author_email']
            if not authorEmail:
                raise logic.ValidationError({
                    _('Author Email'): [_("Missing value")]
                })
        except KeyError as e:
            pass

            # Validation for the update frequency field
            #   Raise an error if no data
        try:
            freqUpdate = data_dict['freq']
            if not freqUpdate:
                raise logic.ValidationError({
                    ('Frequency'): [_("Missing value")]
                })
        except KeyError as e:
            pass

        try:
            methodUpdate = data_dict['updateOption']
            if not methodUpdate:
                raise logic.ValidationError({
                    ('Update'): [_("Missing value")]
                })
        except KeyError as e:
            pass

    if 'type' not in data_dict:
        package_plugin = lib_plugins.lookup_package_plugin()
        try:
            # use first type as default if user didn't provide type
            package_type = package_plugin.package_types()[0]
        except (AttributeError, IndexError):
            package_type = 'dataset'
            # in case a 'dataset' plugin was registered w/o fallback
            package_plugin = lib_plugins.lookup_package_plugin(package_type)
        data_dict['type'] = package_type
    else:
        package_plugin = lib_plugins.lookup_package_plugin(data_dict['type'])

    if 'schema' in context:
        schema = context['schema']
    else:
        schema = package_plugin.create_package_schema()

    _check_access('package_create', context, data_dict)

    if 'api_version' not in context:
        # check_data_dict() is deprecated. If the package_plugin has a
        # check_data_dict() we'll call it, if it doesn't have the method we'll
        # do nothing.
        check_data_dict = getattr(package_plugin, 'check_data_dict', None)
        if check_data_dict:
            try:
                check_data_dict(data_dict, schema)
            except TypeError:
                # Old plugins do not support passing the schema so we need
                # to ensure they still work
                package_plugin.check_data_dict(data_dict)

    data, errors = lib_plugins.plugin_validate(
        package_plugin, context, data_dict, schema, 'package_create')
    log.debug('package_create validate_errs=%r user=%s package=%s data=%r',
              errors, context.get('user'),
              data.get('name'), data_dict)

    if errors:
        model.Session.rollback()
        raise ValidationError(errors)

    rev = model.repo.new_revision()
    rev.author = user
    if 'message' in context:
        rev.message = context['message']
    else:
        rev.message = _(u'REST API: Create object %s') % data.get("name")

    if user:
        user_obj = model.User.by_name(user.decode('utf8'))
        if user_obj:
            data['creator_user_id'] = user_obj.id

    pkg = model_save.package_dict_save(data, context)

    # Needed to let extensions know the package and resources ids
    model.Session.flush()
    data['id'] = pkg.id
    if data.get('resources'):
        for index, resource in enumerate(data['resources']):
            resource['id'] = pkg.resources[index].id

    context_org_update = context.copy()
    context_org_update['ignore_auth'] = True
    context_org_update['defer_commit'] = True
    context_org_update['add_revision'] = False
    _get_action('package_owner_org_update')(context_org_update,
                                            {'id': pkg.id,
                                             'organization_id': pkg.owner_org})

    for item in plugins.PluginImplementations(plugins.IPackageController):
        item.create(pkg)

        item.after_create(context, data)

    # Make sure that a user provided schema is not used in create_views
    # and on package_show
    context.pop('schema', None)

    # Create default views for resources if necessary
    if data.get('resources'):
        logic.get_action('package_create_default_resource_views')(
            {'model': context['model'], 'user': context['user'],
             'ignore_auth': True},
            {'package': data})

    if not context.get('defer_commit'):
        model.repo.commit()

    # need to let rest api create
    context["package"] = pkg
    # this is added so that the rest controller can make a new location
    context["id"] = pkg.id
    log.debug('Created object %s' % pkg.name)

    return_id_only = context.get('return_id_only', False)

    output = context['id'] if return_id_only \
        else _get_action('package_show')(context, {'id': context['id']})

    return output

def resource_create(context, data_dict):
    '''Appends a new resource to a datasets list of resources.

    :param package_id: id of package that the resource should be added to.

    :type package_id: string
    :param url: url of resource
    :type url: string
    :param revision_id: (optional)
    :type revision_id: string
    :param description: (optional)
    :type description: string
    :param format: (optional)
    :type format: string
    :param hash: (optional)
    :type hash: string
    :param name: (optional)
    :type name: string
    :param resource_type: (optional)
    :type resource_type: string
    :param mimetype: (optional)
    :type mimetype: string
    :param mimetype_inner: (optional)
    :type mimetype_inner: string
    :param cache_url: (optional)
    :type cache_url: string
    :param size: (optional)
    :type size: int
    :param created: (optional)
    :type created: iso date string
    :param last_modified: (optional)
    :type last_modified: iso date string
    :param cache_last_updated: (optional)
    :type cache_last_updated: iso date string
    :param upload: (optional)
    :type upload: FieldStorage (optional) needs multipart/form-data

    :returns: the newly created resource
    :rtype: dictionary

    '''

    if data_dict['upload'] is not None:
        file_validators.check_file_extension(data_dict.get('url', ''))


    model = context['model']
    user = context['user']

    package_id = _create._get_or_bust(data_dict, 'package_id')
    if not data_dict.get('url'):
        data_dict['url'] = ''

    pkg_dict = _get_action('package_show')(
        dict(context, return_type='dict'),
        {'id': package_id})

    _check_access('resource_create', context, data_dict)

    for plugin in _create.plugins.PluginImplementations(_create.plugins.IResourceController):
        plugin.before_create(context, data_dict)

    if 'resources' not in pkg_dict:
        pkg_dict['resources'] = []

    upload = _create.uploader.get_resource_uploader(data_dict)
    #upload = custom_uploader.get_resource_uploader(data_dict)

    if 'mimetype' not in data_dict:
        if hasattr(upload, 'mimetype'):
            data_dict['mimetype'] = upload.mimetype

    if 'size' not in data_dict:
        if hasattr(upload, 'filesize'):
            data_dict['size'] = upload.filesize

    pkg_dict['resources'].append(data_dict)

    try:
        context['defer_commit'] = True
        context['use_cache'] = False
        _get_action('package_update')(context, pkg_dict)
        context.pop('defer_commit')
    except ValidationError as e:
        try:
            raise ValidationError(e.error_dict['resources'][-1])
        except (KeyError, IndexError):
            raise ValidationError(e.error_dict)

    # Get out resource_id resource from model as it will not appear in
    # package_show until after commit
    upload.upload(context['package'].resources[-1].id,
                  _create.uploader.get_max_resource_size())
    #upload.upload(context['package'].resources[-1].id, custom_uploader.get_max_resource_size())
    model.repo.commit()

    #  Run package show again to get out actual last_resource
    updated_pkg_dict = _get_action('package_show')(context, {'id': package_id})
    resource = updated_pkg_dict['resources'][-1]

    #  Add the default views to the new resource
    logic.get_action('resource_create_default_resource_views')(
        {'model': context['model'],
         'user': context['user'],
         'ignore_auth': True
         },
        {'resource': resource,
         'package': updated_pkg_dict
         })

    for plugin in _create.plugins.PluginImplementations(_create.plugins.IResourceController):
        plugin.after_create(context, resource)

    return resource

def user_invite(context, data_dict):
    '''Invite a new user.

    You must be authorized to create group members.

    :param email: the email of the user to be invited to the group
    :type email: string
    :param group_id: the id or name of the group
    :type group_id: string
    :param role: role of the user in the group. One of ``member``, ``editor``,
        or ``admin``
    :type role: string

    :returns: the newly created yser
    :rtype: dictionary
    '''
    _check_access('user_invite', context, data_dict)

    schema = context.get('schema',
                         ckan.logic.schema.default_user_invite_schema())
    data, errors = _validate(data_dict, schema, context)
    if errors:
        raise ValidationError(errors)

    name = _create._get_random_username_from_email(data['email'])
    password = str(_create.random.SystemRandom().random())
    data['name'] = name
    data['password'] = password
    data['state'] = ckan.model.State.PENDING
    user_dict = _get_action('user_create_within_org')(context, data)
    user = ckan.model.User.get(user_dict['id'])
    member_dict = {
        'username': user.id,
        'id': data['group_id'],
        'role': data['role']
    }
    _get_action('group_member_create')(context, member_dict)
    custom_mailer.send_invite(user)
    return model_dictize.user_dictize(user, context)

def user_create_within_org(context, data_dict):
    '''Create a new user.

    You must be authorized to create users.

    :param name: the name of the new user, a string between 2 and 100
        characters in length, containing only lowercase alphanumeric
        characters, ``-`` and ``_``
    :type name: string
    :param email: the email address for the new user
    :type email: string
    :param password: the password of the new user, a string of at least 4
        characters
    :type password: string
    :param id: the id of the new user (optional)
    :type id: string
    :param fullname: the full name of the new user (optional)
    :type fullname: string
    :param about: a description of the new user (optional)
    :type about: string
    :param openid: (optional)
    :type openid: string

    :returns: the newly created user
    :rtype: dictionary

    '''
    model = context['model']
    schema = context.get('schema') or custom_schema.default_user_invite_schema()
    session = context['session']

    _check_access('user_create', context, data_dict)

    data, errors = _validate(data_dict, schema, context)

    if errors:
        session.rollback()
        raise ValidationError(errors)

    # user schema prevents non-sysadmins from providing password_hash
    if 'password_hash' in data:
        data['_password'] = data.pop('password_hash')

    user = model_save.user_dict_save(data, context)

    # Flush the session to cause user.id to be initialised, because
    # activity_create() (below) needs it.
    session.flush()

    activity_create_context = {
        'model': model,
        'user': context['user'],
        'defer_commit': True,
        'ignore_auth': True,
        'session': session
    }
    activity_dict = {
        'user_id': user.id,
        'object_id': user.id,
        'activity_type': 'new user',
    }
    logic.get_action('activity_create')(activity_create_context, activity_dict)

    if not context.get('defer_commit'):
        model.repo.commit()

    # A new context is required for dictizing the newly constructed user in
    # order that all the new user's data is returned, in particular, the
    # api_key.
    #
    # The context is copied so as not to clobber the caller's context dict.
    user_dictize_context = context.copy()
    user_dictize_context['keep_apikey'] = True
    user_dictize_context['keep_email'] = True
    user_dict = model_dictize.user_dictize(user, user_dictize_context)

    context['user_obj'] = user
    context['id'] = user.id

    model.Dashboard.get(user.id)  # Create dashboard for user.

    log.debug('Created user {name}'.format(name=user.name))
    return user_dict

def follow_user(context, data_dict):
    '''Start following another user.

    You must provide your API key in the Authorization header.

    :param id: the id or name of the user to follow, e.g. ``'joeuser'``
    :type id: string

    :returns: a representation of the 'follower' relationship between yourself
        and the other user
    :rtype: dictionary

    '''
    if 'user' not in context:
        raise logic.NotAuthorized(_("You must be logged in to follow users"))

    model = context['model']
    session = context['session']

    userobj = model.User.get(context['user'])
    if not userobj:
        raise logic.NotAuthorized(_("You must be logged in to follow users"))

    schema = (context.get('schema')
              or ckan.logic.schema.default_follow_user_schema())

    validated_data_dict, errors = _validate(data_dict, schema, context)

    if errors:
        model.Session.rollback()
        raise ValidationError(errors)

    # Don't let a user follow herself.
    if userobj.id == validated_data_dict['id']:
        message = _('You cannot follow yourself')
        raise ValidationError({'message': message}, error_summary=message)

    # Don't let a user follow someone she is already following.
    if model.UserFollowingUser.is_following(userobj.id,
                                            validated_data_dict['id']):
        followeduserobj = model.User.get(validated_data_dict['id'])
        name = followeduserobj.display_name
        message = _('You are already following {0}').format(name)
        raise ValidationError({'message': message}, error_summary=message)

    follower = model_save.follower_dict_save(
        validated_data_dict, context, model.UserFollowingUser)

    if not context.get('defer_commit'):
        model.repo.commit()

    log.debug(u'User {follower} started following user {object}'.format(
        follower=follower.follower_id, object=follower.object_id))


    if config.get('ckan.gov_theme.is_back'):
        return model_dictize.user_following_user_dictize(follower, context)
    else:
        return 0

def follow_dataset(context, data_dict):
    '''Start following a dataset.

    You must provide your API key in the Authorization header.

    :param id: the id or name of the dataset to follow, e.g. ``'warandpeace'``
    :type id: string

    :returns: a representation of the 'follower' relationship between yourself
        and the dataset
    :rtype: dictionary

    '''

    if not 'user' in context:
        raise logic.NotAuthorized(
            _("You must be logged in to follow a dataset."))

    model = context['model']
    session = context['session']

    userobj = model.User.get(context['user'])
    if not userobj:
        raise logic.NotAuthorized(
            _("You must be logged in to follow a dataset."))

    schema = (context.get('schema')
              or ckan.logic.schema.default_follow_dataset_schema())

    validated_data_dict, errors = _validate(data_dict, schema, context)

    if errors:
        model.Session.rollback()
        raise ValidationError(errors)

    # Don't let a user follow a dataset she is already following.
    if model.UserFollowingDataset.is_following(userobj.id,
                                               validated_data_dict['id']):
        # FIXME really package model should have this logic and provide
        # 'display_name' like users and groups
        pkgobj = model.Package.get(validated_data_dict['id'])
        name = pkgobj.title or pkgobj.name or pkgobj.id
        message = _(
            'You are already following {0}').format(name)
        raise ValidationError({'message': message}, error_summary=message)

    follower = model_save.follower_dict_save(validated_data_dict, context,
                                             model.UserFollowingDataset)

    if not context.get('defer_commit'):
        model.repo.commit()

    log.debug(u'User {follower} started following dataset {object}'.format(
        follower=follower.follower_id, object=follower.object_id))

    if config.get('ckan.gov_theme.is_back'):
        return model_dictize.user_following_dataset_dictize(follower, context)
    else:
        return 0

def follow_group(context, data_dict):
    '''Start following a group.

    You must provide your API key in the Authorization header.

    :param id: the id or name of the group to follow, e.g. ``'roger'``
    :type id: string

    :returns: a representation of the 'follower' relationship between yourself
        and the group
    :rtype: dictionary

    '''
    if 'user' not in context:
        raise logic.NotAuthorized(
            _("You must be logged in to follow a group."))

    model = context['model']
    session = context['session']

    userobj = model.User.get(context['user'])
    if not userobj:
        raise logic.NotAuthorized(
            _("You must be logged in to follow a group."))

    schema = context.get('schema',
                         ckan.logic.schema.default_follow_group_schema())

    validated_data_dict, errors = _validate(data_dict, schema, context)

    if errors:
        model.Session.rollback()
        raise ValidationError(errors)

    # Don't let a user follow a group she is already following.
    if model.UserFollowingGroup.is_following(userobj.id,
                                             validated_data_dict['id']):
        groupobj = model.Group.get(validated_data_dict['id'])
        name = groupobj.display_name
        message = _(
            'You are already following {0}').format(name)
        raise ValidationError({'message': message}, error_summary=message)

    follower = model_save.follower_dict_save(validated_data_dict, context,
                                             model.UserFollowingGroup)

    if not context.get('defer_commit'):
        model.repo.commit()

    log.debug(u'User {follower} started following group {object}'.format(
        follower=follower.follower_id, object=follower.object_id))


    if config.get('ckan.gov_theme.is_back'):
        return model_dictize.user_following_group_dictize(follower, context)
    else:
        return 0
# end of ckan.logic.create extend


# ckan.logic.delete extend
def unfollow_user(context, data_dict):
    '''Stop following a user.
    :param id: the id or name of the user to stop following
    :type id: string
    '''
    if authz.config.get('cakn.gov_theme.is_back'):
        schema = context.get('schema') or (
                ckan.logic.schema.default_follow_user_schema())
        _unfollow(context, data_dict, schema, context['model'].UserFollowingUser)

def unfollow_dataset(context, data_dict):
    '''Stop following a dataset.

    :param id: the id or name of the dataset to stop following
    :type id: string

    '''
    if authz.config.get('cakn.gov_theme.is_back'):
        schema = context.get('schema') or (
            ckan.logic.schema.default_follow_dataset_schema())
        _unfollow(context, data_dict, schema,
                    context['model'].UserFollowingDataset)

def unfollow_group(context, data_dict):
    '''Stop following a group.

    :param id: the id or name of the group to stop following
    :type id: string

    '''
    if authz.config.get('cakn.gov_theme.is_back'):
        schema = context.get('schema',
                                ckan.logic.schema.default_follow_group_schema())
        _unfollow(context, data_dict, schema,
                    context['model'].UserFollowingGroup)
# end of ckan.logic.delete extend


# ckan.logic.update extend
def resource_update(context, data_dict):
    '''Update a resource.

    To update a resource you must be authorized to update the dataset that the
    resource belongs to.

    For further parameters see
    :py:func:`~ckan.logic.action.create.resource_create`.

    :param id: the id of the resource to update
    :type id: string

    :returns: the updated resource
    :rtype: string

    '''

    if data_dict['upload'] is not None:
        file_validators.check_file_extension(data_dict.get('url', ''))

    model = context['model']
    user = context['user']
    id = _update._get_or_bust(data_dict, "id")

    if not data_dict.get('url'):
        data_dict['url'] = ''

    resource = model.Resource.get(id)
    context["resource"] = resource
    try:
        old_resource_format = resource.format
    except:
        None

    if not resource:
        log.debug('Could not find resource %s', id)
        raise NotFound(_('Resource was not found.'))

    _check_access('resource_update', context, data_dict)
    del context["resource"]

    package_id = resource.package.id
    pkg_dict = _get_action('package_show')(dict(context, return_type='dict'),
        {'id': package_id})

    for n, p in enumerate(pkg_dict['resources']):
        if p['id'] == id:
            break
    else:
        log.error('Could not find resource %s after all', id)
        raise NotFound(_('Resource was not found.'))

    # Persist the datastore_active extra if already present and not provided
    if ('datastore_active' in resource.extras and
            'datastore_active' not in data_dict):
        data_dict['datastore_active'] = resource.extras['datastore_active']

    for plugin in _update.plugins.PluginImplementations(_update.plugins.IResourceController):
        plugin.before_update(context, pkg_dict['resources'][n], data_dict)

    upload = _update.uploader.get_resource_uploader(data_dict)
    #upload = custom_uploader.get_resource_uploader(data_dict)

    if 'mimetype' not in data_dict:
        if hasattr(upload, 'mimetype'):
            data_dict['mimetype'] = upload.mimetype

    if 'size' not in data_dict and 'url_type' in data_dict:
        if hasattr(upload, 'filesize'):
            data_dict['size'] = upload.filesize

    pkg_dict['resources'][n] = data_dict

    try:
        context['defer_commit'] = True
        context['use_cache'] = False
        updated_pkg_dict = _get_action('package_update')(context, pkg_dict)
        context.pop('defer_commit')
    except ValidationError as e:
        try:
            raise ValidationError(e.error_dict['resources'][-1])
        except (KeyError, IndexError):
            raise ValidationError(e.error_dict)

    upload.upload(id, _update.uploader.get_max_resource_size())
    #upload.upload(id, custom_uploader.get_max_resource_size())
    model.repo.commit()

    resource = _get_action('resource_show')(context, {'id': id})

    if old_resource_format != resource['format']:
        _get_action('resource_create_default_resource_views')(
            {'model': context['model'], 'user': context['user'],
             'ignore_auth': True},
            {'package': updated_pkg_dict,
             'resource': resource})

    for plugin in _update.plugins.PluginImplementations(_update.plugins.IResourceController):
        plugin.after_update(context, resource)

    return resource

@logic.auth_audit_exempt
def send_email_notifications(context, data_dict):
    '''Send any pending activity stream notification emails to users.

    You must provide a sysadmin's API key in the Authorization header of the
    request, or call this action from the command-line via a `paster post ...`
    command.

    '''
    # If paste.command_request is True then this function has been called
    # by a `paster post ...` command not a real HTTP request, so skip the
    # authorization.
    if not _update.request.environ.get('paste.command_request'):
        _check_access('send_email_notifications', context, data_dict)

    if not _update.converters.asbool(
            config.get('ckan.activity_streams_email_notifications')):
        raise ValidationError('ckan.activity_streams_email_notifications'
                              ' is not enabled in config')

        custom_email_notifications.get_and_send_notifications_for_all_users()

def term_translation_update_many(context, data_dict):
    '''Create or update many term translations at once.

    :param data: the term translation dictionaries to create or update,
        for the format of term translation dictionaries see
        :py:func:`~term_translation_update`
    :type data: list of dictionaries

    :returns: a dictionary with key ``'success'`` whose value is a string
        stating how many term translations were updated
    :rtype: string

    '''
    model = context['model']

    if not (data_dict.get('data') and isinstance(data_dict.get('data'), list)):
        raise ValidationError(
            {'error': 'term_translation_update_many needs to have a '
                      'list of dicts in field data'}
        )

    context['defer_commit'] = True

    action = _get_action('term_translation_update')
    for num, row in enumerate(data_dict['data']):
        action(context, row)

    model.Session.commit()


    if config.get('ckan.gov_theme.is_back'):
        return {'success': '%s rows updated' % (num + 1)}
    else:
        return {'success': False}

def task_status_update_many(context, data_dict):
    '''Update many task statuses at once.

    :param data: the task_status dictionaries to update, for the format of task
        status dictionaries see
        :py:func:`~task_status_update`
    :type data: list of dictionaries

    :returns: the updated task statuses
    :rtype: list of dictionaries

    '''
    results = []
    model = context['model']
    deferred = context.get('defer_commit')
    context['defer_commit'] = True
    for data in data_dict['data']:
        results.append(_get_action('task_status_update')(context, data))
    if not deferred:
        context.pop('defer_commit')
    if not context.get('defer_commit'):
        model.Session.commit()

    if config.get('ckan.gov_theme.is_back'):
        return {'results': results}
    else:
        return {'results': 0}

# end of ckan.logic.update extend


# ckan.logic.patch extend
def package_patch(context, data_dict):
    '''Patch a dataset (package).

    :param id: the id or name of the dataset
    :type id: string

    The difference between the update and patch methods is that the patch will
    perform an update of the provided parameters, while leaving all other
    parameters unchanged, whereas the update methods deletes all parameters
    not explicitly provided in the data_dict

    You must be authorized to edit the dataset and the groups that it belongs
    to.
    '''
    _check_access('package_patch', context, data_dict)

    show_context = {
        'model': context['model'],
        'session': context['session'],
        'user': context['user'],
        'auth_user_obj': context['auth_user_obj'],
        }

    package_dict = _get_action('package_show')(
        show_context,
        {'id': _patch._get_or_bust(data_dict, 'id')})

    patched = dict(package_dict)
    patched.update(data_dict)
    patched['id'] = package_dict['id']

    if config.get('ckan.gov_theme.is_back'):
        return _update.package_update(context, patched)
    else:
        return 0

def resource_patch(context, data_dict):
    '''Patch a resource

    :param id: the id of the resource
    :type id: string

    The difference between the update and patch methods is that the patch will
    perform an update of the provided parameters, while leaving all other
    parameters unchanged, whereas the update methods deletes all parameters
    not explicitly provided in the data_dict
    '''
    _check_access('resource_patch', context, data_dict)

    show_context = {
        'model': context['model'],
        'session': context['session'],
        'user': context['user'],
        'auth_user_obj': context['auth_user_obj'],
        }

    resource_dict = _get_action('resource_show')(
        show_context,
        {'id': _patch._get_or_bust(data_dict, 'id')})

    patched = dict(resource_dict)
    patched.update(data_dict)

    if config.get('ckan.gov_theme.is_back'):
        return _update.resource_update(context, patched)
    else:
        return 0

def group_patch(context, data_dict):
    '''Patch a group

    :param id: the id or name of the group
    :type id: string

    The difference between the update and patch methods is that the patch will
    perform an update of the provided parameters, while leaving all other
    parameters unchanged, whereas the update methods deletes all parameters
    not explicitly provided in the data_dict
    '''
    _check_access('group_patch', context, data_dict)

    show_context = {
        'model': context['model'],
        'session': context['session'],
        'user': context['user'],
        'auth_user_obj': context['auth_user_obj'],
        }

    group_dict = _get_action('group_show')(
        show_context,
        {'id': _patch._get_or_bust(data_dict, 'id')})

    patched = dict(group_dict)
    patched.pop('display_name', None)
    patched.update(data_dict)

    if config.get('ckan.gov_theme.is_back'):
        return _update.group_update(context, patched)
    else:
        return 0

def organization_patch(context, data_dict):
    '''Patch an organization

    :param id: the id or name of the organization
    :type id: string

    The difference between the update and patch methods is that the patch will
    perform an update of the provided parameters, while leaving all other
    parameters unchanged, whereas the update methods deletes all parameters
    not explicitly provided in the data_dict
    '''
    _check_access('organization_patch', context, data_dict)

    show_context = {
        'model': context['model'],
        'session': context['session'],
        'user': context['user'],
        'auth_user_obj': context['auth_user_obj'],
        }

    organization_dict = _get_action('organization_show')(
        show_context,
        {'id': _patch._get_or_bust(data_dict, 'id')})

    patched = dict(organization_dict)
    patched.pop('display_name', None)
    patched.update(data_dict)

    if config.get('ckan.gov_theme.is_back'):
        return _update.organization_update(context, patched)
    else:
        return 0

# end of ckan.logic.patch extend


# ckan.logic.get extend
def related_list(context, data_dict=None):
    '''Return a dataset's related items.

    :param id: id or name of the dataset (optional)
    :type id: string
    :param dataset: dataset dictionary of the dataset (optional)
    :type dataset: dictionary
    :param type_filter: the type of related item to show (optional,
      default: None, show all items)
    :type type_filter: string
    :param sort: the order to sort the related items in, possible values are
      'view_count_asc', 'view_count_desc', 'created_asc' or 'created_desc'
      (optional)
    :type sort: string
    :param featured: whether or not to restrict the results to only featured
      related items (optional, default: False)
    :type featured: bool

    :rtype: list of dictionaries

    '''
    model = context['model']
    dataset = data_dict.get('dataset', None)
    if not dataset:
        dataset = model.Package.get(data_dict.get('id'))
    _check_access('related_show', context, data_dict)
    related_list = []
    if not dataset:
        related_list = model.Session.query(model.Related)

        filter_on_type = data_dict.get('type_filter', None)
        if filter_on_type:
            related_list = related_list.filter(
                model.Related.type == filter_on_type)

        sort = data_dict.get('sort', None)
        if sort:
            sortables = {
                'view_count_asc': model.Related.view_count.asc,
                'view_count_desc': model.Related.view_count.desc,
                'created_asc': model.Related.created.asc,
                'created_desc': model.Related.created.desc,
            }
            s = sortables.get(sort, None)
            if s:
                related_list = related_list.order_by(s())

        if data_dict.get('featured', False):
            related_list = related_list.filter(model.Related.featured == 1)
        related_items = related_list.all()
        context['sorted'] = True
    else:
        relateds = model.Related.get_for_dataset(dataset, status='active')
        related_items = (r.related for r in relateds)
    related_list = model_dictize.related_list_dictize(
        related_items, context)
    if config.get('ckan.gov_theme.is_back'):
        return related_list
    else:
        return 0

def member_list(context, data_dict=None):
    '''Return the members of a group.

    The user must have permission to 'get' the group.

    :param id: the id or name of the group
    :type id: string
    :param object_type: restrict the members returned to those of a given type,
      e.g. ``'user'`` or ``'package'`` (optional, default: ``None``)
    :type object_type: string
    :param capacity: restrict the members returned to those with a given
      capacity, e.g. ``'member'``, ``'editor'``, ``'admin'``, ``'public'``,
      ``'private'`` (optional, default: ``None``)
    :type capacity: string

    :rtype: list of (id, type, capacity) tuples

    :raises: :class:`ckan.logic.NotFound`: if the group doesn't exist

    '''
    model = context['model']

    group = model.Group.get(_get._get_or_bust(data_dict, 'id'))
    if not group:
        raise NotFound

    obj_type = data_dict.get('object_type', None)
    capacity = data_dict.get('capacity', None)

    # User must be able to update the group to remove a member from it
    _check_access('group_show', context, data_dict)

    q = model.Session.query(model.Member).\
        filter(model.Member.group_id == group.id).\
        filter(model.Member.state == "active")

    if obj_type:
        q = q.filter(model.Member.table_name == obj_type)
    if capacity:
        q = q.filter(model.Member.capacity == capacity)

    trans = authz.roles_trans()

    def translated_capacity(capacity):
        try:
            return trans[capacity]
        except KeyError:
            return capacity

    if config.get('ckan.gov_theme.is_back'):
        return [(m.table_id, m.table_name, translated_capacity(m.capacity))
            for m in q.all()]
    else:
        return 0

def organization_list(context, data_dict):
    '''Return a list of the names of the site's organizations.

    :param order_by: the field to sort the list by, must be ``'name'`` or
      ``'packages'`` (optional, default: ``'name'``) Deprecated use sort.
    :type order_by: string
    :param sort: sorting of the search results.  Optional.  Default:
        "name asc" string of field name and sort-order. The allowed fields are
        'name', 'package_count' and 'title'
    :type sort: string
    :param limit: if given, the list of organizations will be broken into pages
        of at most ``limit`` organizations per page and only one page will be
        returned at a time (optional)
    :type limit: int
    :param offset: when ``limit`` is given, the offset to start
        returning organizations from
    :type offset: int
    :param organizations: a list of names of the groups to return,
        if given only groups whose names are in this list will be
        returned (optional)
    :type organizations: list of strings
    :param all_fields: return group dictionaries instead of just names. Only
        core fields are returned - get some more using the include_* options.
        Returning a list of packages is too expensive, so the `packages`
        property for each group is deprecated, but there is a count of the
        packages in the `package_count` property.
        (optional, default: ``False``)
    :type all_fields: boolean
    :param include_extras: if all_fields, include the organization extra fields
        (optional, default: ``False``)
    :type include_extras: boolean
    :param include_tags: if all_fields, include the organization tags
        (optional, default: ``False``)
    :type include_tags: boolean
    :param include_groups: if all_fields, include the organizations the
        organizations are in
        (optional, default: ``False``)
    :type all_fields: boolean
    :param include_users: if all_fields, include the organization users
        (optional, default: ``False``).
    :type include_users: boolean

    :rtype: list of strings

    '''
    _check_access('organization_list', context, data_dict)
    data_dict['groups'] = data_dict.pop('organizations', [])
    data_dict['type'] = 'organization'
    return _group_or_org_list(context, data_dict, is_org=True)

def _group_or_org_list(context, data_dict, is_org=False):
    model = context['model']
    api = context.get('api_version')
    groups = data_dict.get('groups')
    group_type = data_dict.get('type', 'group')
    ref_group_by = 'id' if api == 2 else 'name'
    pagination_dict = {}
    limit = data_dict.get('limit')
    if limit:
        pagination_dict['limit'] = data_dict['limit']
    offset = data_dict.get('offset')
    if offset:
        pagination_dict['offset'] = data_dict['offset']
    if pagination_dict:
        pagination_dict, errors = _validate(
            data_dict, logic.schema.default_pagination_schema(), context)
        if errors:
            raise ValidationError(errors)
    sort = data_dict.get('sort') or 'name'
    q = data_dict.get('q')

    all_fields = _get.asbool(data_dict.get('all_fields', None))

    # order_by deprecated in ckan 1.8
    # if it is supplied and sort isn't use order_by and raise a warning
    order_by = data_dict.get('order_by', '')
    if order_by:
        log.warn('`order_by` deprecated please use `sort`')
        if not data_dict.get('sort'):
            sort = order_by

    # if the sort is packages and no sort direction is supplied we want to do a
    # reverse sort to maintain compatibility.
    if sort.strip() in ('packages', 'package_count'):
        sort = 'package_count desc'

    sort_info = _get._unpick_search(sort,
                               allowed_fields=['name', 'packages',
                                               'package_count', 'title'],
                               total=1)

    if sort_info and sort_info[0][0] == 'package_count':
        query = model.Session.query(model.Group.id,
                                    model.Group.name,
                                    _get.sqlalchemy.func.count(model.Group.id))

        query = query.filter(model.Member.group_id == model.Group.id) \
                     .filter(model.Member.table_id == model.Package.id) \
                     .filter(model.Member.table_name == 'package') \
                     .filter(model.Package.state == 'active')
    else:
        query = model.Session.query(model.Group.id,
                                    model.Group.name)

    query = query.filter(model.Group.state == 'active')

    if groups:
        query = query.filter(model.Group.name.in_(groups))
    if q:
        q = u'%{0}%'.format(q)
        query = query.filter(_get._or_(
            model.Group.name.ilike(q),
            model.Group.title.ilike(q),
            model.Group.description.ilike(q),
        ))

    query = query.filter(model.Group.is_organization == is_org)
    if not is_org:
        query = query.filter(model.Group.type == group_type)
    if sort_info:
        sort_field = sort_info[0][0]
        sort_direction = sort_info[0][1]
        if sort_field == 'package_count':
            query = query.group_by(model.Group.id, model.Group.name)
            sort_model_field = _get.sqlalchemy.func.count(model.Group.id)
        elif sort_field == 'name':
            sort_model_field = model.Group.name
        elif sort_field == 'title':
            sort_model_field = model.Group.title

        if sort_direction == 'asc':
            query = query.order_by(_get.sqlalchemy.asc(sort_model_field))
        else:
            query = query.order_by(_get.sqlalchemy.desc(sort_model_field))

    if limit:
        query = query.limit(limit)
    if offset:
        query = query.offset(offset)

    groups = query.all()

    if all_fields:
        action = 'organization_show' if is_org else 'group_show'
        group_list = []
        for group in groups:
            data_dict['id'] = group.id
            for key in ('include_extras', 'include_tags', 'include_users',
                        'include_groups', 'include_followers'):
                if key not in data_dict:
                    data_dict[key] = False
            pack_count_result = _get_num_of_resources_for_package(group.id)
            pack_count = pack_count_result[0][0]
            group_list.append(_group_or_org_show(context, data_dict, pack_count, True))
    else:
        group_list = [getattr(group, ref_group_by) for group in groups]

    return group_list

def _get_num_of_resources_for_package(group_id):
    from sqlalchemy import create_engine
    from sqlalchemy.sql import text

    eng = create_engine(config.get('sqlalchemy.url'))
    con = eng.connect()

    rs = con.execute(text('SELECT name from "group"'))
    print (rs.fetchone())
    sql = 'SELECT COUNT(*) as num_of_resources FROM '
    sql = sql+ '(SELECT G.title as Office, P.name as DataSet, R.Name as resourceName, date(R.last_modified) as last_modified ,date(R.created) as created, R.id, G.name as name, R.url as url  FROM "group" as G INNER JOIN  "package" as P ON G.id = P.owner_org INNER JOIN resource as R ON P.id = R.package_id'
    sql = sql + " WHERE G.type = 'organization' AND G.state = 'active' AND P.state = 'active' AND R.state = 'active' "
    sql = sql+  " And G.id = '" + group_id +"' "
    sql = sql + " ORDER BY created desc,R.last_modified desc) n"

    result = con.execute(text(sql))
    names = []
    for row in result:
        names.append(row)

    con.close()

    return names

def _group_or_org_show(context, data_dict, resources_count, is_org=False):
    model = context['model']
    id = _get._get_or_bust(data_dict, 'id')

    group = model.Group.get(id)
    context['group'] = group

    include_datasets = _get.asbool(data_dict.get('include_datasets', False))
    packages_field = 'datasets' if include_datasets else 'dataset_count'

    include_tags = _get.asbool(data_dict.get('include_tags', True))
    include_users = _get.asbool(data_dict.get('include_users', True))
    include_groups = _get.asbool(data_dict.get('include_groups', True))
    include_extras = _get.asbool(data_dict.get('include_extras', True))
    include_followers = _get.asbool(data_dict.get('include_followers', True))

    if group is None:
        raise NotFound
    if is_org and not group.is_organization:
        raise NotFound
    if not is_org and group.is_organization:
        raise NotFound

    if is_org:
        _check_access('organization_show', context, data_dict)
    else:
        _check_access('group_show', context, data_dict)

    group_dict = model_dictize.group_dictize(group, context,
                                             packages_field=packages_field,
                                             include_tags=include_tags,
                                             include_extras=include_extras,
                                             include_groups=include_groups,
                                             include_users=include_users,)

    if is_org:
        plugin_type = _get.plugins.IOrganizationController
    else:
        plugin_type = _get.plugins.IGroupController

    for item in _get.plugins.PluginImplementations(plugin_type):
        item.read(group)

    group_plugin = _get.lib_plugins.lookup_group_plugin(group_dict['type'])
    try:
        schema = group_plugin.db_to_form_schema_options({
            'type': 'show',
            'api': 'api_version' in context,
            'context': context})
    except AttributeError:
        schema = group_plugin.db_to_form_schema()

    if include_followers:
        group_dict['num_followers'] = logic.get_action('group_follower_count')(
            {'model': model, 'session': model.Session},
            {'id': group_dict['id']})
    else:
        group_dict['num_followers'] = 0

    if schema is None:
        schema = logic.schema.default_show_group_schema()
    group_dict, errors = _get.lib_plugins.plugin_validate(
        group_plugin, context, group_dict, schema,
        'organization_show' if is_org else 'group_show')
    group_dict['resources_count'] = resources_count
    return group_dict

def group_package_show(context, data_dict):
    '''Return the datasets (packages) of a group.

    :param id: the id or name of the group
    :type id: string
    :param limit: the maximum number of datasets to return (optional)
    :type limit: int

    :rtype: list of dictionaries

    '''

    model = context['model']
    group_id = _get._get_or_bust(data_dict, 'id')

    limit = data_dict.get('limit')
    if limit:
        try:
            limit = int(data_dict.get('limit'))
            if limit < 0:
                raise logic.ValidationError('Limit must be a positive integer')
        except ValueError:
            raise logic.ValidationError('Limit must be a positive integer')

    group = model.Group.get(group_id)
    context['group'] = group
    if group is None:
        raise NotFound

    _check_access('group_show', context, data_dict)

    result = logic.get_action('package_search')(context, {
        'fq': 'groups:{0}'.format(group.name),
        'rows': limit,
    })


    if config.get('ckan.gov_theme.is_back'):
        return result['results']
    else:
        return 0

@logic.validate(logic.schema.default_resource_search_schema)
def resource_search(context, data_dict):
    '''
    Searches for resources satisfying a given search criteria.

    It returns a dictionary with 2 fields: ``count`` and ``results``.  The
    ``count`` field contains the total number of Resources found without the
    limit or query parameters having an effect.  The ``results`` field is a
    list of dictized Resource objects.

    The 'query' parameter is a required field.  It is a string of the form
    ``{field}:{term}`` or a list of strings, each of the same form.  Within
    each string, ``{field}`` is a field or extra field on the Resource domain
    object.

    If ``{field}`` is ``"hash"``, then an attempt is made to match the
    `{term}` as a *prefix* of the ``Resource.hash`` field.

    If ``{field}`` is an extra field, then an attempt is made to match against
    the extra fields stored against the Resource.

    Note: The search is limited to search against extra fields declared in
    the config setting ``ckan.extra_resource_fields``.

    Note: Due to a Resource's extra fields being stored as a json blob, the
    match is made against the json string representation.  As such, false
    positives may occur:

    If the search criteria is: ::

        query = "field1:term1"

    Then a json blob with the string representation of: ::

        {"field1": "foo", "field2": "term1"}

    will match the search criteria!  This is a known short-coming of this
    approach.

    All matches are made ignoring case; and apart from the ``"hash"`` field,
    a term matches if it is a substring of the field's value.

    Finally, when specifying more than one search criteria, the criteria are
    AND-ed together.

    The ``order`` parameter is used to control the ordering of the results.
    Currently only ordering one field is available, and in ascending order
    only.

    The ``fields`` parameter is deprecated as it is not compatible with calling
    this action with a GET request to the action API.

    The context may contain a flag, `search_query`, which if True will make
    this action behave as if being used by the internal search api.  ie - the
    results will not be dictized, and SearchErrors are thrown for bad search
    queries (rather than ValidationErrors).

    :param query: The search criteria.  See above for description.
    :type query: string or list of strings of the form ``{field}:{term1}``
    :param fields: Deprecated
    :type fields: dict of fields to search terms.
    :param order_by: A field on the Resource model that orders the results.
    :type order_by: string
    :param offset: Apply an offset to the query.
    :type offset: int
    :param limit: Apply a limit to the query.
    :type limit: int

    :returns:  A dictionary with a ``count`` field, and a ``results`` field.
    :rtype: dict

    '''
    model = context['model']

    # Allow either the `query` or `fields` parameter to be given, but not both.
    # Once `fields` parameter is dropped, this can be made simpler.
    # The result of all this gumpf is to populate the local `fields` variable
    # with mappings from field names to list of search terms, or a single
    # search-term string.
    query = data_dict.get('query')
    fields = data_dict.get('fields')

    if query is None and fields is None:
        raise ValidationError({'query': _('Missing value')})

    elif query is not None and fields is not None:
        raise ValidationError(
            {'fields': _('Do not specify if using "query" parameter')})

    elif query is not None:
        if isinstance(query, basestring):
            query = [query]
        try:
            fields = dict(pair.split(":", 1) for pair in query)
        except ValueError:
            raise ValidationError(
                {'query': _('Must be <field>:<value> pair(s)')})

    else:
        log.warning('Use of the "fields" parameter in resource_search is '
                    'deprecated.  Use the "query" parameter instead')

        # The legacy fields paramter splits string terms.
        # So maintain that behaviour
        split_terms = {}
        for field, terms in fields.items():
            if isinstance(terms, basestring):
                terms = terms.split()
            split_terms[field] = terms
        fields = split_terms

    order_by = data_dict.get('order_by')
    offset = data_dict.get('offset')
    limit = data_dict.get('limit')

    q = model.Session.query(model.Resource) \
         .join(model.Package) \
         .filter(model.Package.state == 'active') \
         .filter(model.Package.private == False) \
         .filter(model.Resource.state == 'active') \

    resource_fields = model.Resource.get_columns()
    for field, terms in fields.items():

        if isinstance(terms, basestring):
            terms = [terms]

        if field not in resource_fields:
            msg = _('Field "{field}" not recognised in resource_search.')\
                .format(field=field)

            # Running in the context of the internal search api.
            if context.get('search_query', False):
                raise _get.search.SearchError(msg)

            # Otherwise, assume we're in the context of an external api
            # and need to provide meaningful external error messages.
            raise ValidationError({'query': msg})

        for term in terms:

            # prevent pattern injection
            term = misc.escape_sql_like_special_characters(term)

            model_attr = getattr(model.Resource, field)

            # Treat the has field separately, see docstring.
            if field == 'hash':
                q = q.filter(model_attr.ilike(unicode(term) + '%'))

            # Resource extras are stored in a json blob.  So searching for
            # matching fields is a bit trickier.  See the docstring.
            elif field in model.Resource.get_extra_columns():
                model_attr = getattr(model.Resource, 'extras')

                like = _get._or_(
                    model_attr.ilike(
                        u'''%%"%s": "%%%s%%",%%''' % (field, term)),
                    model_attr.ilike(
                        u'''%%"%s": "%%%s%%"}''' % (field, term))
                )
                q = q.filter(like)

            # Just a regular field
            else:
                q = q.filter(model_attr.ilike('%' + unicode(term) + '%'))

    if order_by is not None:
        if hasattr(model.Resource, order_by):
            q = q.order_by(getattr(model.Resource, order_by))

    count = q.count()
    q = q.offset(offset)
    q = q.limit(limit)

    results = []
    for result in q:
        if isinstance(result, tuple) \
                and isinstance(result[0], model.DomainObject):
            # This is the case for order_by rank due to the add_column.
            results.append(result[0])
        else:
            results.append(result)

    # If run in the context of a search query, then don't dictize the results.
    if not context.get('search_query', False):
        results = model_dictize.resource_list_dictize(results, context)


    if config.get('ckan.gov_theme.is_back'):
        return {'count': count,'results': results}
    else:
        return {'count': 0,'results': 0}

def tag_search(context, data_dict):
    '''Return a list of tags whose names contain a given string.

    By default only free tags (tags that don't belong to any vocabulary) are
    searched. If the ``vocabulary_id`` argument is given then only tags
    belonging to that vocabulary will be searched instead.

    :param query: the string(s) to search for
    :type query: string or list of strings
    :param vocabulary_id: the id or name of the tag vocabulary to search in
      (optional)
    :type vocabulary_id: string
    :param fields: deprecated
    :type fields: dictionary
    :param limit: the maximum number of tags to return
    :type limit: int
    :param offset: when ``limit`` is given, the offset to start returning tags
        from
    :type offset: int

    :returns: A dictionary with the following keys:

      ``'count'``
        The number of tags in the result.

      ``'results'``
        The list of tags whose names contain the given string, a list of
        dictionaries.

    :rtype: dictionary

    '''
    tags, count = _get._tag_search(context, data_dict)

    if config.get('ckan.gov_theme.is_back'):
        return {'count': count,'results': [_get._table_dictize(tag, context) for tag in tags]}
    else:
        return {'count': 0,'results': 0}

def term_translation_show(context, data_dict):
    '''Return the translations for the given term(s) and language(s).

    :param terms: the terms to search for translations of, e.g. ``'Russian'``,
        ``'romantic novel'``
    :type terms: list of strings
    :param lang_codes: the language codes of the languages to search for
        translations into, e.g. ``'en'``, ``'de'`` (optional, default is to
        search for translations into any language)
    :type lang_codes: list of language code strings

    :rtype: a list of term translation dictionaries each with keys ``'term'``
        (the term searched for, in the source language), ``'term_translation'``
        (the translation of the term into the target language) and
        ``'lang_code'`` (the language code of the target language)
    '''
    model = context['model']

    trans_table = model.term_translation_table

    q = _get._select([trans_table])

    if 'terms' not in data_dict:
        raise ValidationError({'terms': 'terms not in data'})

    # This action accepts `terms` as either a list of strings, or a single
    # string.
    terms = _get._get_or_bust(data_dict, 'terms')
    if isinstance(terms, basestring):
        terms = [terms]
    if terms:
        q = q.where(trans_table.c.term.in_(terms))

    # This action accepts `lang_codes` as either a list of strings, or a single
    # string.
    if 'lang_codes' in data_dict:
        lang_codes = _get._get_or_bust(data_dict, 'lang_codes')
        if isinstance(lang_codes, basestring):
            lang_codes = [lang_codes]
        q = q.where(trans_table.c.lang_code.in_(lang_codes))

    conn = model.Session.connection()
    cursor = conn.execute(q)

    results = []

    for row in cursor:
        results.append(_get._table_dictize(row, context))

    if config.get('ckan.gov_theme.is_back'):
        return results
    else:
        return 0

def status_show(context, data_dict):
    '''Return a dictionary with information about the site's configuration.

    :rtype: dictionary

    '''
    if authz.config.get('ckan.gov_theme.is_back'):
        return {
        'site_title': config.get('ckan.site_title'),
        'site_description': config.get('ckan.site_description'),
        'site_url': config.get('ckan.site_url'),
        'ckan_version': ckan.__version__,
        'error_emails_to': config.get('email_to'),
        'locale_default': config.get('ckan.locale_default'),
        'extensions': config.get('ckan.plugins').split(),
        }
    else:
        return {'success': False}

@logic.validate(logic.schema.default_activity_list_schema)
def user_activity_list(context, data_dict):
    '''Return a user's public activity stream.

    You must be authorized to view the user's profile.


    :param id: the id or name of the user
    :type id: string
    :param offset: where to start getting activity items from
        (optional, default: 0)
    :type offset: int
    :param limit: the maximum number of activities to return
        (optional, default: 31, the default value is configurable via the
        ckan.activity_list_limit setting)
    :type limit: int

    :rtype: list of dictionaries

    '''
    # FIXME: Filter out activities whose subject or object the user is not
    # authorized to read.
    _check_access('user_show', context, data_dict)

    model = context['model']

    user_ref = data_dict.get('id')  # May be user name or id.
    user = model.User.get(user_ref)
    if user is None:
        raise logic.NotFound

    offset = data_dict.get('offset', 0)
    limit = int(
        data_dict.get('limit', config.get('ckan.activity_list_limit', 31)))

    _activity_objects = model.activity.user_activity_list(user.id, limit=limit,
            offset=offset)
    activity_objects = _get._filter_activity_by_user(_activity_objects,
                                                     _get._activity_stream_get_filtered_users())

    if config.get('ckan.gov_theme.is_back'):
        return model_dictize.activity_list_dictize(activity_objects, context)
    else:
        return 0

@logic.validate(logic.schema.default_activity_list_schema)
def package_activity_list(context, data_dict):
    '''Return a package's activity stream.

    You must be authorized to view the package.

    :param id: the id or name of the package
    :type id: string
    :param offset: where to start getting activity items from
        (optional, default: 0)
    :type offset: int
    :param limit: the maximum number of activities to return
        (optional, default: 31, the default value is configurable via the
        ckan.activity_list_limit setting)
    :type limit: int

    :rtype: list of dictionaries

    '''
    # FIXME: Filter out activities whose subject or object the user is not
    # authorized to read.
    _check_access('package_show', context, data_dict)

    model = context['model']

    package_ref = data_dict.get('id')  # May be name or ID.
    package = model.Package.get(package_ref)
    if package is None:
        raise logic.NotFound

    offset = int(data_dict.get('offset', 0))
    limit = int(
        data_dict.get('limit', config.get('ckan.activity_list_limit', 31)))

    _activity_objects = model.activity.package_activity_list(package.id,
            limit=limit, offset=offset)
    activity_objects = _get._filter_activity_by_user(_activity_objects,
                                                     _get._activity_stream_get_filtered_users())

    if config.get('ckan.gov_theme.is_back'):
        return model_dictize.activity_list_dictize(activity_objects, context)
    else:
        return 0

@logic.validate(logic.schema.default_activity_list_schema)
def group_activity_list(context, data_dict):
    '''Return a group's activity stream.

    You must be authorized to view the group.

    :param id: the id or name of the group
    :type id: string
    :param offset: where to start getting activity items from
        (optional, default: 0)
    :type offset: int
    :param limit: the maximum number of activities to return
        (optional, default: 31, the default value is configurable via the
        ckan.activity_list_limit setting)
    :type limit: int

    :rtype: list of dictionaries

    '''
    # FIXME: Filter out activities whose subject or object the user is not
    # authorized to read.
    _check_access('group_show', context, data_dict)

    model = context['model']
    group_id = data_dict.get('id')
    offset = data_dict.get('offset', 0)
    limit = int(
        data_dict.get('limit', config.get('ckan.activity_list_limit', 31)))

    # Convert group_id (could be id or name) into id.
    group_show = logic.get_action('group_show')
    group_id = group_show(context, {'id': group_id})['id']

    _activity_objects = model.activity.group_activity_list(group_id,
            limit=limit, offset=offset)
    activity_objects = _get._filter_activity_by_user(_activity_objects,
                                                     _get._activity_stream_get_filtered_users())

    if config.get('ckan.gov_theme.is_back'):
        return model_dictize.activity_list_dictize(activity_objects, context)
    else:
        return 0

@logic.validate(logic.schema.default_activity_list_schema)
def organization_activity_list(context, data_dict):
    '''Return a organization's activity stream.

    :param id: the id or name of the organization
    :type id: string

    :rtype: list of dictionaries

    '''
    # FIXME: Filter out activities whose subject or object the user is not
    # authorized to read.
    _check_access('organization_show', context, data_dict)

    model = context['model']
    org_id = data_dict.get('id')
    offset = data_dict.get('offset', 0)
    limit = int(
        data_dict.get('limit', config.get('ckan.activity_list_limit', 31)))

    # Convert org_id (could be id or name) into id.
    org_show = logic.get_action('organization_show')
    org_id = org_show(context, {'id': org_id})['id']

    _activity_objects = model.activity.group_activity_list(org_id,
            limit=limit, offset=offset)
    activity_objects = _get._filter_activity_by_user(_activity_objects,
                                                     _get._activity_stream_get_filtered_users())

    if config.get('ckan.gov_theme.is_back'):
        return model_dictize.activity_list_dictize(activity_objects, context)
    else:
        return 0

@logic.validate(logic.schema.default_pagination_schema)
def recently_changed_packages_activity_list(context, data_dict):
    '''Return the activity stream of all recently added or changed packages.

    :param offset: where to start getting activity items from
        (optional, default: 0)
    :type offset: int
    :param limit: the maximum number of activities to return
        (optional, default: 31, the default value is configurable via the
        ckan.activity_list_limit setting)
    :type limit: int

    :rtype: list of dictionaries

    '''
    # FIXME: Filter out activities whose subject or object the user is not
    # authorized to read.
    model = context['model']
    offset = data_dict.get('offset', 0)
    limit = int(
        data_dict.get('limit', config.get('ckan.activity_list_limit', 31)))

    _activity_objects = model.activity.recently_changed_packages_activity_list(
            limit=limit, offset=offset)
    activity_objects = _get._filter_activity_by_user(_activity_objects,
                                                     _get._activity_stream_get_filtered_users())


    if config.get('ckan.gov_theme.is_back'):
        return model_dictize.activity_list_dictize(activity_objects, context)
    else:
        return 0

def user_activity_list_html(context, data_dict):
    '''Return a user's public activity stream as HTML.

    The activity stream is rendered as a snippet of HTML meant to be included
    in an HTML page, i.e. it doesn't have any HTML header or footer.

    :param id: The id or name of the user.
    :type id: string
    :param offset: where to start getting activity items from
        (optional, default: 0)
    :type offset: int
    :param limit: the maximum number of activities to return
        (optional, default: 31, the default value is configurable via the
        ckan.activity_list_limit setting)
    :type limit: int

    :rtype: string

    '''
    activity_stream = user_activity_list(context, data_dict)
    offset = int(data_dict.get('offset', 0))
    extra_vars = {
        'controller': 'user',
        'action': 'activity',
        'id': data_dict['id'],
        'offset': offset,
    }

    if config.get('ckan.gov_theme.is_back'):
        return custom_activity_streams.activity_list_to_html(context, activity_stream, extra_vars)
    else:
        return 0

def package_activity_list_html(context, data_dict):
    '''Return a package's activity stream as HTML.

    The activity stream is rendered as a snippet of HTML meant to be included
    in an HTML page, i.e. it doesn't have any HTML header or footer.

    :param id: the id or name of the package
    :type id: string
    :param offset: where to start getting activity items from
        (optional, default: 0)
    :type offset: int
    :param limit: the maximum number of activities to return
        (optional, default: 31, the default value is configurable via the
        ckan.activity_list_limit setting)
    :type limit: int

    :rtype: string

    '''
    activity_stream = package_activity_list(context, data_dict)
    offset = int(data_dict.get('offset', 0))
    extra_vars = {
        'controller': 'package',
        'action': 'activity',
        'id': data_dict['id'],
        'offset': offset,
    }

    if config.get('ckan.gov_theme.is_back'):
        return _get.activity_streams.activity_list_to_html(context, activity_stream, extra_vars)
    else:
        return {'success': False}

def group_activity_list_html(context, data_dict):
    '''Return a group's activity stream as HTML.

    The activity stream is rendered as a snippet of HTML meant to be included
    in an HTML page, i.e. it doesn't have any HTML header or footer.

    :param id: the id or name of the group
    :type id: string
    :param offset: where to start getting activity items from
        (optional, default: 0)
    :type offset: int
    :param limit: the maximum number of activities to return
        (optional, default: 31, the default value is configurable via the
        ckan.activity_list_limit setting)
    :type limit: int

    :rtype: string

    '''
    activity_stream = group_activity_list(context, data_dict)
    offset = int(data_dict.get('offset', 0))
    extra_vars = {
        'controller': 'group',
        'action': 'activity',
        'id': data_dict['id'],
        'offset': offset,
    }

    if config.get('ckan.gov_theme.is_back'):
        return _get.activity_streams.activity_list_to_html(context, activity_stream, extra_vars)
    else:
        return {'success': False}

def organization_activity_list_html(context, data_dict):
    '''Return a organization's activity stream as HTML.

    The activity stream is rendered as a snippet of HTML meant to be included
    in an HTML page, i.e. it doesn't have any HTML header or footer.

    :param id: the id or name of the organization
    :type id: string

    :rtype: string

    '''
    activity_stream = organization_activity_list(context, data_dict)
    offset = int(data_dict.get('offset', 0))
    extra_vars = {
        'controller': 'organization',
        'action': 'activity',
        'id': data_dict['id'],
        'offset': offset,
    }

    if config.get('ckan.gov_theme.is_back'):
        return custom_activity_streams.activity_list_to_html(context, activity_stream, extra_vars)
    else:
        return {'success': False}

def user_follower_count(context, data_dict):
    '''Return the number of followers of a user.

    :param id: the id or name of the user
    :type id: string

    :rtype: int

    '''

    if config.get('ckan.gov_theme.is_back'):
        return _get._follower_count(
        context, data_dict,
        ckan.logic.schema.default_follow_user_schema(),
        context['model'].UserFollowingUser)
    else:
        return {'success': False}

def dataset_follower_count(context, data_dict):
    '''Return the number of followers of a dataset.

    :param id: the id or name of the dataset
    :type id: string

    :rtype: int

    '''

    if config.get('ckan.gov_theme.is_back'):
        return _get._follower_count(
        context, data_dict,
        ckan.logic.schema.default_follow_dataset_schema(),
        context['model'].UserFollowingDataset)
    else:
        return {'success': False}

def group_follower_count(context, data_dict):
    '''Return the number of followers of a group.

    :param id: the id or name of the group
    :type id: string

    :rtype: int

    '''

    if config.get('ckan.gov_theme.is_back'):
        return _get._follower_count(
        context, data_dict,
        ckan.logic.schema.default_follow_group_schema(),
        context['model'].UserFollowingGroup)
    else:
        return {'success': False}

def organization_follower_count(context, data_dict):
    '''Return the number of followers of an organization.

    :param id: the id or name of the organization
    :type id: string

    :rtype: int

    '''

    if config.get('ckan.gov_theme.is_back'):
        return group_follower_count(context, data_dict)
    else:
        return {'success': False}

def _follower_list(context, data_dict, default_schema, FollowerClass):
    schema = context.get('schema', default_schema)
    data_dict, errors = _validate(data_dict, schema, context)
    if errors:
        raise ValidationError(errors)

    # Get the list of Follower objects.
    model = context['model']
    object_id = data_dict.get('id')
    followers = FollowerClass.follower_list(object_id)

    # Convert the list of Follower objects to a list of User objects.
    users = [model.User.get(follower.follower_id) for follower in followers]
    users = [user for user in users if user is not None]

    # Dictize the list of User objects.

    if config.get('ckan.gov_theme.is_back'):
        return model_dictize.user_list_dictize(users, context)
    else:
        return {'success': False}

def user_follower_list(context, data_dict):
    '''Return the list of users that are following the given user.

    :param id: the id or name of the user
    :type id: string

    :rtype: list of dictionaries

    '''
    _check_access('user_follower_list', context, data_dict)

    if config.get('ckan.gov_theme.is_back'):
        return _follower_list(
        context, data_dict,
        ckan.logic.schema.default_follow_user_schema(),
        context['model'].UserFollowingUser)
    else:
        return {'success': False}

def dataset_follower_list(context, data_dict):
    '''Return the list of users that are following the given dataset.

    :param id: the id or name of the dataset
    :type id: string

    :rtype: list of dictionaries

    '''
    _check_access('dataset_follower_list', context, data_dict)

    if config.get('ckan.gov_theme.is_back'):
        return _follower_list(
        context, data_dict,
        ckan.logic.schema.default_follow_user_schema(),
        context['model'].UserFollowingUser)
    else:
        return {'success': False}

def group_follower_list(context, data_dict):
    '''Return the list of users that are following the given group.

    :param id: the id or name of the group
    :type id: string

    :rtype: list of dictionaries

    '''
    _check_access('group_follower_list', context, data_dict)

    if config.get('ckan.gov_theme.is_back'):
        return _follower_list(
        context, data_dict,
        ckan.logic.schema.default_follow_group_schema(),
        context['model'].UserFollowingGroup)
    else:
        return {'success': False}

def organization_follower_list(context, data_dict):
    '''Return the list of users that are following the given organization.

    :param id: the id or name of the organization
    :type id: string

    :rtype: list of dictionaries

    '''
    _check_access('organization_follower_list', context, data_dict)

    if config.get('ckan.gov_theme.is_back'):
        return _follower_list(
        context, data_dict,
        ckan.logic.schema.default_follow_group_schema(),
        context['model'].UserFollowingGroup)
    else:
        return {'success': False}

def am_following_user(context, data_dict):
    '''Return ``True`` if you're following the given user, ``False`` if not.

    :param id: the id or name of the user
    :type id: string

    :rtype: boolean

    '''

    if config.get('ckan.gov_theme.is_back'):
        return _get._am_following(
        context, data_dict,
        ckan.logic.schema.default_follow_user_schema(),
        context['model'].UserFollowingUser)
    else:
        return {'success': False}

def am_following_dataset(context, data_dict):
    '''Return ``True`` if you're following the given dataset, ``False`` if not.

    :param id: the id or name of the dataset
    :type id: string

    :rtype: boolean

    '''

    if config.get('ckan.gov_theme.is_back'):
        return _get._am_following(
        context, data_dict,
        ckan.logic.schema.default_follow_dataset_schema(),
        context['model'].UserFollowingDataset)
    else:
        return {'success': False}

def am_following_group(context, data_dict):
    '''Return ``True`` if you're following the given group, ``False`` if not.

    :param id: the id or name of the group
    :type id: string

    :rtype: boolean

    '''

    if config.get('ckan.gov_theme.is_back'):
        return _get._am_following(
        context, data_dict,
        ckan.logic.schema.default_follow_group_schema(),
        context['model'].UserFollowingGroup)
    else:
        return {'success': False}

def followee_count(context, data_dict):
    '''Return the number of objects that are followed by the given user.

    Counts all objects, of any type, that the given user is following
    (e.g. followed users, followed datasets, followed groups).

    :param id: the id of the user
    :type id: string

    :rtype: int

    '''
    model = context['model']
    followee_users = _get._followee_count(context, data_dict,
                                     model.UserFollowingUser)

    # followee_users has validated data_dict so the following functions don't
    # need to validate it again.
    context['skip_validation'] = True

    followee_datasets = _get._followee_count(context, data_dict,
                                        model.UserFollowingDataset)
    followee_groups = _get._followee_count(context, data_dict,
                                      model.UserFollowingGroup)


    if config.get('ckan.gov_theme.is_back'):
        return sum((followee_users, followee_datasets, followee_groups))
    else:
        return {'success': False}

def user_followee_count(context, data_dict):
    '''Return the number of users that are followed by the given user.

    :param id: the id of the user
    :type id: string

    :rtype: int

    '''

    if config.get('ckan.gov_theme.is_back'):
        return _get._followee_count(
        context, data_dict,
        context['model'].UserFollowingUser)
    else:
        return {'success': False}

def dataset_followee_count(context, data_dict):
    '''Return the number of datasets that are followed by the given user.

    :param id: the id of the user
    :type id: string

    :rtype: int

    '''

    if config.get('ckan.gov_theme.is_back'):
        return _get._followee_count(
        context, data_dict,
        context['model'].UserFollowingDataset)
    else:
        return {'success': False}

def group_followee_count(context, data_dict):
    '''Return the number of groups that are followed by the given user.

    :param id: the id of the user
    :type id: string

    :rtype: int

    '''

    if config.get('ckan.gov_theme.is_back'):
        return _get._followee_count(
        context, data_dict,
        context['model'].UserFollowingGroup)
    else:
        return {'success': False}

@logic.validate(logic.schema.default_follow_user_schema)
def followee_list(context, data_dict):
    '''Return the list of objects that are followed by the given user.

    Returns all objects, of any type, that the given user is following
    (e.g. followed users, followed datasets, followed groups.. ).

    :param id: the id of the user
    :type id: string

    :param q: a query string to limit results by, only objects whose display
        name begins with the given string (case-insensitive) wil be returned
        (optional)
    :type q: string

    :rtype: list of dictionaries, each with keys ``'type'`` (e.g. ``'user'``,
        ``'dataset'`` or ``'group'``), ``'display_name'`` (e.g. a user's
        display name, or a package's title) and ``'dict'`` (e.g. a dict
        representing the followed user, package or group, the same as the dict
        that would be returned by :py:func:`user_show`,
        :py:func:`package_show` or :py:func:`group_show`)

    '''
    _check_access('followee_list', context, data_dict)

    def display_name(followee):
        '''Return a display name for the given user, group or dataset dict.'''
        display_name = followee.get('display_name')
        fullname = followee.get('fullname')
        title = followee.get('title')
        name = followee.get('name')
        return display_name or fullname or title or name

    # Get the followed objects.
    # TODO: Catch exceptions raised by these *_followee_list() functions?
    # FIXME should we be changing the context like this it seems dangerous
    followee_dicts = []
    context['skip_validation'] = True
    context['ignore_auth'] = True
    for followee_list_function, followee_type in (
            (user_followee_list, 'user'),
            (dataset_followee_list, 'dataset'),
            (group_followee_list, 'group'),
            (_get.organization_followee_list, 'organization')):
        dicts = followee_list_function(context, data_dict)
        for d in dicts:
            followee_dicts.append(
                {'type': followee_type,
                 'display_name': display_name(d),
                 'dict': d})

    followee_dicts.sort(key=lambda d: d['display_name'])

    q = data_dict.get('q')
    if q:
        q = q.strip().lower()
        matching_followee_dicts = []
        for followee_dict in followee_dicts:
            if followee_dict['display_name'].strip().lower().startswith(q):
                matching_followee_dicts.append(followee_dict)
        followee_dicts = matching_followee_dicts


    if config.get('ckan.gov_theme.is_back'):
        return followee_dicts
    else:
        return 0

def user_followee_list(context, data_dict):
    '''Return the list of users that are followed by the given user.

    :param id: the id of the user
    :type id: string

    :rtype: list of dictionaries

    '''
    _check_access('user_followee_list', context, data_dict)

    if not context.get('skip_validation'):
        schema = context.get('schema') or (
            ckan.logic.schema.default_follow_user_schema())
        data_dict, errors = _validate(data_dict, schema, context)
        if errors:
            raise ValidationError(errors)

    # Get the list of Follower objects.
    model = context['model']
    user_id = _get._get_or_bust(data_dict, 'id')
    followees = model.UserFollowingUser.followee_list(user_id)

    # Convert the list of Follower objects to a list of User objects.
    users = [model.User.get(followee.object_id) for followee in followees]
    users = [user for user in users if user is not None]

    # Dictize the list of User objects.

    if config.get('ckan.gov_theme.is_back'):
        return model_dictize.user_list_dictize(users, context)
    else:
        return 0

def dataset_followee_list(context, data_dict):
    '''Return the list of datasets that are followed by the given user.

    :param id: the id or name of the user
    :type id: string

    :rtype: list of dictionaries

    '''
    _check_access('dataset_followee_list', context, data_dict)

    if not context.get('skip_validation'):
        schema = context.get('schema') or (
            ckan.logic.schema.default_follow_user_schema())
        data_dict, errors = _validate(data_dict, schema, context)
        if errors:
            raise ValidationError(errors)

    # Get the list of Follower objects.
    model = context['model']
    user_id = _get._get_or_bust(data_dict, 'id')
    followees = model.UserFollowingDataset.followee_list(user_id)

    # Convert the list of Follower objects to a list of Package objects.
    datasets = [model.Package.get(followee.object_id)
                for followee in followees]
    datasets = [dataset for dataset in datasets if dataset is not None]

    # Dictize the list of Package objects.

    if config.get('ckan.gov_theme.is_back'):
        return [model_dictize.package_dictize(dataset, context)
            for dataset in datasets]
    else:
        return 0

def group_followee_list(context, data_dict):
    '''Return the list of groups that are followed by the given user.

    :param id: the id or name of the user
    :type id: string

    :rtype: list of dictionaries

    '''
    _check_access('group_followee_list', context, data_dict)


    if config.get('ckan.gov_theme.is_back'):
        return _get._group_or_org_followee_list(context, data_dict, is_org=False)
    else:
        return 0

@logic.validate(logic.schema.default_pagination_schema)
def dashboard_activity_list(context, data_dict):
    '''Return the authorized user's dashboard activity stream.

    Unlike the activity dictionaries returned by other ``*_activity_list``
    actions, these activity dictionaries have an extra boolean value with key
    ``is_new`` that tells you whether the activity happened since the user last
    viewed her dashboard (``'is_new': True``) or not (``'is_new': False``).

    The user's own activities are always marked ``'is_new': False``.

    :param offset: where to start getting activity items from
        (optional, default: 0)
    :type offset: int
    :param limit: the maximum number of activities to return
        (optional, default: 31, the default value is configurable via the
        :ref:`ckan.activity_list_limit` setting)

    :rtype: list of activity dictionaries

    '''
    _check_access('dashboard_activity_list', context, data_dict)

    model = context['model']
    user_id = model.User.get(context['user']).id
    offset = data_dict.get('offset', 0)
    limit = int(
        data_dict.get('limit', config.get('ckan.activity_list_limit', 31)))

    # FIXME: Filter out activities whose subject or object the user is not
    # authorized to read.
    _activity_objects = model.activity.dashboard_activity_list(user_id,
            limit=limit, offset=offset)

    activity_objects = _get._filter_activity_by_user(_activity_objects,
                                                     _get._activity_stream_get_filtered_users())
    activity_dicts = model_dictize.activity_list_dictize(
        activity_objects, context)

    # Mark the new (not yet seen by user) activities.
    strptime = _get.datetime.datetime.strptime
    fmt = '%Y-%m-%dT%H:%M:%S.%f'
    last_viewed = model.Dashboard.get(user_id).activity_stream_last_viewed
    for activity in activity_dicts:
        if activity['user_id'] == user_id:
            # Never mark the user's own activities as new.
            activity['is_new'] = False
        else:
            activity['is_new'] = (
                strptime(activity['timestamp'], fmt) > last_viewed)

    if config.get('ckan.gov_theme.is_back'):
        return activity_dicts
    else:
        return {'success': False}

@logic.validate(ckan.logic.schema.default_pagination_schema)
def dashboard_activity_list_html(context, data_dict):
    '''Return the authorized user's dashboard activity stream as HTML.

    The activity stream is rendered as a snippet of HTML meant to be included
    in an HTML page, i.e. it doesn't have any HTML header or footer.

    :param id: the id or name of the user
    :type id: string
    :param offset: where to start getting activity items from
        (optional, default: 0)
    :type offset: int
    :param limit: the maximum number of activities to return
        (optional, default: 31, the default value is configurable via the
        ckan.activity_list_limit setting)
    :type limit: int

    :rtype: string

    '''
    activity_stream = dashboard_activity_list(context, data_dict)
    model = context['model']
    offset = data_dict.get('offset', 0)
    extra_vars = {
        'controller': 'user',
        'action': 'dashboard',
        'offset': offset,
    }

    if config.get('ckan.gov_theme.is_back'):
        return custom_activity_streams.activity_list_to_html(context, activity_stream,
                                                  extra_vars)
    else:
        return {'success': False}

def dashboard_new_activities_count(context, data_dict):
    '''Return the number of new activities in the user's dashboard.

    Return the number of new activities in the authorized user's dashboard
    activity stream.

    Activities from the user herself are not counted by this function even
    though they appear in the dashboard (users don't want to be notified about
    things they did themselves).

    :rtype: int

    '''
    _check_access('dashboard_new_activities_count', context, data_dict)
    activities = logic.get_action('dashboard_activity_list')(
        context, data_dict)

    if config.get('ckan.gov_theme.is_back'):
        return len([activity for activity in activities if activity['is_new']])
    else:
        return {'success': False}

def member_roles_list(context, data_dict):
    '''Return the possible roles for members of groups and organizations.

    :param group_type: the group type, either ``"group"`` or ``"organization"``
        (optional, default ``"organization"``)
    :type id: string
    :returns: a list of dictionaries each with two keys: ``"text"`` (the
        display name of the role, e.g. ``"Admin"``) and ``"value"`` (the
        internal name of the role, e.g. ``"admin"``)
    :rtype: list of dictionaries

    '''
    group_type = data_dict.get('group_type', 'organization')
    roles_list = authz.roles_list()
    if group_type == 'group':
        roles_list = [role for role in roles_list
                      if role['value'] != 'editor']

    _check_access('member_roles_list', context, data_dict)

    if config.get('ckan.gov_theme.is_back'):
        return roles_list
    else:
        return {'success': False}

