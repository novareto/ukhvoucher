# -*- coding: utf-8 -*-

import webob.exc
import transaction


from . import Site
from .components import ExternalPrincipal, AdminPrincipal
from .interfaces import IAdminLayer, IUserLayer
from .models import Accounts, Addresses, Account, Vouchers, Invoices, Categories
from .caching_query import query_callable
from .environment import regions

from cromlech.browser import IPublicationRoot, getSession
from cromlech.security import Interaction, unauthenticated_principal
from cromlech.sqlalchemy import get_session, SQLAlchemySession
from ul.auth import SecurePublication, ICredentials
from ul.browser.context import ContextualRequest
from ul.browser.decorators import sessionned
from uvclight import GlobalUtility, name
from uvclight.backends.sql import SQLPublication
from zope.component import getGlobalSiteManager
from zope.interface import implementer
from zope.location import ILocation, LocationProxy, locate
from zope.location import Location
from zope.security.proxy import removeSecurityProxy
from uvclight.directives import traversable
from .resources import ukhcss
from base64 import decodestring


def transaction_sql(engine):
    def sql_wrapped(wrapped):
        def caller(*args):
            with transaction.manager as tm:
                query_cls = query_callable(regions)
                with SQLAlchemySession(
                        engine, transaction_manager=tm, query_cls=query_cls):
                    return wrapped(*args)
        return caller
    return sql_wrapped


USERS = {
    'admin': dict(login="admin", passwort="!admin!", permissions=('manage.vouchers', 'display.vouchers')),
    'mseibert': dict(login="mseibert", passwort="susanne09", permissions=('manage.vouchers', 'display.vouchers')),
    'mleber': dict(login="mleber", passwort="ehr17!", permissions=('manage.vouchers', 'display.vouchers')),
    'hgabt': dict(login="hgabt", passwort="AB471!", permissions=('manage.vouchers', 'display.vouchers')),
    'ckraft': dict(login="ckraft", passwort="QX392!", permissions=('manage.vouchers', 'display.vouchers')),
    'aburkhard': dict(login="aburkhard", passwort="NY259!", permissions=('manage.vouchers', 'display.vouchers')),
    'rknittel': dict(login="rknittel", passwort="XA056!", permissions=('manage.vouchers', 'display.vouchers')),
    'evstraub': dict(login="evstraub", passwort="AH221!", permissions=('manage.vouchers', 'display.vouchers')),
    'bsvejda': dict(login="bsvejda", passwort="ZT780!", permissions=('manage.vouchers', 'display.vouchers')),
    'pschaeferdeluca': dict(login="pschaeferdeluca", passwort="UK926!", permissions=('manage.vouchers', 'display.vouchers')),
    'dreichelt': dict(login="dreichelt", passwort="xq819!", permissions=('manage.vouchers', 'display.vouchers')),
    'amehicjusic': dict(login="amehicjusic", passwort="tz851!", permissions=('manage.vouchers', 'display.vouchers')),
    'viewer': dict(login="viewer", passwort="viewer", permissions=("display.vouchers",)),
    }



@implementer(ICredentials)
class Access(GlobalUtility):
    name('admins')

    def log_in(self, request, username, password, **kws):
        user = USERS.get(username)
        if user and user['passwort'] == password:
            return True
        return None


@implementer(ICredentials)
class AdminUsers(GlobalUtility):
    name('users')

    def log_in(self, request, username, password, **kws):
        session = get_session('ukhvoucher')
        user = session.query(Account).filter(Account.login == username, Account.az == "eh")
        if user.count():
            user = user.one()
            if user.password.strip() == password:
                return user
        return None


class AccountTraverser(Location):

    def __init__(self, parent, name):
        self.__parent__ = parent
        self.__name__ = name

    def __getitem__(self, key):
        session = get_session('ukhvoucher')
        try:
            ret = session.query(Account).filter(Account.oid == key).all()
            if ret > 0:
                model = ret[0]
                proxy = ILocation(model, None)
                if proxy is None:
                    proxy = LocationProxy(model)
                locate(proxy, self, str(model.oid))
                return proxy
            else:
                raise KeyError
        except:
            raise KeyError


