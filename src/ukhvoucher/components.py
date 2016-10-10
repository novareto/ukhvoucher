# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de

from GenericCache.GenericCache import GenericCache, default_marshaller
from collections import namedtuple
from cromlech.sqlalchemy import get_session
from ordered_set import OrderedSet
from plone.memoize import ram
from profilehooks import profile
from sqlalchemy import and_
from ukhvoucher import models, log
from ukhvoucher.interfaces import K1, K2, K3, K4, K5, K6, K7, K8, K9, K10, K11
from ul.auth import Principal

from .caching_query import FromCache, RelationshipCache
from .interfaces import IAccount, IVoucher
from .models import get_ukh_config

TABLENAMES = get_ukh_config()

principal_cache = GenericCache(maxsize=5000)


def _render_details_cachekey(method, oid):
    return (oid, method.__name__)


def _render_account_cachekey(method, self, *args, **kwargs):
    return (self.id, method.__name__)


def log(m):
    pass


class NoMarshallError(Exception):
    """Exception: we don't know how to marshall.
    """


def cached(cache, marshaller=default_marshaller):
    def decorator(func):
        def inner(*args, **kwargs):
            try:
                key = marshaller(func, *args, **kwargs)
                return cache.fetch_with_generator(key, func, *args, **kwargs)
            except NoMarshallError:
                return func(*args, **kwargs)
        return inner
    return decorator


def principal_marshaller(func, principal):
    return repr((func.__name__, principal.id))


def vouchers_marshaller(func, principal, cat=None):
    return repr((func.__name__, principal.id, cat))


