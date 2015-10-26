# -*- coding: utf-8 -*-

import webob.exc

from . import Site
from .interfaces import IAdminLayer, IUserLayer
from .models import Accounts, Addresses, Account, Vouchers, Invoices, Categories

from cromlech.browser import IPublicationRoot
from cromlech.security import Interaction, unauthenticated_principal
from cromlech.sqlalchemy import get_session
from ul.auth import SecurePublication, ICredentials
from ul.browser.context import ContextualRequest
from ul.browser.decorators import sessionned
from ul.sql.decorators import transaction_sql
from uvclight import GlobalUtility, name
from uvclight.backends.sql import SQLPublication
from zope.component import getGlobalSiteManager
from zope.interface import implementer
from zope.location import Location
from zope.security.proxy import removeSecurityProxy
from uvclight.directives import traversable


@implementer(ICredentials)
class Access(GlobalUtility):
    name('admins')
    
    def log_in(self, request, username, password, **kws):
        if username == "admin" and password == "admin":
            return True
        return None


@implementer(ICredentials)
class AdminUsers(GlobalUtility):
    name('users')

    def log_in(self, request, username, password, **kws):
        session = get_session('ukhvoucher')
        user = session.query(Account).filter(Account.oid == username)
        if user.count():
            user = user.one()
            if user.password == password:
                return user
        return None


@implementer(IPublicationRoot)
class AdminRoot(Location):
    traversable('categories', 'accounts', 'addresses', 'vouchers', 'invoices')
    
    credentials = ('admins',)

    def getSiteManager(self):
        return getGlobalSiteManager()

    def __init__(self, request, session_key):
        self.accounts = Accounts(self, 'accounts', session_key)
        self.addresses = Addresses(self, 'addresses', session_key)
        self.vouchers = Vouchers(self, 'vouchers', session_key)
        self.invoices = Invoices(self, 'invoices', session_key)
        self.categories = Categories(self, 'categories', session_key)
        

class Admin(SQLPublication, SecurePublication):

    layers = [IAdminLayer]
    
    def setup_database(self, engine):
        pass

    def principal_factory(self, username):
        principal = SecurePublication.principal_factory(self, username)
        if principal is not unauthenticated_principal:
            principal.permissions = set(('manage.vouchers',))
            principal.roles = set()
        return principal

    def site_manager(self, request):
        return Site(AdminRoot(request, self.name))

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
        from .components import ExternalPrincipal
        if username:
            principal = ExternalPrincipal(id=username)
            principal.permissions = set(('users.access',))
            principal.roles = set()
            return principal
        return unauthenticated_principal

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
            with ContextualRequest(environ, layers=layers) as request:
                response = self.publish_traverse(request)
                return response(environ, start_response)

        return publish(environ, start_response)
