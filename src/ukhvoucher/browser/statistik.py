# -*- coding: utf-8 -*-

import uvclight
import csv
import types
import xlsxwriter


from sqlalchemy import func
from ul.auth import require
from ukhvoucher import BOOKED
from ukhvoucher import models
from zope import schema, interface
from cromlech.sqlalchemy import get_session
from ukhvoucher.interfaces import get_kategorie
from dolmen.forms.base import SUCCESS, NO_VALUE
from dolmen.forms.base.markers import SuccessMarker
from ukhvoucher.resources import ukhvouchers as js


class ExportMarker(SuccessMarker):

    def __init__(self, name, success, url=None, code=None, content_type=None):
        self.content_type = content_type
        SuccessMarker.__init__(self, name, success, url=url, code=code)


CSVEXPORT = ExportMarker('CSV', True, content_type="text/csv")



class IStatForm(interface.Interface):
    von = schema.TextLine(
        title=u"Von",
        required=False,
     )

    bis = schema.TextLine(
        title=u"Bis",
        required=False,
     )


def make_csv(form, result, *args, **kwargs):
    response = form.responseFactory()
    response.content_type = 'text/csv'
    result.seek(0)
    response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['content-disposition'] = 'attachment; filename=Staistik.xlsx'
    response.write(result.read() or u'')
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

    def create_result(self, *args, **kwargs):
        from StringIO import StringIO
        f = StringIO()
        workbook = xlsxwriter.Workbook(f)
        sheet = workbook.add_worksheet(u'mgl_betreuer')
        for i, x in enumerate(self.statdata):
            sheet.write(i, 0, x[0])
            sheet.write(i, 1, x[1])
        return f

    def updateActions(self):
        action, result = uvclight.Form.updateActions(self)
        if result is CSVEXPORT:
            self.render = types.MethodType(self.create_result, self)
            self.make_response = types.MethodType(make_csv, self)
        return action, result

    def update(self):
        js.need()
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
            rc.append((kats.getTerm(cat.strip()).title, str(count)))
        self.statdata = rc


