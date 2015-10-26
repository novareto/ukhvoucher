# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de

from ul.auth import Principal
from ukhvoucher import models
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
                    cat.add('kat1')
                if category.kat2:
                    cat.add('kat2')
                if category.kat3:
                    cat.add('kat3')
                if category.kat4:
                    cat.add('kat4')
                if category.kat5:
                    cat.add('kat5')
                return cat
            return createCategory(category)
        else:  # LEGACY
            pass