class ExternalPrincipal(Principal):

    permissions = frozenset(('users.access',))
    roles = frozenset()
    info_factory = namedtuple('AccountInfo', list(IAccount))
    voucher_factory = namedtuple('VoucherInfo', list(IVoucher))

    def __init__(self, id, title=u''):
        self.id = id

    @property
    def title(self):
        adr = self.getAddress()
        return "%s %s" %(adr.name1, adr.name2)

    @property
    def oid(self):
        account = self.getAccountInfo()
        return int(account.oid)

    @property
    def merkmal(self):
        account = self.getAccount()
        if not account and not account.merkmal:
            return "M"
        return str(account.merkmal).strip()

    @cached(principal_cache, marshaller=principal_marshaller)
    def getAccountInfo(self):
        account = self.getAccount()
        fields = [getattr(account, field) for field in list(IAccount)]
        return self.info_factory(*fields)

    def getAccount(self, invalidate=False):
        session = get_session('ukhvoucher')
        account = session.query(models.Account).options(
            FromCache("default")).filter(
                and_(models.Account.login==self.id, models.Account.az=="eh"))
        if invalidate:
            print "INVALIDATE"
            account.invalidate()
        return account.one()

    def getAddress(self):
        session = get_session('ukhvoucher')
        address = session.query(models.Address).options(
            FromCache("default")).get(str(self.oid))
        if address:
            return address
        @ram.cache(_render_details_cachekey)
        def getSlowAdr(oid):
            address = session.query(models.AddressTraeger).options(
            FromCache("default")).get(oid)
            if address:
                return address
            address = session.query(models.AddressEinrichtung).options(
            FromCache("default")).get(oid)
            if address:
                return address
        return getSlowAdr(self.oid)

    def getCategory(self, invalidate=False):
        session = get_session('ukhvoucher')
        if invalidate:
            session.query(models.Category).options(FromCache("default")).filter(models.Category.oid == self.oid).invalidate()
        category = session.query(models.Category).options(
            FromCache("default")).get(self.oid)
        if category:
            def createCategory(category):
                cat = OrderedSet()
                if category.kat1:
                    cat.add(K1)
                if category.kat2:
                    cat.add(K2)
                if category.kat3:
                    cat.add(K3)
                if category.kat4:
                    cat.add(K4)
                if category.kat5:
                    cat.add(K5)
                if category.kat6:
                    cat.add(K6)
                if category.kat7:
                    cat.add(K7)
                if category.kat8:
                    cat.add(K8)
                if category.kat9:
                    cat.add(K9)
                if category.kat10:
                    cat.add(K10)
                if category.kat11:
                    cat.add(K11)
                return cat
            return createCategory(category)
        else:
            mnr = self.getAddress().mnr
            return self.getCategoryFromMNR(mnr)
        return []

    def sql_base(self, enrea1, enrea2):
        umgebung = TABLENAMES['sqlbase']
        session = get_session('ukhvoucher')
        if umgebung == 'test':
            sql = """SELECT  TRGMNR FROM tstcusadat.mitrg1aa a, tstcusadat.mienr1aa b
            WHERE A.TRGRCD = b.Enroid
            and a.trgbv in(1, 3) and substr(a.trgmnr, 3, 2) in(10, 30)
            and b.enrea1  in(%s) and b.enrea2 in(%s)""" % (enrea1, enrea2)
        if umgebung == 'prod':
            sql = """SELECT  TRGMNR FROM educusadat.mitrg1aa a, educusadat.mienr1aa b
            WHERE A.TRGRCD = b.Enroid
            and a.trgbv in(1, 3) and substr(a.trgmnr, 3, 2) in(10, 30)
            and b.enrea1  in(%s) and b.enrea2 in(%s)""" % (enrea1, enrea2)
        res = session.execute(sql).fetchall()
        return [x[0].strip() for x in res]

    def sql_schulen(self, enrea1, enrea2):
        umgebung = TABLENAMES['sqlbase']
        session = get_session('ukhvoucher')
        if umgebung == 'test':
            sql = """SELECT  TRGMNR FROM tstcusadat.mitrg1aa a, tstcusadat.mienr1aa b
            WHERE A.TRGRCD = b.Enroid
            and b.enrea1  in(%s) and b.enrea2 in(%s) and b.enrea3 = 'N'""" % (enrea1, enrea2)
        if umgebung == 'prod':
            sql = """SELECT  TRGMNR FROM educusadat.mitrg1aa a, educusadat.mienr1aa b
            WHERE A.TRGRCD = b.Enroid
            and b.enrea1  in(%s) and b.enrea2 in(%s) and b.enrea3 = 'N'""" % (enrea1, enrea2)
        res = session.execute(sql).fetchall()
        return [x[0].strip() for x in res]

    def getCategoryFromMNR(self, mnr):
        origmnr = mnr.strip()
        mnr = mnr[:4]
        cat = OrderedSet()
        if mnr in ('1.02', '1.03', '1.04'):
            cat = OrderedSet([K1, K2, K3, K4, K6, K9, K10])
        elif mnr == '1.05':
            cat = OrderedSet([K1, K2, K6, K8, K9])
        elif mnr == '1.11':
            if origmnr == '1.11.60/00007':
                cat = OrderedSet([K6,])
            else:
                cat = OrderedSet([K2,])
        elif mnr in ('1.10', '1.30', '3.10'):
            if origmnr in self.sql_base('2', '1,2,3,4'):
                log('%s entsorgungsbetrieb' % origmnr)
                cat = OrderedSet([K2, K4])
            elif origmnr in self.sql_base('2', '5,6,7'):
                log('%s abwasserbetrieb' % origmnr)
                cat = OrderedSet([K2, K6])
            elif origmnr in self.sql_base('1', '1,2,3,4,6,7,8'):
                log('%s Gesundheitsdienst' % origmnr)
                cat = OrderedSet([K11,])
            elif origmnr in self.sql_base('2', '7'):
                log('%s Gas und Wasserversorgung' % origmnr)
                cat = OrderedSet([K2, K6])
            elif origmnr in self.sql_base('3', '6'):
                log('%s Beschaeftigungsgesellschaften' % origmnr)
                cat = OrderedSet([K2,])
            elif origmnr in self.sql_base('4', '1,2,3,4,5,6'):
                log('%s Bauwesen' % origmnr)
                cat = OrderedSet([K2,])
            elif origmnr in self.sql_base('5', '2,4'):
                log('%s Landwirtschaft' % origmnr)
                cat = OrderedSet([K2,])
            elif origmnr in self.sql_base('6', '1,2,4,5,9'):
                log('%s Kulturelle Einrichtungen' % origmnr)
                cat = OrderedSet([K2,])
            elif origmnr in self.sql_base('8', '1,2,3,4,5,6'):
                log('%s Verkehrsunternehmen' % origmnr)
                cat = OrderedSet([K2,])
            elif origmnr in self.sql_base('9', '4'):
                log('%s Forschungseinrichtungen' % origmnr)
                cat = OrderedSet([K2,])
            elif origmnr in self.sql_base('7', '1'):
                log('%s Feuerwehrvereine' % origmnr)
                cat = OrderedSet([])
            else:
                cat = OrderedSet([K1,])
        elif mnr in ('2.10.64/00005', '2.10.34/00005', '2.10.65/00010'):
            cat = OrderedSet([K2, ])
        elif mnr in ('2.10.61/00002'):
            cat = OrderedSet([K5, ])
        elif mnr in ('1.20'):
            cat = OrderedSet([K1, ])
        elif mnr in ('3.2.', '3.3.'):
            self.sql_schulen('3','2')
            log('%s Schule' % origmnr)
            cat = OrderedSet([K7, ])
        return cat

    def getVouchers(self, cat=None, invalidate=False):
        print "getVouchers", cat
        session = get_session('ukhvoucher')
        #query = session.query(models.Voucher).options(
        #    FromCache("default")).filter(models.Voucher.user_id == self.oid)
        query = session.query(models.Voucher).filter(models.Voucher.user_id == self.oid)
        if cat:
            query = query.filter(models.Voucher.cat == cat)
        #if invalidate:
        #    print "INVALIDATE"
        #    query.invalidate()
        return query.all()


class AdminPrincipal(ExternalPrincipal):

    #permissions = frozenset(('manage.vouchers',))
    roles = frozenset()

    def __init__(self, id, masquarade, permissions):
        self.id = id
        self.masquarade = masquarade
        self.permissions = permissions

    @property
    def canEdit(self):
        return 'manage.vouchers' in self.permissions

    @property
    def oid(self):
        return self.masquarade

    @property
    def title(self):
        return "Administrator"

    def getAccount(self, invalidate=False):
        session = get_session('ukhvoucher')
        accounts = session.query(models.Account).filter(models.Account.oid==self.oid, models.Account.az == "eh")
        return accounts

    def getVouchers(self, cat=None):
        session = get_session('ukhvoucher')
        query = session.query(models.Voucher).filter(
            models.Voucher.user_id == self.oid)
        if cat:
            query = query.filter(models.Voucher.cat == cat)
        return query.all()

    def getJournalEntries(self):
        session = get_session('ukhvoucher')
        query = session.query(models.JournalEntry).filter(
            models.JournalEntry.oid == self.oid)
        return query.all()

