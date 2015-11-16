# -*- coding: utf-8 -*-

import uvclight


from .views import ModelIndex
from ..interfaces import IAccount
from zope.interface import Interface
from ukhtheme.uvclight.viewlets import BelowContent


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


from uvc.entities.browser.menus import IPersonalMenu

class Username(uvclight.MenuItem):
    uvclight.context(Interface)
    uvclight.menu(IPersonalMenu)
    id = "username"
    action = ""
    submenu = None

    @property
    def title(self):
        return u"Sie sind angemeldet als: %s" % self.request.principal.title


