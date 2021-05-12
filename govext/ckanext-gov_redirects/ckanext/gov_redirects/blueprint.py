from flask import Blueprint
from flask import redirect
from ckan.common import config
from types import FunctionType

redirects_blueprint = Blueprint(u'redirects', __name__)

config_redirects_prefix = 'ckanext.gov_redirects'
config_redirects_keys = [x for x in config.keys() if x.startswith(config_redirects_prefix)]
for redirect_key in config_redirects_keys:
    endpoint = redirect_key.replace('.', '')

    # function during run-time
    func_str = "def {function_name}(): return redirect('{url}', code=302)".format(
        function_name=endpoint,
        url=config.get(redirect_key, ''))
    f_code = compile(func_str, "<string>", "exec")
    f_func = FunctionType(f_code.co_consts[0], globals(), "gfg")

    # add route to flask
    redirects_blueprint.add_url_rule(rule=redirect_key[len(config_redirects_prefix):].replace('.', '/'),
                                     endpoint=endpoint,
                                     view_func=f_func)



