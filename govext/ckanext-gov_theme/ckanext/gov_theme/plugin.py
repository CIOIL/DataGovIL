import ckan
import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckan.lib.plugins import DefaultTranslation

import ckanext.gov_theme.action as _action
import ckanext.gov_theme.auth as _auth
import ckanext.gov_theme.schema as _schema
import ckanext.gov_theme.helpers as gov_helpers
from ckanext.gov_theme import blueprint

import logging

log = logging.getLogger(__name__)


class Gov_ThemePlugin(plugins.SingletonPlugin, DefaultTranslation):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.ITranslation)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IActions)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IResourceController)

    def get_blueprint(self):
        return blueprint.gov_blueprint

    # IConfigurer
    def update_config(self, config):
        toolkit.add_template_directory(config, 'theme/templates')
        toolkit.add_public_directory(config, 'theme/public')
        toolkit.add_resource('theme/public', 'gov_theme')
        ckan.logic.schema.default_user_schema = _schema.default_user_schema
        ckan.logic.schema.user_new_form_schema = _schema.user_new_form_schema
        ckan.logic.schema.user_edit_form_schema = _schema.user_edit_form_schema
        ckan.logic.schema.default_update_user_schema = _schema.default_update_user_schema
        ckan.logic.schema.default_tags_schema = _schema.default_tags_schema

    # ITemplateHelpers
    def get_helpers(self):
        return {'is_back_site': gov_helpers.is_back,
                'get_tags_count': gov_helpers.tags_count,
                'format_resource_items': gov_helpers.format_resource_items,
                'api_usage_count': gov_helpers.api_usage_count,
                'gui_view_count': gov_helpers.gui_view_count,
                'resource_download_count': gov_helpers.resource_download_count,
                'get_resources_count': gov_helpers.get_resources_count,
                'sessionTimeout': gov_helpers.getTimeout,
                'get_config_value': gov_helpers.get_config_value,
                'get_datasets_count': gov_helpers.get_datasets_count,
                'get_organizations_count': gov_helpers.get_organizations_count,
                'govil_markdown_extract': gov_helpers.govil_markdown_extract
                }

    # IActions
    def get_actions(self):
        return {'resource_create': _action.resource_create,
                'resource_update': _action.resource_update,
                'package_update': _action.package_update,
                'user_invite': _action.user_invite,
                'user_create_within_org': _action.user_create_within_org,
                'follow_user': _action.follow_user,
                'follow_dataset': _action.follow_dataset,
                'follow_group': _action.follow_group,
                'unfollow_user': _action.unfollow_user,
                'unfollow_dataset': _action.unfollow_dataset,
                'unfollow_group': _action.unfollow_group,
                'send_email_notifications': _action.send_email_notifications,
                'term_translation_update_many': _action.term_translation_update_many,
                'task_status_update_many': _action.task_status_update_many,
                'package_patch': _action.package_patch,
                'resource_patch': _action.resource_patch,
                'group_patch': _action.group_patch,
                'organization_patch': _action.organization_patch,
                'related_list': _action.related_list,
                'member_list': _action.member_list,
                'organization_list': _action.organization_list,
                'organization_delete': _action.organization_delete,
                'group_package_show': _action.group_package_show,
                'resource_search': _action.resource_search,
                'tag_search': _action.tag_search,
                'term_translation_show': _action.term_translation_show,
                'status_show': _action.status_show,
                'user_activity_list': _action.user_activity_list,
                'package_activity_list': _action.package_activity_list,
                'group_activity_list': _action.group_activity_list,
                'organization_activity_list': _action.organization_activity_list,
                'recently_changed_packages_activity_list': _action.recently_changed_packages_activity_list,
                'user_activity_list_html': _action.user_activity_list_html,
                'package_activity_list_html': _action.package_activity_list_html,
                'group_activity_list_html': _action.group_activity_list_html,
                'organization_activity_list_html': _action.organization_activity_list_html,
                'user_follower_count': _action.user_follower_count,
                'dataset_follower_count': _action.dataset_follower_count,
                'group_follower_count': _action.group_follower_count,
                'organization_follower_count': _action.organization_follower_count,
                '_follower_list': _action._follower_list,
                'user_follower_list': _action.user_follower_list,
                'dataset_follower_list': _action.dataset_follower_list,
                'group_follower_list': _action.group_follower_list,
                'organization_follower_list': _action.organization_follower_list,
                'am_following_user': _action.am_following_user,
                'am_following_dataset': _action.am_following_dataset,
                'am_following_group': _action.am_following_group,
                'followee_count': _action.followee_count,
                'user_followee_count': _action.user_followee_count,
                'dataset_followee_count': _action.dataset_followee_count,
                'group_followee_count': _action.group_followee_count,
                'followee_list': _action.followee_list,
                'user_followee_list': _action.user_followee_list,
                'dataset_followee_list': _action.dataset_followee_list,
                'group_followee_list': _action.group_followee_list,
                # 'dashboard_activity_list':  _action.dashboard_activity_list,
                # 'dashboard_activity_list_html':  _action.dashboard_activity_list_html,
                # 'dashboard_new_activities_count':  _action.dashboard_new_activities_count,
                'member_roles_list': _action.member_roles_list,
                'resource_tracking_count': _action.resource_tracking}

    # IAuthFunctions
    def get_auth_functions(self):
        return {'package_create': _auth.package_create,
                'resource_create': _auth.resource_create,

                'resource_view_create': _auth.resource_view_create,
                'resource_create_default_resource_views': _auth.resource_create_default_resource_views,
                'package_create_default_resource_views': _auth.package_create_default_resource_views,
                'package_relationship_create': _auth.package_relationship_create,
                'group_create': _auth.group_create,
                'organization_create': _auth.organization_create,
                'rating_create': _auth.rating_create,
                'user_create': _auth.user_create,
                'user_invite': _auth.user_invite,
                'organization_member_create': _auth.organization_member_create,
                'group_member_create': _auth.group_member_create,
                'member_create': _auth.member_create,

                'package_update': _auth.package_update,
                'package_resource_reorder': _auth.package_resource_reorder,
                'resource_update': _auth.resource_update,
                'resource_view_update': _auth.resource_view_update,
                'resource_view_reorder': _auth.resource_view_reorder,
                'package_relationship_update': _auth.package_relationship_update,
                'group_update': _auth.group_update,
                'organization_update': _auth.organization_update,

                'user_update': _auth.user_update,
                'user_generate_apikey': _auth.user_generate_apikey,
                'dashboard_mark_activities_old': _auth.dashboard_mark_activities_old,
                'bulk_update_private': _auth.bulk_update_private,
                'bulk_update_public': _auth.bulk_update_public,
                'bulk_update_delete': _auth.bulk_update_delete,

                'package_delete': _auth.package_delete,
                'resource_delete': _auth.resource_delete,
                'resource_view_delete': _auth.resource_view_delete,

                'package_relationship_delete': _auth.package_relationship_delete,
                'group_delete': _auth.group_delete,
                'organization_delete': _auth.organization_delete,
                'group_member_delete': _auth.group_member_delete,
                'organization_member_delete': _auth.organization_member_delete,
                'member_delete': _auth.member_delete,

                'revision_list': _auth.revision_list,
                'group_revision_list': _auth.group_revision_list,
                'organization_revision_list': _auth.organization_revision_list,
                'package_revision_list': _auth.package_revision_list,
                'user_list': _auth.user_list,
                'revision_show': _auth.revision_show,
                'user_show': _auth.user_show,
                'task_status_show': _auth.task_status_show,
                'resource_status_show': _auth.resource_status_show
                }

    # IResourceController

    def before_create(self, context, resource):
        pass

    def after_create(self, context, resource):
        pass

    def before_update(self, context, current, resource):
        log.info('Start resource_update for file:'
                 ' name: {name}, resource_id: {resource_id}, package_id: {package_id}, user: {user}, url: {url}'
                 .format(name=resource.get('name'), user=context.get('user'), url=current.get('original_url'),
                         resource_id=current.get('resource_id'), package_id=current.get('package_id')))

    def after_update(self, context, resource):
        pass

    def before_delete(self, context, resource, resources):
        pass

    def after_delete(self, context, resource):
        pass

    def before_show(self, resource_dict):
        pass
