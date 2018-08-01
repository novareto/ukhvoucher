# -*- coding: utf-8 -*-

from cromlech.configuration.utils import load_zcml
from cromlech.i18n import register_allowed_languages, setLanguage
from cromlech.sqlalchemy import create_engine
from paste.urlmap import URLMap
from ul.auth import GenericSecurityPolicy
from zope.i18n import config
from zope.security.management import setSecurityPolicy
from webob import Response

from . import Base
from .apps import Admin, User
from collections import namedtuple


Configuration = namedtuple(
    'Configuration',
    ('session_key', 'engine', 'name', 'fs_store', 'layer', 'smtp_server')
)


def localize(application):
    def wrapper(*args, **kwargs):
        setLanguage('de')
        return application(*args, **kwargs)
    return wrapper

def router(conf, session_key, zcml, dsn, name):
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

    # Router
    root = URLMap()
    configuration = Configuration(session_key, engine, name, None, None, None)
    admin_app = Admin(configuration)
    root['/admin'] = localize(admin_app)
    root['/'] = localize(User(configuration))

    root.__runner__ = admin_app.__runner__

    return root
