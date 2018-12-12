# -*- coding: utf-8 -*-

import uvclight

from math import ceil
from urllib import urlencode

from GenericCache.GenericCache import GenericCache
from cromlech.sqlalchemy import get_session
from dolmen.location import get_absolute_url
from natsort import natsorted
from profilehooks import profile
from sqlalchemy import inspect
from ukhvoucher import models
from ul.auth import require
from webhelpers.html.builder import HTML
from zope.component import getMultiAdapter
from zope.component.hooks import getSite
from zope.i18n import translate
from zope.interface import Interface
from zope.location import ILocation, LocationProxy

from ..apps import AdminRoot, UserRoot
from ..components import cached
from ..interfaces import IAdminLayer, IUserLayer, K10
from ..interfaces import IModelContainer, get_oid, get_journal_entry_title
from ..models import JournalEntry
from ..resources import ukhcss
from ..resources import ukhvouchers, masked_input
from .batch import get_dichotomy_batches
from .ffw import getData, getKto


cache = GenericCache(maxsize=5000)


def principal_marshaller(func, view, principal):
    return repr((func.__name__, view.__name__, principal.oid))


class SearchUnternehmen(uvclight.JSON):
    uvclight.name('search_unternehmen')
    uvclight.layer(IAdminLayer)
    uvclight.context(Interface)
    require('display.vouchers')
    #require('manage.vouchers')

    #@profile
    def update(self):
        self.term = self.request.form['term']
        self.vocabulary = get_oid(self.context)

    #@profile
    def render(self):
        terms = []
        matcher = self.term.lower()
        for item in self.vocabulary:
            if matcher in item.title.lower():
                terms.append({'id': item.token, 'text': item.title})
        return {'q': self.term, 'results': terms}


class UserRootIndexBase(object):

    template = uvclight.get_template('userroot.cpt', __file__)

    def get_principal(self):
        return self.request.principal
    
    def update(self):
        ukhvouchers.need()

        self.categories = self._categories

        self.principal = self.get_principal()
        self.address = self.principal.getAddress()
        self.vouchers = self.principal.getVouchers
        self.raw_categories = self.principal.getCategory()

        if K10 in self.raw_categories:
            self.redirect(self.url(self.context, 'ffwform'))

    @property
    def _categories(self):
        for cat in natsorted(self.raw_categories,
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
                'vouchers': self.vouchers(),
                'form': form,
                }


class UserRootIndex(uvclight.Page, UserRootIndexBase):
    uvclight.name('index')
    uvclight.layer(IUserLayer)
    uvclight.context(UserRoot)
    require('users.access')

    template = uvclight.get_template('userroot.cpt', __file__)

    def update(self):
        super(UserRootIndex, self).update()
        UserRootIndexBase.update(self)
        account = self.principal.getAccount()
        if account:
            if (account.phone.strip() == "" or
                account.vorwahl.strip() == "" or
                account.nname.strip() == "" or
                account.email.strip() == "" or
                account.vname.strip() == ""):
                self.redirect(self.url(self.context, 'edit_account'))


