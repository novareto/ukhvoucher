# -*- coding: utf-8 -*-

import grokcore.component as grok
from datetime import datetime
from sqlalchemy import distinct
from . import VOCABULARIES, DISABLED, BOOKED
from .models import Account, Invoice, Voucher, Address
from cromlech.sqlalchemy import get_session
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.interface import provider
from zope.schema.interfaces import IContextAwareDefaultFactory


class MyVoc(SimpleVocabulary):

    def __init__(self, context=None):
        self.context = context

    @property
    def _terms(self):
        session = get_session('ukhvoucher')
        from ukhvoucher.models import Voucher
        rc = []
        for item in session.query(Voucher.oid).all():
            rc.append(SimpleTerm(item.oid, item.oid, item.oid))
        return rc

    def __contains__(self, value):
        session = get_session('ukhvoucher')
        from ukhvoucher.models import Voucher
        return session.query(Voucher).get(value.oid)

    def getTerm(self, term):
        session = get_session('ukhvoucher')
        from ukhvoucher.models import Voucher
        item = session.query(Voucher).get(term.oid)
        return SimpleTerm(item, token=item.oid, title="%s - %s %s" %(item.title, item.status.strip(), item.cat))

    def getTermByToken(self, token):
        session = get_session('ukhvoucher')
        from ukhvoucher.models import Voucher
        item = session.query(Voucher).get(token)
        return SimpleTerm(item, token=item.oid, title="%s - %s %s" %(item.title, item.status.strip(), item.cat))


@provider(IContextSourceBinder)
def mysource(context):
    return MyVoc(context)



@grok.provider(IContextSourceBinder)
def accounts(context):
    session = get_session('ukhvoucher')
    items = [SimpleTerm(None, None, u'Bitte auswählen')]
    for user_id in session.query(distinct(Voucher.user_id)).all():
        userid = int(user_id[0])
        items.append(SimpleTerm(int(userid), token=userid, title=userid))
    return SimpleVocabulary(items)


@grok.provider(IContextSourceBinder)
def invoices(context):
    session = get_session('ukhvoucher')
    items = [SimpleTerm(item.oid, token=item.oid, title=item.title)
             for item in session.query(Invoice).all()]
    return SimpleVocabulary(items)


@grok.provider(IContextSourceBinder)
def all_vouchers(context):
    items = [SimpleTerm(None, None, u'Bitte auswählen')]
    session = get_session('ukhvoucher')
    query = session.query(Voucher)
    for item in query.all():
        items.append(SimpleTerm(item.oid, token=item.oid, title="%s - %s" %(item.title, item.status.strip())))
    return SimpleVocabulary(items)


@grok.provider(IContextSourceBinder)
def vouchers(context):
    session = get_session('ukhvoucher')
    items = []
    disabled = set()
    query = session.query(Voucher)
    if isinstance(context, Account):
        query = query.filter(Voucher.user_id==context.oid)
    for item in query.all():
        items.append(SimpleTerm(item, token=item.oid, title="%s - %s %s" %(item.title, item.status.strip(), item.cat)))
        if item.invoice is not None or item.status.strip() in (DISABLED, BOOKED):
            disabled.add(str(item.oid))
            disabled.add(item.oid)
    vocabulary = SimpleVocabulary(items)
    vocabulary.disabled_items = disabled
    return vocabulary


@grok.provider(IContextSourceBinder)
def addresses(context):
    session = get_session('ukhvoucher')
    items = [SimpleTerm(item.oid, token=item.oid, title=item.title)
             for item in session.query(Addresses).all()]
    return SimpleVocabulary(items)


@grok.provider(IContextSourceBinder)
def categories(context):
    items = [SimpleTerm(item, token=item, title=item)
             for item in ('kat1', 'kat2', 'kat3', 'kat4')]
    return SimpleVocabulary(items)


@provider(IContextAwareDefaultFactory)
def getNextID(context):
    session = get_session('ukhvoucher')
    from sqlalchemy.sql.functions import max
    oid = int(session.query(max(Account.login)).one()[0] or 0) + 1
    return unicode(oid)


class RangeSimpleTerm(SimpleTerm):

    def __init__(self, value, token=None, title=None, von=None, bis=None):
        super(RangeSimpleTerm, self).__init__(value, token, title)
        self.von = von
        self.bis = bis


@provider(IContextAwareDefaultFactory)
def get_abrechnungszeitraum(context):
    items = [RangeSimpleTerm('ez3', 'ez3', '01.01.2021 - 31.12.2022', datetime(2021, 01, 01), datetime(2022, 12, 31)),
             RangeSimpleTerm('ez2', 'ez2', '01.01.2019 - 31.12.2020', datetime(2019, 01, 01), datetime(2020, 12, 31)),
             RangeSimpleTerm('ez1', 'ez1', '01.01.2016 - 31.12.2018', datetime(2016, 01, 01), datetime(2018, 12, 31))
             ]
    return SimpleVocabulary(items)


def get_default_abrechnungszeitraum(zeitpunkt=None):
    if not zeitpunkt:
        zeitpunkt = datetime.now()
    vocab = get_abrechnungszeitraum(None)
    for term in vocab:
        if term.von <= zeitpunkt and zeitpunkt <= term.bis:
            return term
    return None


def get_selected_abrechungszeitraum():
    from cromlech.browser import getSession
    session = getSession()
    date_range = session.get('date_range') or get_default_abrechnungszeitraum().token
    return get_abrechnungszeitraum(None).getTermByToken(date_range)


VOCABULARIES['accounts'] = accounts
VOCABULARIES['invoices'] = invoices
VOCABULARIES['vouchers'] = vouchers
VOCABULARIES['all_vouchers'] = all_vouchers
VOCABULARIES['addresses'] = addresses
VOCABULARIES['categories'] = categories
VOCABULARIES['account'] = getNextID
VOCABULARIES['mysource'] = mysource
VOCABULARIES['abrechnungszeitraum'] = get_abrechnungszeitraum
