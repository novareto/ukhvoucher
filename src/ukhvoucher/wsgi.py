# -*- coding: utf-8 -*-

from cromlech.configuration.utils import load_zcml
from cromlech.i18n import register_allowed_languages, setLanguage
from cromlech.sqlalchemy import create_and_register_engine
from paste.urlmap import URLMap
from ul.auth import GenericSecurityPolicy
from zope.i18n import config
from zope.security.management import setSecurityPolicy

from . import Base
from .apps import Admin, User


def localize(application):
    def wrapper(*args, **kwargs):
        setLanguage('de')
        return application(*args, **kwargs)
    return wrapper


def router(conf, session_key, zcml, name):

    allowed = ('de',)
    register_allowed_languages(allowed)
    config.ALLOWED_LANGUAGES = None

    load_zcml(zcml)

    setSecurityPolicy(GenericSecurityPolicy)

    # We register our SQLengine under a given name
    dsn = "sqlite:////tmp/ukhvoucher.db"
    dsn = "sqlite:////Users/ck/tmp/ukhvoucher.db"
    engine = create_and_register_engine(dsn, name)

    # We use a declarative base, if it exists we bind it and create
    engine.bind(Base)
    metadata = Base.metadata
    metadata.create_all(engine.engine, checkfirst=True)

    # Router
    root = URLMap()
    root['/admin'] = localize(Admin(session_key, engine, name))
    root['/external'] = localize(User(session_key, engine, name))

    return root