class AdminRootIndex(uvclight.Page):
    uvclight.name('index')
    uvclight.layer(IAdminLayer)
    uvclight.context(AdminRoot)
    require('display.vouchers')

    template = uvclight.get_template('adminroot.cpt', __file__)

    def update(self):
        ukhvouchers.need()

    def getFFWData(self):
        oid = self.request.principal.oid
        data = None
        from ukhvoucher.vocabularies import get_selected_abrechungszeitraum
        zeitraum = get_selected_abrechungszeitraum()
        budget = getData(oid, zeitraum.von)
        if budget:
            kto = getKto(oid)
            betrag = budget.budget
            restbudget = budget.budget_vj
            zahlbetrag = betrag - restbudget
            betrag = "%0.2f" % float(betrag)
            restbudget = "%0.2f" % float(restbudget)
            zahlbetrag = "%0.2f" % float(zahlbetrag)
            data = {
                'zahlbetrag': zahlbetrag,
                'kontoinhaber': kto.kto_inh,
                'last_budget': restbudget,
                'einsatzkraefte': budget.einsatzk,
                'datum': budget.datum,
                'betrag': betrag,
                'iban': kto.iban,
                'verw_zweck': kto.verw_zweck,
                'betreuer': budget.jugendf,
                'grund': budget.grund,
                'bank': kto.bank}
        return data

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
        return rc

    def getCatActions(self):
        rc = []
        oid = self.request.principal.oid
        session = get_session('ukhvoucher')
        category = session.query(models.Category).get(str(oid))
        if category:
            rc.append(HTML.tag(
                'a',
                href="%s/categories/%s/edit" % (
                    self.application_url(), oid),
                c="Kontingente bearbeiten",)
            )
        else:
            rc.append(HTML.tag(
                'a',
                href="%s/categories/add?form.field.oid=%s" % (
                    self.application_url(), oid),
                c="Neue Kontingente anlegen",)
            )
        return rc

    def getVoucherActions(self):
        rc = []
        oid = self.request.principal.oid
        rc.append(HTML.tag(
            'a',
            href="%s/account/%s/ask.vouchers" % (
                self.application_url(), oid),
            c=u"Zusätzliche Berechtigungsscheine erzeugen",)
        )
        rc.append(HTML.tag(
            'a',
            href="%s/account/%s/disable.vouchers" % (
                self.application_url(), oid),
            c=u"Berechtigungsscheine sperren",)
        )
        rc.append(HTML.tag(
            'a',
            href="%s/account/%s/disable.charge" % (
                self.application_url(), oid),
            c=u"Charge sperren",)
        )
        return rc

    def getJournalEntryTitle(self, entry):
        return get_journal_entry_title(entry)



def safe_str(v):
    if isinstance(v, str):
        return v
    elif isinstance(v, unicode):
        return v.encode('utf-8')
    else:
        raise TypeError("Can't urlencode param %s" % v)


def flatten_params(params):
    for k, v in params.items():
        if isinstance(v, (str, unicode)):
           yield k, v
        else:
            try:
                iterator = iter(v)
                for i in iterator:
                        yield k, i
            except TypeError:
                yield k, str(v)


class Batch(object):

    prefix = 'batch'

    def __init__(self, context, request, results=None, length=None, size=10):
        self.context = context
        self.request = request

        if results is None:
            results = self.context
        self.results = results
        if length is None:
            length = len(self.results)
        self.length = length
        self.size = size
        self.current = 1

    def update(self):
        self.pages = int(ceil(float(self.length) / self.size))
        self.current = int(self.request.form.get(
            self.prefix + '.page', self.current))

    def get_elements(self):
        start = (self.current - 1) * self.size
        if isinstance(self.results, (list, tuple)):
            return self.results[start:start+self.size]
        return list(self.results.slice(start, self.size))

    def batch_url(self, page):
        param = self.prefix + ".page"
        params = [(k, safe_str(v))
                  for k, v in flatten_params(self.request.form)
                  if k not in (param,)]
        params.append((param, page))
        return '?' + urlencode(params)

    def batches(self):
        if not ILocation.providedBy(self.results):
            url = get_absolute_url(self.context, self.request)
        else:
            url = get_absolute_url(self.results, self.request)
        for page in xrange(1, self.pages + 1):
            if page == self.current:
                current = True
            else:
                current = False
            yield {
                'current': current,
                'id': page,
                'url': url + self.batch_url(page),
                }

    def dichotomy(self):
        url = get_absolute_url(self.results, self.request)
        start = self.current * self.size
        for type, value in get_dichotomy_batches(self.pages, start):
            yield {
                'current': type == 'current',
                'id': value,
                'url': value and (url + self.batch_url(value)) or None,
                }


class ContainerIndex(uvclight.Page):
    uvclight.name('index')
    uvclight.layer(IAdminLayer)
    uvclight.context(IModelContainer)
    require('manage.vouchers')

    template = uvclight.get_template('container.cpt', __file__)
    batching = uvclight.get_template('batch.pt', __file__)
    results = None

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
                    'link': (
                        col.identifier == self.context.pkey
                        and itemurl or '')}]

    def update(self):
        ukhvouchers.need()
        ukhcss.need()
        self.columns = [field.title for field in self.context.listing_attrs]
        if self.results == []:
            self.results = None
        self.batcher = Batch(
            self.context, self.request, results=self.results, size=100)
        self.batcher.update()
        self.batch = self.batching.render(self, **{'batch': self.batcher})

    def relation(self, id, value):
        site = getSite()
        if id == 'vouchers':
            baseurl = self.url(site) + '/vouchers/'
            for voucher in value:
                yield voucher, baseurl + str(voucher.oid)


