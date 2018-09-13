# -*- coding: utf-8 -*-

import uvclight
from ukhvoucher import DISABLED, BOOKED
from ukhvoucher import models
from ukhvoucher.apps import AdminRoot
from cromlech.sqlalchemy import get_session
from sqlalchemy import cast, String


class SearchJSONVouchers(uvclight.JSON):
    uvclight.context(AdminRoot)
    uvclight.name('SearchJSONVouchers')
    uvclight.auth.require('zope.Public')

    def render(self):
        terms = []
        void = self.request.form.get('term')
        if void:
            session = get_session('ukhvoucher')
            if len(void) < 6:
                ress = session.query(models.Voucher).filter(
                    cast(models.Voucher.oid, String).like(void + '%')).all()
            else:
                ress = session.query(models.Voucher).filter(models.Voucher.oid == void).all()
            for x in ress:
                terms.append({
                    'id': int(x.oid),
                    'text': "%s (%s) - %s %s" %(x.title, x.zeitraum().token, x.status.strip(), x.cat),
                    'disabled': (x.invoice is not None or x.status.strip() in (DISABLED, BOOKED)),
                    #'disabled': True,
                })
        return {'q': void.strip(), 'results': terms}
