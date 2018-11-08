# -*- coding: utf-8 -*-

import uvclight
import types
import xlsxwriter
from natsort import natsorted


from datetime import datetime
from sqlalchemy import func
from ul.auth import require
from ukhvoucher import models, BOOKED
from zope import schema, interface
from cromlech.sqlalchemy import get_session
from ukhvoucher.interfaces import get_kategorie
from dolmen.forms.base import NO_VALUE
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
    #response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    response.headers['Content-Type'] = 'application/vnd.ms-excel'
    response.headers['content-disposition'] = 'attachment; filename=Statistik.xlsx'
    response.write(result.read() or u'')
    return response


class StatistikNeu(uvclight.Form):
    uvclight.context(interface.Interface)
    require('manage.vouchers')
    template = uvclight.get_template('statistik.cpt', __file__)

    fields = uvclight.Fields(IStatForm)

    @uvclight.action(u'Suchen')
    def handle_search(self):
        data, errors = self.extractData()
        if errors:
            return
        self.data = data

    @uvclight.action(u'Export')
    def handle_export(self):
        data, errors = self.extractData()
        if errors:
            return
        self.data = data
        return CSVEXPORT

    def create_result(self, *args, **kwargs):
        from StringIO import StringIO
        f = StringIO()
        workbook = xlsxwriter.Workbook(f)
        workbook.set_size(1600, 800)
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 2,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': 'blue'})
        merge_format_w = workbook.add_format({
            'bold': 1,
            'border': 2,
            'align': 'center',
            'text_wrap': True,
            'valign': 'vcenter',
            'font_color': 'blue'})
        sum_f = workbook.add_format({'border': 2, 'num_format': '#,##0'})
        border = workbook.add_format( {'border': 1, 'num_format':'#,##0'} )
        border_f = workbook.add_format( {'border': 1, 'align': 'center'} )
        wrap = workbook.add_format({'border': 1, 'text_wrap': True, 'align':'center'})
        #wrap = workbook.add_format({'text_wrap': True, 'align':'center'})
        gray = workbook.add_format({'bg_color': '#f7f7f9'})
        green = workbook.add_format({'bg_color': '#ccff99'})

        bold = workbook.add_format({'bold': True})
        sheet = workbook.add_worksheet(u'Berechtigungsscheine')
        sheet.set_landscape()
        sheet.set_column(1, 1, 55)
        sheet.set_column(2, 9, 14)
        sheet.write('A1', 'Datum der Abfrage: %s' % datetime.now().strftime('%d.%m.%Y'), bold)
        sheet.merge_range('A2:B2', 'Abfragezeitraum: %s - %s' %(self.data.get('von', ''), self.data.get('bis', '')), bold)
        sheet.merge_range('A3:B3', 'Kontingente', merge_format)
        sheet.merge_range('A15:B15', 'Summe', merge_format)
        sheet.merge_range('C3:F3', 'Zahl der Berechtigungsscheine', merge_format)
        sheet.merge_range('G3:H3', 'Gesamtzahl der \n Berechtigungsscheine', merge_format_w)
        sheet.merge_range('I3:J3', 'Ausgaben', merge_format)
        sheet.write('A4', 'Gruppe', border_f)
        sheet.write('B4', u'Bezeichnung', border_f)
        sheet.write('C4', 'erstellt', border_f)
        sheet.write('D4', 'manuell \n erstellt', wrap)
        sheet.write('E4', 'gebucht', border_f)
        sheet.write('F4', u'ungültig', border_f)
        sheet.write('G4', u'ohne ungültig', border_f)
        sheet.write('H4', 'erstellt + \n manuell erstellt', wrap)
        sheet.write('I4', 'gebucht', border_f)
        sheet.write('J4', 'erstellt + \n manuell erstellt', wrap)
        sheet.write('I2', u'Lehrgangsgebühren', bold)
        sheet.merge_range('A18:B18', u'Kontingente für Beschäftigte', gray)
        sheet.merge_range('A19:B19', u'Kontingente für Kinderbetreuung', green)
        #import pdb; pdb.set_trace()
        i = 0
        for k, v in natsorted(self.statdata.items()):
            sheet.write(4+i, 0, k, border)
            sheet.write(4+i, 1, v['title'], border)
            sheet.write(4+i, 2, v.get('erstellt', 0), border)
            sheet.write(4+i, 3, v.get('manuell', 0), border)
            sheet.write(4+i, 4, v.get('gebucht', 0), border)
            sheet.write(4+i, 5, v.get(u'ung\xfcltig', 0), border)
            #sheet.write_formula(4+i, 6, '=C%s+D%s+E%s-F%s' % (5+i, 5+i, 5+i, 5+i), border ) #=C5+D5+E5-F5
            sheet.write_formula(4+i, 6, '=C%s+D%s+E%s' % (5+i, 5+i, 5+i), border ) #=C5+D5+E5 ### am 11.05.2017 geaendert -F entfernt
            sheet.write_formula(4+i, 7, '=C%s+D%s' % (5+i, 5+i), border ) #=C5+D5
            sheet.write_formula(4+i, 8, '=E%s*J2' % (5+i), border) # =E5*J2
            sheet.write_formula(4+i, 9, '=H%s*J2' % (5+i), border) # =E5*J2
            i += 1
        sheet.write_formula(14, 2, '=sum(C5:C14)', sum_f)
        sheet.write_formula(14, 3, '=sum(D5:D14)', sum_f)
        sheet.write_formula(14, 4, '=sum(E5:E14)', sum_f)
        sheet.write_formula(14, 5, '=sum(F5:F14)', sum_f)
        sheet.write_formula(14, 6, '=sum(G5:G14)', sum_f)
        sheet.write_formula(14, 7, '=sum(H5:H14)', sum_f)
        sheet.write_formula(14, 8, '=sum(I5:I14)', sum_f)
        sheet.write_formula(14, 9, '=sum(J5:J14)', sum_f)
        sheet.conditional_format('A5:J6', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': gray})
        sheet.conditional_format('A8:J10', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': gray})
        sheet.conditional_format('A14:J14', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': gray})
        sheet.conditional_format('A7:J7', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': green})
        sheet.conditional_format('A11:J13', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': green})
        sheet.set_row(2, 30)
        workbook.close()
        return f

    def updateActions(self):
        action, result = uvclight.Form.updateActions(self)
        if result is CSVEXPORT:
            self.render = types.MethodType(self.create_result, self)
            self.make_response = types.MethodType(make_csv, self)
        return action, result

    def filterCreation(self, query, data):
        if data['von'] and data['von'] is not NO_VALUE:
            query = query.filter(
                models.Voucher.creation_date >= datetime.strptime(data['von'], '%d.%m.%Y')
            )
        if data['bis'] and data['bis'] is not NO_VALUE:
            query = query.filter(
                models.Voucher.creation_date <= datetime.strptime(data['bis'], '%d.%m.%Y')
            )
        return query

    def filterModification(self, query, data):
        if data['von'] and data['von'] is not NO_VALUE:
            query = query.filter(
                models.Voucher.modification_date >= datetime.strptime(data['von'], '%d.%m.%Y')
            )
        if data['bis'] and data['bis'] is not NO_VALUE:
            query = query.filter(
                models.Voucher.modification_date <= datetime.strptime(data['bis'], '%d.%m.%Y')
            )
        return query

    def update(self):
        js.need()
        data, errors = self.extractData()
        kats = get_kategorie(None)
        session = get_session('ukhvoucher')
        rc = []
        query = session.query(
            models.Voucher.cat, func.count(models.Voucher.oid)).group_by(models.Voucher.cat).filter(
                models.Voucher.status == BOOKED).order_by(models.Voucher.cat)
        if data['von'] and data['von'] is not NO_VALUE:
            query = query.filter(models.Voucher.modification_date >= datetime.strptime(data['von'], '%d.%m.%Y'))
        if data['bis'] and data['bis'] is not NO_VALUE:
            query = query.filter(models.Voucher.modification_date <= datetime.strptime(data['bis'], '%d.%m.%Y'))
        for cat, count in query.all():
            rc.append((kats.getTerm(cat.strip()).title, str(count)))
        self.statdata1 = rc


        print
        print "#" * 44
        print

        q = session.query(models.Voucher)
        queryNew = self.filterCreation(q, data)
        ret = {}
        
        for voucher in queryNew.all():
            vcat = voucher.cat.strip()
            if vcat not in ret:
                try:
                    title = kats.getTerm(vcat).title
                except:
                    title = vcat
                    print vcat
                ret[vcat] = {'title': title, 'total': 0, 'manuell': 0, 'erstellt': 0, 'gebucht': 0, u'ung\xfcltig': 0 }
            ret[vcat]['total'] += 1
            if voucher.generation.data.strip() == '"Manuelle Erzeugung"':
                ret[vcat]['manuell'] += 1
            else:
                ret[vcat]['erstellt'] += 1
        for voucher in self.filterModification(q, data).all():
            if voucher.status.strip() == 'gebucht':
                ret[vcat]['gebucht'] += 1
            elif voucher.status.strip() == u'ungültig':
                ret[vcat][u'ung\xfcltig'] += 1
            if voucher.status.strip() in ['gebucht', u'ungültig']:
                if voucher.generation.data == '"Manuelle Erzeugung"':
                    ret[vcat]['manuell'] -= 1
                else:
                    ret[vcat]['erstellt'] -= 1
        self.statdata = ret
