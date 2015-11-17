# -*- coding: utf-8 -*-

import uvclight


from .forms import ModelIndex
from ..interfaces import IAccount
from zope.interface import Interface
from ukhtheme.uvclight.viewlets import BelowContent
from uvc.entities.browser.menus import IPersonalMenu
from dolmen.menu import Entry, menu
from uvc.design.canvas import menus
from ..interfaces import IAdminLayer


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


class VouchersEntry(Entry):
    uvclight.context(Interface)
    menu(menus.NavigationMenu)
    uvclight.layer(IAdminLayer)
    uvclight.title('Vouchers')

    attribute = 'vouchers'

    @property
    def url(self):
        site = uvclight.url(self.request, uvclight.getSite())
        return '%s/%s' % (site, self.attribute)

    @property
    def action(self):
        return self.url

    @property
    def selected(self):
        return self.request.url.startswith(self.url)


class InvoicesEntry(VouchersEntry):
    uvclight.title('Invoices')
    attribute = 'invoices'


class AddressesEntry(VouchersEntry):
    uvclight.title('Addresses')
    attribute = 'addresses'


class CategoriesEntry(VouchersEntry):
    uvclight.title('Categories')
    attribute = 'categories'


class AccountsEntry(VouchersEntry):
    uvclight.title('Accounts')
    attribute = 'accounts'
