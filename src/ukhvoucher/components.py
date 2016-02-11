# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de

from ul.auth import Principal
from ukhvoucher import models
from ukhvoucher.interfaces import IKG1, IKG2, IKG3, IKG4, IKG5, IKG6, IKG7
from cromlech.sqlalchemy import get_session
from sqlalchemy import and_


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
        account = session.query(models.Account).filter(and_(models.Account.login==self.id, models.Account.az=="00"))
        return account.one()

    def getAddress(self):
        session = get_session('ukhvoucher')
        address = session.query(models.Address).get(self.oid)
        if address:
            return address
        address = session.query(models.AddressTraeger).get(self.oid)
        if address:
            return address
        address = session.query(models.AddressEinrichtung).get(self.oid)
        if address:
            return address

    def getCategory(self):
        session = get_session('ukhvoucher')
        category = session.query(models.Category).get(self.oid)
        if category:
            def createCategory(category):
                cat = set()
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
                return cat
            return createCategory(category)
        else:  # LEGACY
            ##################################################import pdb; pdb.set_trace()
            mnr = self.getAddress().mnr
            return self.getCategoryFromMNR(mnr)
        return []

    def getCategoryFromMNR(self, mnr):
        mnr = mnr[:4]
        cat = set()
        if mnr in ('1.02', '1.03', '1.04'):
            cat = set([IKG1, IKG2, IKG3, IKG4, IKG5, IKG6])
        elif mnr == '1.05':
            cat = set([IKG1, IKG2])
        elif mnr == "Abwasserverband":
            cat = set([IKG1, IKG2, IKG3, IKG4, IKG5, IKG6])
        elif mnr == "Freie KITA":
            cat = set([IKG1, IKG2, IKG3, IKG4, IKG5, IKG6])
        elif mnr == "Staatstehater":
            cat = set([IKG1, IKG2, IKG3, IKG4, IKG5, IKG6])
        elif mnr == "Entsorgungsbetrieb":
            cat = set([IKG1, IKG2, IKG3, IKG4, IKG5, IKG6])
        elif mnr == "Schule":
            cat = set([IKG1, IKG2, IKG3, IKG4, IKG5, IKG6])
        elif mnr == "Gemeinsahftskasse":
            cat = set([IKG1, IKG2, IKG3, IKG4, IKG5, IKG6])
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
        accounts = session.query(models.Account).filter(models.Account.oid==self.oid)
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

