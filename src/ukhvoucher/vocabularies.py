# -*- coding: utf-8 -*-

import grokcore.component as grok
from sqlalchemy import distinct
from . import VOCABULARIES, DISABLED, BOOKED
from .models import Account, Invoice, Voucher, Address
from cromlech.sqlalchemy import get_session
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.interface import provider
from zope.schema.interfaces import IContextAwareDefaultFactory


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
    if isinstance(context, Address):
        query = query.filter(Voucher.user_id==context.oid)
    for item in query.all():
        items.append(SimpleTerm(item, token=item.oid, title="%s - %s" %(item.title, item.status.strip())))
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
    print "i am called"
    session = get_session('ukhvoucher')
    from sqlalchemy.sql.functions import max
    oid = int(session.query(max(Account.login)).one()[0]) + 1
    return unicode(oid)


VOCABULARIES['accounts'] = accounts
VOCABULARIES['invoices'] = invoices
VOCABULARIES['vouchers'] = vouchers
VOCABULARIES['all_vouchers'] = all_vouchers
VOCABULARIES['addresses'] = addresses
VOCABULARIES['categories'] = categories
VOCABULARIES['account'] = getNextID
