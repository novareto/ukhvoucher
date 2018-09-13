# -*- coding: utf-8 -*-

import Cookie

from cromlech.configuration.utils import load_zcml
from cromlech.i18n import register_allowed_languages, setLanguage
from cromlech.sqlalchemy import create_engine
from paste.urlmap import URLMap
from ul.auth import GenericSecurityPolicy
from zope.i18n import config
from zope.security.management import setSecurityPolicy
from webob import Response

from . import Base
from os import path
from .apps import Admin, User
from collections import namedtuple
from cromlech.jwt.components import ExpiredToken
from cromlech.sessions.jwt import JWTCookieSession
from cromlech.sessions.jwt import key_from_file


Configuration = namedtuple(
    'Configuration',
    ('session_key', 'engine', 'name', 'fs_store', 'layer', 'smtp_server')
)


class Session(JWTCookieSession):

    def extract_session(self, environ):
        if 'HTTP_COOKIE' in environ:
            cookie = Cookie.SimpleCookie()
            cookie.load(environ['HTTP_COOKIE'])
            token = cookie.get(self.cookie_name)
            if token is not None:
                try:
                    session_data = self.check_token(token.value)
                    return session_data
                except ExpiredToken:
                    environ['session.timeout'] = True
        return {}


def localize(application):
    def wrapper(*args, **kwargs):
        setLanguage('de')
        return application(*args, **kwargs)
    return wrapper


def router(conf, session_key, zcml, dsn, name, root):
    allowed = ('de',)
    register_allowed_languages(allowed)
    config.ALLOWED_LANGUAGES = None

    load_zcml(zcml)

    setSecurityPolicy(GenericSecurityPolicy)

    # We register our SQLengine under a given name
    engine = create_engine(dsn, name)
    # We use a declarative base, if it exists we bind it and create
    engine.bind(Base)
    metadata = Base.metadata
    metadata.create_all(engine.engine, checkfirst=True)

    # We create the session wrappper
    key = key_from_file(path.join(root, 'jwt.key'))
    session_wrapper = Session(key, 6000, environ_key=session_key)

    # Router
    root = URLMap()
    configuration = Configuration(session_key, engine, name, None, None, None)
    admin_app = Admin(configuration)
    root['/admin'] = localize(admin_app)
    root['/'] = localize(User(configuration))

    root.__runner__ = admin_app.__runner__

    return session_wrapper(root.__call__)
