# -*- coding: utf-8 -*-

import uvclight
import json
from ..models import Voucher
from ..interfaces import IAccount, IAdminLayer, IUserLayer
from .forms import ModelIndex
from dolmen.menu import Entry, menu
from ukhtheme.uvclight.viewlets import BelowContent
from uvc.design.canvas import menus
from uvc.entities.browser.menus import IPersonalMenu, INavigationMenu
from zope.interface import Interface


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
            return u"Keine Kategorien"
        return "Categories: %s" % ', '.join(
            (kat[0] for kat in values if kat[1]))


class VoucherGeneration(uvclight.Viewlet):
    uvclight.context(Voucher)
    uvclight.view(ModelIndex)
    uvclight.viewletmanager(BelowContent)

    template = uvclight.get_template('generation.cpt', __file__)

    def update(self):
        self.data = json.loads(self.context.generation.data)


class Username(uvclight.MenuItem):
    uvclight.context(Interface)
    uvclight.menu(IPersonalMenu)
    id = "username"
    action = ""
    submenu = None

    @property
    def title(self):
        try:
            return u"Sie sind angemeldet als: %s" % self.request.principal.title
        except:
            return "HHH"


class BaseNavMenu(uvclight.MenuItem):
    uvclight.context(Interface)
    uvclight.menu(INavigationMenu)
    uvclight.layer(IAdminLayer)
    uvclight.baseclass()

    attribute = ""
    title = "Startseite"

    @property
    def url(self):
        return "%s/%s" % (self.view.application_url(), self.attribute)

    @property
    def action(self):
        return self.url

    @property
    def selected(self):
        return self.request.url.startswith(self.url)


class Startseite(BaseNavMenu):
    uvclight.order(1)
    attribute = "/"
    title = "Startseite"


class MenuInvoice(BaseNavMenu):
    uvclight.order(2)
    attribute = "invoices"
    title = "Rechnung"


class MenuAccounts(BaseNavMenu):
    uvclight.order(3)
    attribute = "accounts"
    title = "Benutzer"


class MenuAddresses(BaseNavMenu):
    uvclight.order(3)
    attribute = "addresses"
    title = "Adressen"


class MenuKategorien(BaseNavMenu):
    uvclight.order(4)
    attribute = "categories"
    title = "Kategorien"


class MenuVouchers(BaseNavMenu):
    uvclight.order(5)
    attribute = "vouchers"
    title = "Gutscheine"

class Journal(BaseNavMenu):
    uvclight.order(6)
    attribute = "journal"
    title = u"Historie"
