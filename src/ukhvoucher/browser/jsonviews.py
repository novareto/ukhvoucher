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
                if len(void) == 6 and x.status.strip() in (DISABLED, BOOKED):
                    print "REMOVE THE DISABLED ONE"
                    continue
                datum = x.zeitraum()
                terms.append({
                    'id': int(x.oid),
                    'text': "[%s-%s] %s - %s %s" %(datum.von.strftime('%y'), datum.bis.strftime('%y'), x.title, x.status.strip(), x.cat),
                    'disabled': (x.invoice is not None or x.status.strip() in (DISABLED, BOOKED)),
                    #'disabled': True,
                })
        return {'q': void.strip(), 'results': terms}
