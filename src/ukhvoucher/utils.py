# -*- coding: utf-8 -*-


from cromlech.browser import IPublicationRoot
from zope.interface import implements
from zope.location import Location
from zope.component import getGlobalSiteManager
from uvclight.utils import Site
#from ul.auth import SecurePublication
from ul.browser.publication import Publication


class Root(Location):
    implements(IPublicationRoot)

    title = u"Example Site"
    description = u"An Example application."

    def __init__(self, name):
        self.name = name

    def getSiteManager(self):
        return getGlobalSiteManager()


class Application(Publication):

    def site_manager(self, environ):
        return Site(Root, self.name)
