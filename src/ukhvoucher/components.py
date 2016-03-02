# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de

from ul.auth import Principal
from ukhvoucher import models, log
from ukhvoucher.interfaces import IKG1, IKG2, IKG3, IKG4, IKG5, IKG6, IKG7, IKG8, IKG9
from cromlech.sqlalchemy import get_session
from sqlalchemy import and_
from plone.memoize import ram
from ordered_set import OrderedSet


def _render_details_cachekey(method, oid):
    return (oid, method.__name__)


def log(m):
    print m


class ExternalPrincipal(Principal):

    permissions = frozenset(('users.access',))
    roles = frozenset()

    def __init__(self, id, title=u''):
        self.id = id

    @property
    def title(self):
        adr = self.getAddress()
        return "%s %s" %(adr.name1, adr.name2)

    @property
    def oid(self):
        account = self.getAccount()
        return int(account.oid)

    @property
    def merkmal(self):
        account = self.getAccount()
        if not account and not account.merkmal:
            return "M"
        return str(account.merkmal).strip()

    def getAccount(self):
        session = get_session('ukhvoucher')
        account = session.query(models.Account).filter(and_(models.Account.login==self.id, models.Account.az=="eh"))
        return account.one()

    def getAddress(self):
        session = get_session('ukhvoucher')
        address = session.query(models.Address).get(str(self.oid))
        if address:
            return address
        @ram.cache(_render_details_cachekey)
        def getSlowAdr(oid):
            print "ADR FROM CAHCE"
            address = session.query(models.AddressTraeger).get(oid)
            if address:
                return address
            address = session.query(models.AddressEinrichtung).get(oid)
            if address:
                return address
        return getSlowAdr(self.oid)

    def getCategory(self):
        session = get_session('ukhvoucher')
        category = session.query(models.Category).get(self.oid)
        if category:
            def createCategory(category):
                cat = OrderedSet()
                if category.kat1:
                    cat.add(IKG1)
                if category.kat2:
                    cat.add(IKG2)
                if category.kat3:
                    cat.add(IKG3)
                if category.kat4:
                    cat.add(IKG4)
                if category.kat5:
                    cat.add(IKG5)
                if category.kat6:
                    cat.add(IKG6)
                if category.kat7:
                    cat.add(IKG7)
                if category.kat8:
                    cat.add(IKG8)
                if category.kat9:
                    cat.add(IKG9)
                return cat
            return createCategory(category)
        else:
            mnr = self.getAddress().mnr
            return self.getCategoryFromMNR(mnr)
        return []

    def sql_base(self, enrea1, enrea2):
        session = get_session('ukhvoucher')
        sql = """SELECT  TRGMNR FROM tstcusadat.mitrg1aa a, tstcusadat.mienr1aa b
        WHERE A.TRGRCD = b.Enroid
        and a.trgbv in(1, 3) and substr(a.trgmnr, 3, 2) in(10, 30)
        and b.enrea1  in(%s) and b.enrea2 in(%s)""" % (enrea1, enrea2)
        res = session.execute(sql).fetchall()
        return [x[0].strip() for x in res]

    def sql_schulen(self, enrea1, enrea2):
        session = get_session('ukhvoucher')
        sql = """SELECT  TRGMNR FROM tstcusadat.mitrg1aa a, tstcusadat.mienr1aa b
        WHERE A.TRGRCD = b.Enroid
        and b.enrea1  in(%s) and b.enrea2 in(%s) and b.enrea3 = 'N'""" % (enrea1, enrea2)
        res = session.execute(sql).fetchall()
        return [x[0].strip() for x in res]

    def getCategoryFromMNR(self, mnr):
        origmnr = mnr.strip()
        mnr = mnr[:4]
        cat = OrderedSet()
        if mnr in ('1.02', '1.03', '1.04'):
            cat = OrderedSet([IKG1, IKG2, IKG3, IKG4, IKG5, IKG6, IKG9])
        elif mnr == '1.05':
            cat = OrderedSet([IKG1, IKG2])
        elif mnr in ('1.10', '1.30', '3.10'):
            if origmnr in self.sql_base('2', '1,2,3,4'):
                log('%s entsorgungsbetrieb' % origmnr)
                cat = OrderedSet([IKG2, IKG4])
            elif origmnr in self.sql_base('2', '5,6,7'):
                log('%s abwasserbetrieb' % origmnr)
                cat = OrderedSet([IKG2, IKG6])
            elif origmnr in self.sql_base('1', '1,2,3,4,5,6,7,8'):
                log('%s Gesundheitsdienst' % origmnr)
                cat = OrderedSet([IKG2,])
            elif origmnr in self.sql_base('2', '7'):
                log('%s Gas und Wasserversorgung' % origmnr)
                cat = OrderedSet([IKG2,])
            elif origmnr in self.sql_base('3', '6'):
                log('%s Beschaeftigungsgesellschaften' % origmnr)
                cat = OrderedSet([IKG2,])
            elif origmnr in self.sql_base('4', '1,2,3,4,5,6'):
                log('%s Bauwesen' % origmnr)
                cat = OrderedSet([IKG2,])
            elif origmnr in self.sql_base('5', '2,3,4'):
                log('%s Landwirtschaft' % origmnr)
                cat = OrderedSet([IKG2,])
            elif origmnr in self.sql_base('6', '1,2,3,4,5'):
                log('%s Kulturelle Einrichtungen' % origmnr)
                cat = OrderedSet([IKG2,])
            elif origmnr in self.sql_base('8', '1,2,3,4,5,6'):
                log('%s Verkehrsunternehmen' % origmnr)
                cat = OrderedSet([IKG2,])
            elif origmnr in self.sql_base('9', '4'):
                log('%s Forschungseinrichtungen' % origmnr)
                cat = OrderedSet([IKG2,])
            elif origmnr in self.sql_base('7', '1'):
                log('%s Feuerwehrvereine' % origmnr)
                cat = OrderedSet([])
            else:
                cat = OrderedSet([IKG1,])
        elif mnr in ('2.10.64/00005', '2.10.34/00005', '2.10.65/00010'):
            cat = OrderedSet([IKG2, ])
        elif mnr in ('1.20'):
            cat = OrderedSet([IKG1, ])
        elif self.sql_schulen('3','2'):
            log('%s Schule' % origmnr)
            cat = OrderedSet([IKG7, ])
        return cat

    def getVouchers(self, cat=None):
        session = get_session('ukhvoucher')
        query = session.query(models.Voucher).filter(
            models.Voucher.user_id == self.oid)
        if cat:
            query = query.filter(models.Voucher.cat == cat)
        return query.all()


class AdminPrincipal(ExternalPrincipal):

    permissions = frozenset(('manage.vouchers',))
    roles = frozenset()

    def __init__(self, id, masquarade):
        self.id = id
        self.masquarade = masquarade

    @property
    def oid(self):
        return self.masquarade

    @property
    def title(self):
        return "Administrator"

    def getAccount(self):
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

