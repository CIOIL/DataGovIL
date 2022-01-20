import ckan
import logging
import ckan.lib.base as _base
from ckan.common import c, request, g


log = logging.getLogger(__name__)

def csrf_check(self):
    '''
    from pylons.decorators.secure import  authenticated_form
    from webhelpers.pylonslib import secure_form

    if authenticated_form(request.POST):
        del request.POST[secure_form.token_key]
    else:
        log.warn('Cross-site request forgery detected, request denied: %r '
                 'REMOTE_ADDR: %s' % (request, request.remote_addr))
        _base.abort(403, detail="Cross-site request forgery detected, request denied. See "
                          "http://en.wikipedia.org/wiki/Cross-site_request_forgery for more "
                          "information.")
    '''
    pass

# def g_analitics():
#     log.info("g_analitics start")
#     # GOV CUSTOM CODE START
#     url = request.environ['CKAN_CURRENT_URL'].split('?')[0]
#     # /fanstatic/"ns=asdas<![endif]--><BODY ONLOAD=alert('xxx')><SCRIPT>
#     #if "fanstatic" in url:
#     #    _base.abort(401, ('You can not enter fanstatic directory directly'))
#     log.info("url: " + url)
#     c.organization_id = None
#     # get the first folder after the site name
#     type_from_url = url.split('/')[1]
#     log.info("type_from_url: " + type_from_url)
#     # get the last folder (the id) to search
#     type_id = url.split('/')[-1]
#     log.info("type_id: " + type_id)
#     import json
#     import requests
#     if type_from_url == "organization":
#         log.info("*** ORGANIZATION LEVEL ***")
#         # check if we are inside an organization
#         try:
#             dataset_dict = {
#                 'id': type_id,
#             }
#             organization_show_api = _base.config.get('ckan.site_url') + '/api/3/action/organization_show?id='
#             organization_show_api_url = organization_show_api + type_id
#             log.info("organization_show_api_url: "+ organization_show_api_url)
#             response = requests.get(organization_show_api_url)
#             response_dict = json.loads(response.text)
#             log.info(response_dict)
#             if (response_dict['success'] and len(response_dict['result']['extras'])>0):
#                 c.organization_id = response_dict['result']['extras'][0]['value']
#         except Exception as ex:
#             log.error(ex.message)
#             c.organization_id = None
#
#     elif type_from_url == "dataset":
#         log.info("*** DATASET/RESOURCE LEVEL ***")
#         # check if we are inside a dataset
#         try:
#             if "resource" in url:
#                 log.info("*** RESOURCE LEVEL ***")
#                 # we are at resource level (resource id)
#                 # use the resource id to get the package id
#                 dataset_dict = {
#                     'id': type_id,
#                 }
#                 resource_show_api = _base.config.get('ckan.site_url') + '/api/3/action/resource_show?id='
#                 resource_show_api_url = resource_show_api + type_id
#                 log.info("RESOURCE LEVEL - resource_show_api_url: " + resource_show_api_url)
#                 response = requests.get(resource_show_api_url)
#                 response_dict = json.loads(response.text)
#                 log.info(response_dict)
#
#                 if (response_dict['success']):
#                     # use the package id to get the organization id
#                     package_id = response_dict['result']['package_id']
#                     log.info("RESOURCE LEVEL - package_id: " + package_id)
#                     package_show_api = _base.config.get('ckan.site_url') + '/api/3/action/package_show?id='
#                     package_show_api_url = package_show_api + package_id
#                     log.info("RESOURCE LEVEL - package_show_api_url: " + package_show_api_url)
#                     response = requests.get(package_show_api_url)
#                     response_dict = json.loads(response.text)
#                     if (response_dict['success']):
#                         org_id = response_dict['result']['organization']['id']
#                         organization_show_api = _base.config.get('ckan.site_url') + '/api/3/action/organization_show?id='
#                         organization_show_api_url = organization_show_api + org_id
#                         response = requests.get(organization_show_api_url)
#                         response_dict = json.loads(response.text)
#                         if(response_dict['success'] and len(response_dict['result']['extras'])>0):
#                             c.organization_id = response_dict['result']['extras'][0]['value']
#             else:
#                 log.info("*** DATASET LEVEL ***")
#                 # we are at dataset level (package id)
#                 dataset_dict = {
#                     'id': type_id,
#                 }
#                 package_show_api = _base.config.get('ckan.site_url') + '/api/3/action/package_show?id='
#                 package_show_api_url = package_show_api + type_id
#                 response = requests.get(package_show_api_url)
#                 response_dict = json.loads(response.text)
#                 log.info(response_dict)
#                 if (response_dict['success']):
#                     org_id = response_dict['result']['organization']['id']
#                     organization_show_api = _base.config.get('ckan.site_url') + '/api/3/action/organization_show?id='
#                     organization_show_api_url = organization_show_api + org_id
#                     response = requests.get(organization_show_api_url)
#                     response_dict = json.loads(response.text)
#                     if (response_dict['success'] and len(response_dict['result']['extras'])>0):
#                         c.organization_id = response_dict['result']['extras'][0]['value']
#         except Exception as ex:
#             log.error(ex.message)
#             c.organization_id = None
#             # GOV CUSTOM CODE END


