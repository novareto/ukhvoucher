# -*- coding: utf-8 -*-

import uvclight
from GenericCache.GenericCache import GenericCache
from webhelpers.html.builder import HTML
from ukhvoucher import models
from ..apps import AdminRoot, UserRoot
from ..interfaces import IAdminLayer, IUserLayer
from ..interfaces import IModelContainer, get_oid
from ..models import JournalEntry
from ..resources import ukhcss
from ..resources import ukhvouchers, masked_input
from .batch import get_dichotomy_batches
from cromlech.sqlalchemy import get_session
from dolmen.batch import Batcher
from sqlalchemy import inspect
from ul.auth import require
from zope.component import getMultiAdapter
from zope.component.hooks import getSite
from zope.i18n import translate
from zope.interface import Interface
from profilehooks import profile
from natsort import natsorted
from ..components import cached


cache = GenericCache(maxsize=5000)


def principal_marshaller(func, view, principal):
    return repr((func.__name__, view.__name__, principal.oid))


class SearchUnternehmen(uvclight.JSON):
    uvclight.name('search_unternehmen')
    uvclight.layer(IAdminLayer)
    uvclight.context(Interface)
    require('manage.vouchers')

    #@profile
    def update(self):
        self.term = self.request.form['data[q]']
        self.vocabulary = get_oid(self.context)

    #@profile
    def render(self):
        terms = []
        matcher = self.term.lower()
        for item in self.vocabulary:
            if matcher in item.title.lower():
                terms.append({'id': item.token, 'text': item.title})
        return {'q': self.term, 'results': terms}



class UserRootIndex(uvclight.Page):
    uvclight.name('index')
    uvclight.layer(IUserLayer)
    uvclight.context(UserRoot)
    require('users.access')

    template = uvclight.get_template('userroot.cpt', __file__)

    def update(self):
        ukhvouchers.need()
        self.categories = self._categories
        account = self.request.principal.getAccount()
        if account:
            if (account.phone.strip() == "" or
                account.vorwahl.strip() == "" or
                account.nname.strip() == "" or
                account.email.strip() == "" or
                account.vname.strip() == ""):
                self.redirect(self.url(self.context, 'edit_account'))

    @property
    def _categories(self):
        for cat in natsorted(self.request.principal.getCategory(),
                          key=lambda x: x.getName()):
            name = cat.getName()
            form = getMultiAdapter((self.context, self.request), Interface,
                                   name=name.lower() + 'form')
            form.update()
            form.updateForm()

            yield {
                'name': name,
                'doc': cat.getDoc(),
                'desc': form._iface.getTaggedValue('descr'),
                'infolink': form._iface.getTaggedValue('infolink'),
                'url': '%s/%sform' % (self.application_url(), name.lower()),
                'vouchers': self.request.principal.getVouchersList(),
                'form': form,
                }


class AdminRootIndex(uvclight.Page):
    uvclight.name('index')
    uvclight.layer(IAdminLayer)
    uvclight.context(AdminRoot)
    require('display.vouchers')

    template = uvclight.get_template('adminroot.cpt', __file__)

    def update(self):
        ukhvouchers.need()

    @cached(cache, marshaller=principal_marshaller)
    def getAdrActions(self, principal):
        rc = []
        adr = principal.getAddress()

        address = {
            'name1': adr.name1,
            'name2': adr.name2,
            'name3': adr.name3,
            'street': adr.street,
            'number': adr.number,
            'zip_code': adr.zip_code,
            'city': adr.city,
            }

        oid = principal.oid
        if not adr or isinstance(adr, (models.AddressTraeger, models.AddressEinrichtung)):
            rc.append(
                    HTML.tag(
                        'a',
                        href="%s/addresses/add?form.field.oid=%s&form.field.mnr=%s" % (self.application_url(), oid, adr.mnr),
                        c="Neue Adresse anlegen",)
                    )
        elif isinstance(adr, models.Address):
            rc.append(
                    HTML.tag(
                        'a',
                        href="%s/addresses/%s/edit" % (self.application_url(), oid),
                        c="Adresse bearbeiten",)
                    )
        return address, rc

    def getAccountActions(self, account):
        rc = []
        oid = self.request.principal.oid
        rc.append(
                HTML.tag(
                    'a',
                    href="%s/accounts/add?form.field.oid=%s" % (self.application_url(), oid),
                    c="Neuen Benutzer anlegen",)
                )
        if not account:
            rc.append(
                    HTML.tag(
                        'a',
                        href="%s/accounts/add" % self.application_url(),
                        c="Neuen Benutzer anlegen",)
                    )
        return rc

    def getCatActions(self):
        rc = []
        oid = self.request.principal.oid
        session = get_session('ukhvoucher')
        category = session.query(models.Category).get(oid)
        if category:
            rc.append(
                    HTML.tag(
                        'a',
                        href="%s/categories/%s/edit" % (self.application_url(), oid),
                        c="Kontingente bearbeiten",)
                    )
        else:
            rc.append(
                    HTML.tag(
                        'a',
                        href="%s/categories/add?form.field.oid=%s" % (self.application_url(), oid),
                        c="Neue Kontingente anlegen",)
                    )
        return rc

    def getVoucherActions(self):
        rc = []
        oid = self.request.principal.oid
        rc.append(
                HTML.tag(
                    'a',
                    href="%s/account/%s/ask.vouchers" % (self.application_url(), oid),
                    c=u"Zusätzliche Berechtigungsscheine erzeugen",)
                )
        rc.append(
                HTML.tag(
                    'a',
                    href="%s/account/%s/disable.vouchers" % (self.application_url(), oid),
                    c=u"Berechtigungsscheine sperren",)
                )
        rc.append(
                HTML.tag(
                    'a',
                    href="%s/account/%s/disable.charge" % (self.application_url(), oid),
                    c=u"Charge sperren",)
                )
        return rc


class ContainerIndex(uvclight.Page):
    uvclight.name('index')
    uvclight.layer(IAdminLayer)
    uvclight.context(IModelContainer)
    require('manage.vouchers')

    template = uvclight.get_template('container.cpt', __file__)
    batching = uvclight.get_template('batch.pt', __file__)

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

    def batch_elements(self):
        return list(self.context)

    def set_batch(self):
        self.batcher = Batcher(self.context, self.request, size=50)
        elements = self.batch_elements()
        if elements:
            self.batcher.update(elements)
            self.dichotomy = get_dichotomy_batches(
                self.batcher.batch.batches,
                self.batcher.batch.total,
                self.batcher.batch.number)
            self.batch = self.batching.render(
                self, **self.namespace())
        else:
            self.batch = u''

    def update(self):
        ukhvouchers.need()
        ukhcss.need()
        self.columns = [field.title for field in self.context.listing_attrs]
        self.set_batch()

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
        ukhvouchers.need()
        session = get_session('ukhvoucher')
        self.entries = session.query(JournalEntry)


class InvoicesView(uvclight.Page):
    uvclight.name('index')
    uvclight.context(models.Invoices)
    uvclight.layer(IAdminLayer)
    require('manage.vouchers')
    template = uvclight.get_template('invoices_view.cpt', __file__)

    def getInvoices(self):
        invoices = [x for x in self.context]
        invoices.reverse()
        return invoices

    def reverseVouchers(self, vouchers):
        vl = [x for x in vouchers]
        return sorted(vl, key=lambda k: k.oid)