class InvoicesView(uvclight.Page):
    uvclight.name('index')
    uvclight.context(models.Invoices)
    uvclight.layer(IAdminLayer)
    require('manage.vouchers')
    template = uvclight.get_template('invoices_view.cpt', __file__)

    def getInvoices(self):
        invoices = [x for x in self.context]
        return invoices

    def reverseVouchers(self, vouchers):
        vl = [x for x in vouchers]
        return sorted(vl, key=lambda k: k.oid, reverse=True)


class JournalView(uvclight.Page):
    uvclight.name('index')
    uvclight.context(models.Journal)
    uvclight.layer(IAdminLayer)
    require('manage.vouchers')
    template = uvclight.get_template('journal.cpt', __file__)

    @property
    def entries(self):
        return [x for x in self.context]


class Helper(uvclight.Page):
    uvclight.context(Interface)
    require('manage.vouchers')

    def render(self):
        session = get_session('ukhvoucher')
        from ukhvoucher import models
        from ukhvoucher import MANUALLY_CREATED
        query = session.query(models.Voucher).filter(
            models.Voucher.generation_id == models.Generation.oid,
            models.Generation.data == '"Manuelle Erzeugung"')
        for v in query.all():
            v.status = MANUALLY_CREATED


class Migration(uvclight.Page):
    uvclight.context(Interface)
    require('manage.vouchers')

    def render(self):
        session = get_session('ukhvoucher')
        from ukhvoucher import models
        query = session.query(models.Address, models.Account).filter(models.Address.oid == models.Account.oid)
        print "Migration User"
        #print query.count()
        #for adr, account in query.all():
        #    adr.user_login = int(account.login)
        #    adr.user_az = account.az
        #    adr.user_id = account.oid
        #    print adr
        print "Migration der Gutscheine"
        #session.flush()
        #query = session.query(models.Voucher, models.Account).filter(models.Voucher.user_id == models.Account.oid)
        #print query.count()
        #for vou, account in query.all():
        #    vou.user_login = int(account.login)
        #    vou.user_az = account.az
        print "Migration FWBudget Datum"
        #query = session.query(models.FWBudget)
        #for budget in query.all():
        #    dd = budget.datum
        #    budget.datum = "%s-%s-%s" %(dd[6:10], dd[3:5], dd[0:2])
        #import pdb; pdb.set_trace()
        print "Zuordnugn Datum"
        #query = session.query(models.Voucher, models.JournalEntry).filter(
        #        models.JournalEntry.oid == models.Voucher.invoice_id,
        #        models.Voucher.status == "gebucht",
        #        models.JournalEntry.action == 'Neue Zuordnung angelegt')
        #i = 1
        #for vou, je in query.all():
        #    vou.modification_date = je.date

        # Zuordnungen DAtuem
        #query = session.query(models.Voucher, models.JournalEntry).filter(
        #        models.JournalEntry.oid == models.Voucher.invoice_id,
        #        models.Voucher.status == "gebucht",
        #        models.JournalEntry.action == 'Zuordnung')
        #i = 1
        #for vou, je in query.all():
        #    vou.modification_date = je.date
        #    i += 1
        # Zuordnungen DAtuem
        #query = session.query(models.Voucher, models.JournalEntry).filter(
        #        models.JournalEntry.oid == models.Voucher.user_id,
        #        models.Voucher.status == "ungültig",
        #        models.JournalEntry.action.like('%Berechtigungsscheine gesperrt%'))
        #i = 1
        #for vou, je in query.all():
        #    vou.modification_date = je.date
        #    i += 1
        #print i
        from datetime import datetime
        #query = session.query(models.Voucher).filter( models.Voucher.status == "ungültig", models.Voucher.modification_date==datetime(2018,12,10))
        #print query.count()
        #for vou in query.all():
        #    vou.modification_date = vou.creation_date 
        query = session.query(models.Voucher).filter( models.Voucher.status == "erstellt", models.Voucher.modification_date==datetime(2018,12,10))
        print query.count()
        for vou in query.all():
            vou.modification_date = vou.creation_date 
        #print i
        #a.close()
