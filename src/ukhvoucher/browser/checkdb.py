 # -*- coding: utf-8 -*-

import uvclight
from zope.interface import Interface
from ukhvoucher.models import  Voucher
from cromlech.sqlalchemy import get_session

class CheckDatabaseConnectivity(uvclight.View):
    uvclight.context(Interface)
    uvclight.name('checkdb')
    uvclight.auth.require('zope.Public')

    def render(self):
        session = get_session('ukhvoucher')
        ret = session.query(Voucher.oid)
        return str(ret.count())
