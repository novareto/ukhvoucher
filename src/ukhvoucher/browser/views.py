# -*- coding: utf-8 -*-

import uvclight
from ul.auth import require
from ..apps import AdminRoot, UserRoot
from ..interfaces import IModel, IModelContainer
from ..interfaces import IAdminLayer, IUserLayer
from zope.component import getMultiAdapter
from zope.interface import Interface
from zope.i18n import translate
from ..resources import ukhvouchers


class UserRootIndex(uvclight.Page):
    uvclight.name('index')
    uvclight.layer(IUserLayer)
    uvclight.context(UserRoot)
    require('users.access')

    template = uvclight.get_template('userroot.cpt', __file__)

    def update(self):
        self.categories = self._categories
        account = self.request.principal.getAccount()
        if account:
            if account.phone == "" or account.name == "" or account.email == "":
                self.redirect(self.url(self.context, 'edit_account'))

    @property
    def _categories(self):
        for cat in self.request.principal.getCategory():
            name = cat.getName()
            form = getMultiAdapter((self.context, self.request), Interface,
                                   name=name.lower() + 'form')
            form.update()
            form.updateForm()
            yield {
                'name': name,
                'doc': cat.getDoc(),
                'url': '%s/%sform' % (self.application_url(), name.lower()),
                'vouchers': self.request.principal.getVouchers(),
                'form': form,
                }


class AdminRootIndex(uvclight.Page):
    uvclight.name('index')
    uvclight.layer(IAdminLayer)
    uvclight.context(AdminRoot)
    require('manage.vouchers')

    @property
    def panels(self):
        for id in uvclight.traversable.bind().get(self.context):
            panel = getattr(self.context, id)
            yield {'title': translate(panel.__label__, context=self.request),
                   'url': self.url(panel)}
    template = uvclight.get_template('adminroot.cpt', __file__)

    def update(self):
        ukhvouchers.need()


class ContainerIndex(uvclight.Page):
    uvclight.name('index')
    uvclight.layer(IAdminLayer)
    uvclight.context(IModelContainer)
    require('manage.vouchers')

    template = uvclight.get_template('container.cpt', __file__)

    def update(self):
        self.columns = [field.title for field in self.context.listing_attrs]

    def listing(self, item):
        for col in self.context.listing_attrs:
            yield col.identifier, getattr(
                item, col.identifier, col.defaultValue)
