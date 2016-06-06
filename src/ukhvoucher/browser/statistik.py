# -*- coding: utf-8 -*-

import uvclight
from sqlalchemy import func
from ul.auth import require
from ukhvoucher import BOOKED
from ukhvoucher import models
from zope import schema, interface
from cromlech.sqlalchemy import get_session
from ukhvoucher.interfaces import get_kategorie
from dolmen.forms.base import SUCCESS, NO_VALUE
from dolmen.forms.base.markers import SuccessMarker


class Export(SuccessMarker):

    def __init__(self, name, success, url=None, code=None, content_type=None):
        self.content_type = content_type
        SuccessMarker.__init__(self, name, success, url=url, code=code)


#CSVEXPORT = ExportMarker('CSV', True, content_type="text/csv")



class IStatForm(interface.Interface):
    von = schema.Date(
        title=u"Von",
        required=False,
     )

    bis = schema.Date(
        title=u"Bis",
        required=False,
     )


def make_csv(form, result, *args, **kwargs):
    response = form.responseFactory()
    response.content_type = 'text/csv'
    response.write(result or u'')
    return response


class Statistik(uvclight.Form):
    uvclight.context(interface.Interface)
    require('manage.vouchers')
    template = uvclight.get_template('statistik.cpt', __file__)

    fields = uvclight.Fields(IStatForm)

    @uvclight.action(u'Suchen')
    def handle_search(self):
        data, errors = self.extractData()
        if errors:
            return

    @uvclight.action(u'Export')
    def handle_export(self):
        data, errors = self.extractData()
        if errors:
            return
        return CSVEXPORT

    #def updateActions(self):
    #    action, result = uvclight.Form.updateActions()
    #    if result is CSVEXPORT:
    #        self.make_response = make_csv
    #    return action, result

    def update(self):
        data, errors = self.extractData()
        kats = get_kategorie(None)
        session = get_session('ukhvoucher')
        rc = []
        query = session.query(
            models.Voucher.cat, func.count(models.Voucher.oid)).group_by(models.Voucher.cat).filter(models.Voucher.status == BOOKED).order_by(models.Voucher.cat)
        if data['von'] and data['von'] is not NO_VALUE:
            query = query.filter(models.Voucher.creation_date > data['von'])
        if data['bis'] and data['bis'] is not NO_VALUE:
            query = query.filter(models.Voucher.creation_date < data['bis'])
        for cat, count in query.all():
            rc.append((kats.getTerm(cat.strip()).title, count))
        self.statdata = rc


