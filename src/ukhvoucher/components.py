# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de

from ul.auth import Principal
from ukhvoucher import models
from ukhvoucher.interfaces import IKG1, IKG2, IKG3
from cromlech.sqlalchemy import get_session


class ExternalPrincipal(Principal):

    def getAddress(self):
        session = get_session('ukhvoucher')
        address = session.query(models.Address).get(self.id)
        if address:
            return address
        else:  # LEGACY
            pass

    def getCategory(self):
        session = get_session('ukhvoucher')
        category = session.query(models.Category).get(self.id)
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
                    cat.add('kat4')
                if category.kat5:
                    cat.add('kat5')
                return cat
            return createCategory(category)
        else:  # LEGACY
            pass

    def getVouchers(self, cat=None):
        session = get_session('ukhvoucher')
        query = session.query(models.Voucher).filter(
            models.Voucher.user_id == self.id)
        if cat:
            query = query.filter(models.Voucher.cat == cat)
        return query.all()
