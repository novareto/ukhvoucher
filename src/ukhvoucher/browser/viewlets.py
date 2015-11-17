# -*- coding: utf-8 -*-

import uvclight


from .views import ModelIndex
from ..interfaces import IAccount
from zope.interface import Interface
from ukhtheme.uvclight.viewlets import BelowContent
from uvc.entities.browser.menus import IPersonalMenu, INavigationMenu
from ..interfaces import IAdminLayer, IUserLayer


class Categories(uvclight.Viewlet):
    uvclight.context(IAccount)
    uvclight.view(ModelIndex)
    uvclight.viewletmanager(BelowContent)

    def render(self):
        values = []
        categories = self.context.categories
        for category in categories:
            values += [(kid, getattr(category, kid))
                       for kid in ('kat1', 'kat2', 'kat3', 'kat4', 'kat5')]
        if not values:
            return u"No categories"
        return "Categories: %s" % ', '.join(
            (kat[0] for kat in values if kat[1]))


class Username(uvclight.MenuItem):
    uvclight.context(Interface)
    uvclight.menu(IPersonalMenu)
    id = "username"
    action = ""
    submenu = None

    @property
    def title(self):
        return u"Sie sind angemeldet als: %s" % self.request.principal.title


class BaseNavMenu(uvclight.MenuItem):
    uvclight.context(Interface)
    uvclight.menu(INavigationMenu)
    uvclight.layer(IAdminLayer)
    uvclight.baseclass()

    id = ""
    title = "Startseite"

    @property
    def action(self):
        return "%s/%s" % (self.view.application_url(), self.id)


class Startseite(BaseNavMenu):
    uvclight.order(1)
    id = "/"
    title = "Startseite"


class MenuInvoice(BaseNavMenu):
    uvclight.order(2)
    id = "invoices"
    title = "Rechnung"


class MenuAccounts(BaseNavMenu):
    uvclight.order(3)
    id = "accounts"
    title = "Benutzer"


class MenuAddresses(BaseNavMenu):
    uvclight.order(3)
    id = "addresses"
    title = "Adressen"


class MenuKategorien(BaseNavMenu):
    uvclight.order(4)
    id = "categories"
    title = "Katgorien"


class MenuVouchers(BaseNavMenu):
    uvclight.order(5)
    id = "vouchers"
    title = "Gutscheine"