@implementer(IPublicationRoot)
class AdminRoot(Location):
    traversable('categories', 'accounts', 'addresses', 'vouchers', 'invoices', 'account')

    credentials = ('admins',)

    def getSiteManager(self):
        return getGlobalSiteManager()

    def __init__(self, request, session_key):
        self.accounts = Accounts(self, 'accounts', session_key)
        self.addresses = Addresses(self, 'addresses', session_key)
        self.vouchers = Vouchers(self, 'vouchers', session_key)
        self.invoices = Invoices(self, 'invoices', session_key)
        self.categories = Categories(self, 'categories', session_key)
        self.account = AccountTraverser(self, 'account')


class Admin(SQLPublication, SecurePublication):

    layers = [IAdminLayer]

    def setup_database(self, engine):
        pass

    def principal_factory(self, username):
        if username:
            session = getSession()
            masquarade = session.get('masquarade', None)
            user = USERS.get(username)
            permissions = frozenset(user['permissions'])
            return AdminPrincipal(username, masquarade, permissions)
        return unauthenticated_principal

    def site_manager(self, request):
        return Site(AdminRoot(request, self.name))

    def __runner__(self, func):
        return SQLPublication.__runner__(self, func)

    def __interact__(self, *args, **kwargs):
        return SQLPublication.__interact__(self, *args, **kwargs)

    def publish_traverse(self, request):
        user = self.get_credentials(request.environment)
        request.principal = self.principal_factory(user)
        try:
            with self.site_manager(request) as site:
                with Interaction(request.principal):
                    response = self.publish(request, site)
                    response = removeSecurityProxy(response)
                    return response
        except webob.exc.HTTPException as e:
            return e

    def __call__(self, environ, start_response):

        @sessionned(self.session_key)
        @transaction_sql(self.engine)
        def publish(environ, start_response):
            layers = self.layers or list()
            ukhcss.need()
            with ContextualRequest(environ, layers=layers) as request:
                response = self.publish_traverse(request)
                return response(environ, start_response)

        return publish(environ, start_response)


@implementer(IPublicationRoot)
class UserRoot(Location):
    traversable('accounts', 'addresses')

    credentials = ('users',)

    def __init__(self, request, session_key):
        pass

    def getSiteManager(self):
        return getGlobalSiteManager()



class User(SQLPublication, SecurePublication):

    layers = [IUserLayer]

    def setup_database(self, engine):
        pass

    def principal_factory(self, username):
        if username:
            return ExternalPrincipal(id=username)
        return unauthenticated_principal

    def get_credentials(self, environ):
        auser = None
        if 'HTTP_AUTHORIZATION' in environ.keys():
            auser = decodestring(environ.get('HTTP_AUTHORIZATION')[6:]).split(':')[0]
        session = getSession()
        user = environ.get('REMOTE_USER') or session.get('username') or auser
        return user

    def site_manager(self, request):
        return Site(UserRoot(request, self.name))

    def publish_traverse(self, request):
        user = self.get_credentials(request.environment)
        request.principal = self.principal_factory(user)
        try:
            with self.site_manager(request) as site:
                with Interaction(request.principal):
                    response = self.publish(request, site)
                    response = removeSecurityProxy(response)
                    return response
        except webob.exc.HTTPException as e:
            return e

    def __call__(self, environ, start_response):

        @sessionned(self.session_key)
        @transaction_sql(self.engine)
        def publish(environ, start_response):
            layers = self.layers or list()
            ukhcss.need()
            with ContextualRequest(environ, layers=layers) as request:
                response = self.publish_traverse(request)
                return response(environ, start_response)

        return publish(environ, start_response)
