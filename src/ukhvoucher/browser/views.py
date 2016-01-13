# -*- coding: utf-8 -*-

import uvclight
from ..apps import AdminRoot, UserRoot
from ..interfaces import IAdminLayer, IUserLayer
from ..interfaces import IModel, IModelContainer
from ..resources import ukhvouchers
from ..models import JournalEntry
from cromlech.sqlalchemy import get_session
from sqlalchemy import inspect
from ul.auth import require
from zope.component import getMultiAdapter
from zope.component.hooks import getSite
from zope.i18n import translate
from zope.interface import Interface
from dolmen.batch import Batcher
from ..resources import ukhcss


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
            if (account.phone.strip() == "" or
                account.nname.strip() == "" or
                account.email.strip() == "" or
                account.vname.strip() == ""):
                print "redirect"
                self.redirect(self.url(self.context, 'edit_account'))

    @property
    def _categories(self):
        for cat in sorted(self.request.principal.getCategory(),
                          key=lambda x: x.getName()):
            name = cat.getName()
            form = getMultiAdapter((self.context, self.request), Interface,
                                   name=name.lower() + 'form')
            form.update()
            form.updateForm()
            yield {
                'name': name,
                'doc': cat.getDoc(),
                'desc': self.getDesc(name),
                'url': '%s/%sform' % (self.application_url(), name.lower()),
                'vouchers': self.request.principal.getVouchers(),
                'form': form,
                }

    def getDesc(self, name):
        desc = ""
        if name == "IKG1":
            desc = u"Lorem IPSUM"
        return desc


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

    def listing(self, item):
        details = inspect(item)
        relations = details.mapper.relationships.keys()
        itemurl = self.url(item)

        for col in self.context.listing_attrs:
            value = getattr(item, col.identifier, col.defaultValue)
            if col.identifier in relations:
                relation = self.relation(col.identifier, value)
                yield col.identifier, [{
                    'value': rel.title,
                    'link': link} for rel, link in relation]
            else:
                yield col.identifier, [{
                    'value': value,
                    'link': col.identifier == 'oid' and itemurl or ''}]

    def update(self):
        ukhcss.need()
        self.columns = [field.title for field in self.context.listing_attrs]
        elements = list(self.context)
        self.batching = Batcher(self.context, self.request, size=10)
        self.batching.update(elements)        

    def relation(self, id, value):
        site = getSite()
        if id == 'vouchers':
            baseurl = self.url(site) + '/vouchers/'
            for voucher in value:
                yield voucher, baseurl + str(voucher.oid)


class JournalIndex(uvclight.Page):
    uvclight.name('journal')
    uvclight.layer(IAdminLayer)
    uvclight.context(Interface)
    require('manage.vouchers')

    template = uvclight.get_template('journal.cpt', __file__)

    def update(self):
        session = get_session('ukhvoucher')
        self.entries = session.query(JournalEntry)
