# encoding: utf-8

import logging
from ckan.lib.authenticator import UsernamePasswordAuthenticator
from zope.interface import implements
from repoze.who.interfaces import IAuthenticator
from webob import Request
import captcha as custom_captcha
from ckan.model import User

log = logging.getLogger(__name__)


class CustomUsernamePasswordAuthenticator(UsernamePasswordAuthenticator):
    implements(IAuthenticator)

    def authenticate(self, environ, identity):

        request = Request(environ)
        if request.method == 'POST':
            came_from = request.params.get('came_from')
            if came_from == "/user/logged_in":
                #if not custom_captcha.check_recaptcha(request):
                log.debug('Bad Captcha error')
                return None

        if not ('login' in identity and 'password' in identity):
            return None

        login = identity['login']
        user = User.by_name(login)

        if user is None:
            log.debug('Login failed - username %r not found', login)
        elif not user.is_active():
            log.debug('Login as %r failed - user isn\'t active', login)
        elif not user.validate_password(identity['password']):
            log.debug('Login as %r failed - password not valid', login)
        else:
            return user.name

        return None
