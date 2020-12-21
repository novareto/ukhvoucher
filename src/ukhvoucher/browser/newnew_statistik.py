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

ctext01 = u'''
Definition:
Zahl der Berechtigungsscheine, die im Abfragezeitraum den Status "erstellt" \
tragen bzw. getragen haben. Den Status "erstellt" erhalten alle \
Berechtigungsscheine, die vom System aufgrund der Dateneingabe des \
EHP-Mitglieds automatisch generiert wurden und noch nicht modifiziert sind. \
Dargestellt wird immer der zuletzt erfasste Status des Berechtigungsscheins \
im Abfragezeitraum.
'''

ctext02 = u'''
Definition:
Zahl der Berechtigungsscheine, die im Abfragezeitraum den Status \
"manuell_erstellt" tragen bzw. getragen haben. Den Status "manuell_erstellt" \
erhalten alle Berechtigungsscheine, die vom Administrator manuell generiert \
wurden und noch nicht modifiziert sind.
Dargestellt wird immer der zuletzt erfasste Status des Berechtigungsscheins \
im Abfragezeitraum.
'''

ctext03 = u'''
Definition:
Zahl der Berechtigungsscheine, die im Abfragezeitraum den Status "gebucht" \
tragen. Den Status "gebucht" erhalten alle Berechtigungsscheine, die vom \
Administrator einer Rechnung zugeordnet wurden.
Dargestellt wird immer der zuletzt erfasste Status des Berechtigungsscheins \
im Abfragezeitraum.
'''

ctext04 = u'''
Definition:
Zahl der Berechtigungsscheine, die im Abfragezeitraum den Status "ungültig" \
tragen. Den Status "ungültig" erhalten alle Berechtigungsscheine, die vom \
Administrator gesperrt wurden.
Dargestellt wird immer der zuletzt erfasste Status des Berechtigungsscheins \
im Abfragezeitraum.
'''

ctext05 = u'''
Definition:
Zahl der Berechtigungsscheine, die im Abfragezeitraum den Status "abgelaufen" \
tragen. Den Status "abgelaufen" erhalten alle Berechtigungsscheine, die vom \
System nach Ablauf von 5 Kalenderjahren nach Erstellung noch nicht modifiziert \
wurden.
Dargestellt wird immer der zuletzt erfasste Status des Berechtigungsscheins \
im Abfragezeitraum.
'''

ctext06 = u'''
Definition:
Statusunabhängige Zahl der Berechtigungsscheine, die im Abfragezeitraum vom \
EHP-Mitglied ("erstellt") oder dem Admin ("manuell_erstellt") generiert \
wurden, unabhängig eines Modifikationsdatums.
'''

ctext07 = u'''
Definition:
Statusunabhängige Zahl der Berechtigungsscheine, die im Abfragezeitraum vom \
EHP-Mitglied ("erstellt") oder dem Admin ("manuell_erstellt") generiert \
wurden abzüglich der Berechtigungsscheine mit Status "ungültig" (Spalte F).
'''

ctext08 = u'''
Definition:
Anzahl der Berechtigungsscheine, die im Abfragezeitraum vom EHP-Mitglied \
("erstellt") oder dem Admin ("manuell_erstellt") generiert wurden abzüglich \
der Berechtigungsscheine, die bezogen auf den Abfragezeitraum modifiziert wurden.

Z.B. Im Abfragzeitraum 01.01.2017-31.12.2017 wurden 50 BS erstellt und 20 BS \
davon sind zum 31.12.2017 noch offen.

-> In diesem Beispiel würden dann die 20 BS angezeigt werden.
'''

ctext09 = u'''
Definition:
Anzahl der Berechtigungsscheine, die im Zeitraum "Abfragezeitraum von" \
bis zum "Abfragezeitpunkt" vom EHP-Mitglied ("erstellt") oder dem Admin \
("manuell_erstellt") generiert wurden abzüglch der Berechtigungsscheine, \
die bezogen auf den Zeitraum modifiziert wurden.
'''


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
    oid = schema.TextLine(
        title=u"oid",
        required=False,
        )
    abis = schema.TextLine(
        title=u"Abfragezeitpunkt (Sollte kein Datum eingetragen werden, wird das aktuelle Tagesdatum verwendet.)",
        required=False,
        )


def make_csv(form, result, *args, **kwargs):
    response = form.responseFactory()
    response.content_type = 'text/csv'
    result.seek(0)
    response.headers['Content-Type'] = 'application/vnd.ms-excel'
    response.headers['content-disposition'] = 'attachment; filename=Statistik.xlsx'
    response.write(result.read() or u'')
    return response


class StatistikSuperNeu(uvclight.Form):
    uvclight.context(interface.Interface)
    require('manage.vouchers')
    template = uvclight.get_template('statistik.cpt', __file__)
    allvouchers = []

    fields = uvclight.Fields(IStatForm)

    #@uvclight.action(u'Suchen')
    #def handle_search(self):
    #    data, errors = self.extractData()
    #    if errors:
    #        return
    #    self.data = data

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
        merge_format_s = workbook.add_format({
            'font_size': 9,
            'bold': 1,
            'border': 2,
            'align': 'center',
            'text_wrap': True,
            'valign': 'vcenter',
            'font_color': 'blue'})
        merge_format_summe = workbook.add_format({
            'bold': 1,
            'border': 2,
            'align': 'center',
            'valign': 'vcenter',
            'font_color': 'blue',
            'num_format': '#,##0'})
        sum_f = workbook.add_format({'border': 2, 'num_format': '#,##0'})
        sum_x = workbook.add_format({'border': 2, 'num_format': '0.00 "EUR"'})
        border = workbook.add_format({'border': 1, 'num_format': '#,##0'})
        border_summe = workbook.add_format({'border': 1, 'num_format': '0.00 "EUR"'})
        border_f = workbook.add_format({'border': 1, 'align': 'center'})
        wrap = workbook.add_format({'border': 1, 'text_wrap': True, 'align': 'center'})
        gray = workbook.add_format({'bg_color': '#f7f7f9'})
        green = workbook.add_format({'bg_color': '#ccff99'})
        orange = workbook.add_format({'bg_color': 'FFA500'})
        bold = workbook.add_format({'bold': True})
        sheet = workbook.add_worksheet(u'Berechtigungsscheine')
        sheet.set_landscape()
        sheet.set_column(1, 1, 55)
        sheet.set_column(2, 12, 14)
        # # Zeile 1                                                          #
        sheet.write('A1', 'Datum der Abfrage: %s' % datetime.now().strftime('%d.%m.%Y'), bold)
        sheet.merge_range('L1:M1', u'Lehrgangsgebühren in EUR:', bold)
        # # Zeile 2                                                          #
        sheet.merge_range('A2:B2', 'Abfragezeitraum: %s - %s' % (self.data.get('von', ''), self.data.get('bis', '')), bold)
        sheet.write('M2', u'', orange)
        # # Zeile 3                                                          #
        sheet.merge_range('A3:B3', 'Kontingente', merge_format)
        sheet.merge_range('C3:G3', 'Zahl der Berechtigungsscheine mit Status "..." im Abfragezeitraum', merge_format)
        sheet.merge_range('H3:I3', 'Gesamtzahl der \n Berechtigungsscheine', merge_format_w)
        dvon = self.data.get('von', '')
        dbis = self.data.get('bis', '')
        sheet.write('J3', 'Anzahl der \n offenen \n Berechtigungs- \n scheine im \n Abfragezeitraum \n' + dvon + '\n' + dbis, merge_format_s)
        abis = self.data.get('abis', '')
        sheet.write('K3', 'Anzahl der \n offenen \n Berechtigungs- \n scheine zum \n Abfragezeitpunkt \n' + abis, merge_format_s)
        sheet.merge_range('L3:M3', 'Ausgaben', merge_format)
        # # Zeile 4                                                          #
        sheet.write('A4', 'Gruppe', border_f)
        sheet.write('B4', u'Bezeichnung', border_f)
        sheet.write('C4', 'erstellt', border_f)
        sheet.write_comment('C4', ctext01, {'width': 320, 'height': 250, 'font_size': 10})
        sheet.write('D4', 'manuell \n erstellt', wrap)
        sheet.write_comment('D4', ctext02, {'width': 320, 'height': 250, 'font_size': 10})
        sheet.write('E4', 'gebucht', border_f)
        sheet.write_comment('E4', ctext03, {'width': 320, 'height': 250, 'font_size': 10})
        sheet.write('F4', u'ungültig', border_f)
        sheet.write_comment('F4', ctext04, {'width': 320, 'height': 250, 'font_size': 10})
        sheet.write('G4', u'abgelaufen', border_f)
        sheet.write_comment('G4', ctext05, {'width': 320, 'height': 250, 'font_size': 10})
        sheet.write('H4', u'generiert', border_f)
        sheet.write_comment('H4', ctext06, {'width': 320, 'height': 250, 'font_size': 10})
        sheet.write('I4', u'generiert \n abzüglich \n ungültig', wrap)
        sheet.write_comment('I4', ctext07, {'width': 320, 'height': 250, 'font_size': 10})
        sheet.write('J4', u'offen', wrap)
        sheet.write_comment('J4', ctext08, {'width': 320, 'height': 250, 'font_size': 10})
        sheet.write('K4', u'offen', wrap)
        sheet.write_comment('K4', ctext09, {'width': 320, 'height': 250, 'font_size': 10})
        sheet.write('L4', u'gebucht', border_f)
        sheet.write('M4', u'offen', border_f)
        # # Zeile 18                                                         #
        sheet.merge_range('A18:B18', 'Summe', merge_format_summe)
        # # Zeile 20                                                         #
        sheet.merge_range('A20:B20', u'Kontingente für Beschäftigte', gray)
        # # Zeile 21                                                         #
        sheet.merge_range('A21:B21', u'Kontingente für Kinderbetreuung', green)
        #import pdb; pdb.set_trace()
        #i = 0
        for k, v in natsorted(self.statdata.items()):
            if int(k[1:]) == 13:
                sheet.write(int(k[1:])+2, 0, k, border)
                sheet.write(int(k[1:])+2, 1, v['title'], border)
                sheet.write(int(k[1:])+2, 2, v.get('erstellt', 0), border)
                sheet.write(int(k[1:])+2, 3, v.get('manuell', 0), border)
                sheet.write(int(k[1:])+2, 4, v.get('gebucht', 0), border)
                sheet.write(int(k[1:])+2, 5, v.get(u'ung\xfcltig', 0), border)
                sheet.write(int(k[1:])+2, 6, 0, border)  # seibert 13.12.2018 Platzhalter abgelaufene BS
                sheet.write(int(k[1:])+2, 7, v.get(u'total', 0), border)
                sheet.write_formula(int(k[1:])+2, 8, '=C%s+D%s+E%s' % (int(k[1:])+4, int(k[1:])+4, int(k[1:])+4), border)
                sheet.write_formula(int(k[1:])+2, 9, '=C%s+D%s' % (int(k[1:])+4, int(k[1:])+4), border)
                sheet.write_formula(int(k[1:])+2, 11, '=E%s*M2' % (int(k[1:])+4), border_summe)
                sheet.write_formula(int(k[1:])+2, 12, '=J%s*M2' % (int(k[1:])+4), border_summe)
            else:
                sheet.write(int(k[1:])+3, 0, k, border)
                sheet.write(int(k[1:])+3, 1, v['title'], border)
                sheet.write(int(k[1:])+3, 2, v.get('erstellt', 0), border)
                sheet.write(int(k[1:])+3, 3, v.get('manuell', 0), border)
                sheet.write(int(k[1:])+3, 4, v.get('gebucht', 0), border)
                sheet.write(int(k[1:])+3, 5, v.get(u'ung\xfcltig', 0), border)
                sheet.write(int(k[1:])+3, 6, 0, border)  # seibert 13.12.2018 Platzhalter abgelaufene BS
                sheet.write(int(k[1:])+3, 7, v.get(u'total', 0), border)
                sheet.write_formula(int(k[1:])+3, 8, '=C%s+D%s+E%s' % (int(k[1:])+4, int(k[1:])+4, int(k[1:])+4), border)
                sheet.write_formula(int(k[1:])+3, 9, '=C%s+D%s' % (int(k[1:])+4, int(k[1:])+4), border)
                sheet.write_formula(int(k[1:])+3, 11, '=E%s*M2' % (int(k[1:])+4), border_summe)
                sheet.write_formula(int(k[1:])+3, 12, '=J%s*M2' % (int(k[1:])+4), border_summe)
            #i += 1
        #i = 0
        for k, v in natsorted(self.abfragezeitpunkt.items()):
            if int(k[1:]) == 13:
                sheet.write(int(k[1:])+2, 0, k, border)
                sheet.write(int(k[1:])+2, 1, v['title'], border)
                z1 = int(v.get('erstellt', 0))
                z2 = int(v.get('manuell', 0))
                su = z1 + z2
                sheet.write_formula(int(k[1:])+2, 10, str(su), border)
            else:
                sheet.write(int(k[1:])+3, 0, k, border)
                sheet.write(int(k[1:])+3, 1, v['title'], border)
                z1 = int(v.get('erstellt', 0))
                z2 = int(v.get('manuell', 0))
                su = z1 + z2
                sheet.write_formula(int(k[1:])+3, 10, str(su), border)
            #i += 1
        # # Zeile 17                                                         #
        sheet.write_formula(17, 2, '=sum(C5:C16)', sum_f)
        sheet.write_formula(17, 3, '=sum(D5:D16)', sum_f)
        sheet.write_formula(17, 4, '=sum(E5:E16)', sum_f)
        sheet.write_formula(17, 5, '=sum(F5:F16)', sum_f)
        sheet.write_formula(17, 6, '=sum(G5:G16)', sum_f)
        sheet.write_formula(17, 7, '=sum(H5:H16)', sum_f)
        sheet.write_formula(17, 8, '=sum(I5:I16)', sum_f)
        sheet.write_formula(17, 9, '=sum(J5:J16)', sum_f)
        sheet.write_formula(17, 10, '=sum(K5:K16)', sum_f)
        sheet.write_formula(17, 11, '=sum(L5:L16)', sum_x)
        sheet.write_formula(17, 12, '=sum(M5:M16)', sum_x)
        for k, v in natsorted(self.statdata.items()):
            if k == 'K1':
                sheet.conditional_format('A5:M5', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': gray})
            if k == 'K2':
                sheet.conditional_format('A6:M6', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': gray})
            if k == 'K3':
                sheet.conditional_format('A7:M7', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': green})
            if k == 'K4':
                sheet.conditional_format('A8:M8', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': gray})
            if k == 'K5':
                sheet.conditional_format('A9:M9', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': gray})
            if k == 'K6':
                sheet.conditional_format('A10:M10', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': gray})
            if k == 'K7':
                sheet.conditional_format('A11:M11', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': green})
            if k == 'K8':
                sheet.conditional_format('A12:M12', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': green})
            if k == 'K9':
                sheet.conditional_format('A13:M13', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': green})
            if k == 'K10':
                sheet.conditional_format('A14:M14', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': gray})
            if k == 'K11':
                sheet.conditional_format('A15:M15', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': gray})
            if k == 'K13':
                sheet.conditional_format('A16:M16', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': green})
        for k, v in natsorted(self.abfragezeitpunkt.items()):
            if k == 'K1':
                sheet.conditional_format('A5:M5', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': gray})
            if k == 'K2':
                sheet.conditional_format('A6:M6', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': gray})
            if k == 'K3':
                sheet.conditional_format('A7:M7', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': green})
            if k == 'K4':
                sheet.conditional_format('A8:M8', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': gray})
            if k == 'K5':
                sheet.conditional_format('A9:M9', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': gray})
            if k == 'K6':
                sheet.conditional_format('A10:M10', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': gray})
            if k == 'K7':
                sheet.conditional_format('A11:M11', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': green})
            if k == 'K8':
                sheet.conditional_format('A12:M12', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': green})
            if k == 'K9':
                sheet.conditional_format('A13:M13', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': green})
            if k == 'K10':
                sheet.conditional_format('A14:M14', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': gray})
            if k == 'K11':
                sheet.conditional_format('A15:M15', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': gray})
            if k == 'K13':
                sheet.conditional_format('A16:M16', {'type': 'cell', 'criteria': '>=', 'value': 0, 'format': green})
        sheet.set_row(2, 100)
        sheet.set_row(3, 45)
        sheet.set_row(15, 18)
        if self.allvouchers:
            i = 1
            sheet = workbook.add_worksheet(u'Alle Gutscheine')
            sheet.write(0, 0, "Erstelldatum")
            sheet.write(0, 1, "Modifikations Datum")
            sheet.write(0, 2, "Status")
            sheet.write(0, 3, "BS-ID")
            sheet.write(0, 4, "Kategorie")
            sheet.write(0, 5, "Info")
            for voucher in self.allvouchers:
                sheet.write(i, 0, voucher.creation_date.strftime('%d.%m.%Y'))
                sheet.write(i, 1, voucher.modification_date.strftime('%d.%m.%Y'))
                sheet.write(i, 2, voucher.status)
                sheet.write(i, 3, voucher.oid)
                sheet.write(i, 4, voucher.displayKat)
                sheet.write(i, 5, voucher.displayData)
                i += 1
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

    @uvclight.action(u'Export')
    def handle_export(self):
        data, errors = self.extractData()
        if errors:
            return
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
        q = session.query(models.Voucher)
        if data['oid'] and data['oid'] is not NO_VALUE:
            q = q.filter(models.Voucher.user_id == data['oid'])
            self.allvouchers = q.all()
        queryNew = self.filterCreation(q, data)
        adat = {}
        adat['von'] = '01.01.2016'
        adat['oid'] = data['oid']
        if data['abis'] == '':
            adat['bis'] = datetime.now().strftime('%d.%m.%Y')
        else:
            adat['bis'] = data['abis']
        querytest = self.filterCreation(q, adat)
        ret = {}
        for voucher in queryNew.all():
            vcat = voucher.cat.strip()
            if vcat not in ret:
                try:
                    title = kats.getTerm(vcat).title
                except:
                    title = vcat
                ret[vcat] = {'title': title, 'total': 0, 'manuell': 0, 'erstellt': 0, 'gebucht': 0, u'ung\xfcltig': 0, 'erstellt_all': 0}
            ret[vcat]['total'] += 1
            if voucher.generation.data.strip() == '"Manuelle Erzeugung"':
                ret[vcat]['manuell'] += 1
            else:
                ret[vcat]['erstellt'] += 1
        for voucher in self.filterModification(q, data).all():
            vcat = voucher.cat.strip()
            if vcat not in ret:
                try:
                    title = kats.getTerm(vcat).title
                except:
                    title = vcat
                ret[vcat] = {'title': title, 'total': 0, 'manuell': 0, 'erstellt': 0, 'gebucht': 0, u'ung\xfcltig': 0, 'erstellt_all': 0}
            if voucher.status.strip() == 'gebucht':
                ret[vcat]['gebucht'] += 1
            elif voucher.status.strip() == u'ungültig':
                ret[vcat][u'ung\xfcltig'] += 1
            if True:
                if voucher.status.strip() in ['gebucht', u'ungültig']:
                    if data['bis'] is not NO_VALUE and data['von'] is not NO_VALUE:
                        bis = data['bis']
                        if not bis:
                            bis = '01.01.2016'
                        von = data['von']
                        if not von:
                            von = '31.12.2027'
                        if voucher.creation_date >= datetime.strptime(von, '%d.%m.%Y').date() and voucher.creation_date <= datetime.strptime(bis, '%d.%m.%Y').date():
                            if voucher.generation.data.strip() == '"Manuelle Erzeugung"':
                                if ret[vcat]['manuell'] > 0:
                                    ret[vcat]['manuell'] -= 1
                            else:
                                if ret[vcat]['erstellt'] > 0:
                                    ret[vcat]['erstellt'] -= 1
        self.statdata = ret
        ret2 = {}
        for voucher in querytest.all():
            vcat = voucher.cat.strip()
            if vcat not in ret2:
                try:
                    title = kats.getTerm(vcat).title
                except:
                    title = vcat
                ret2[vcat] = {'title': title, 'total': 0, 'manuell': 0, 'erstellt': 0, 'gebucht': 0, u'ung\xfcltig': 0, 'erstellt_all': 0}
            ret2[vcat]['total'] += 1
            if voucher.generation.data.strip() == '"Manuelle Erzeugung"':
                ret2[vcat]['manuell'] += 1
            else:
                ret2[vcat]['erstellt'] += 1
        for voucher in self.filterModification(q, adat).all():
            vcat = voucher.cat.strip()
            if vcat not in ret2:
                try:
                    title = kats.getTerm(vcat).title
                except:
                    title = vcat
                ret2[vcat] = {'title': title, 'total': 0, 'manuell': 0, 'erstellt': 0, 'gebucht': 0, u'ung\xfcltig': 0, 'erstellt_all': 0}
            if voucher.status.strip() == 'gebucht':
                ret2[vcat]['gebucht'] += 1
            elif voucher.status.strip() == u'ungültig':
                ret2[vcat][u'ung\xfcltig'] += 1
            if True:
                if voucher.status.strip() in ['gebucht', u'ungültig']:
                    if adat['bis'] is not NO_VALUE and adat['von'] is not NO_VALUE:
                        bis = adat['bis']
                        if not bis:
                            bis = '01.01.2016'
                        von = adat['von']
                        if not von:
                            von = '31.12.2027'
                        if voucher.creation_date >= datetime.strptime(von, '%d.%m.%Y').date() and voucher.creation_date <= datetime.strptime(bis, '%d.%m.%Y').date():
                            if voucher.generation.data.strip() == '"Manuelle Erzeugung"':
                                if ret2[vcat]['manuell'] > 0:
                                    ret2[vcat]['manuell'] -= 1
                            else:
                                if ret2[vcat]['erstellt'] > 0:
                                    ret2[vcat]['erstellt'] -= 1
        self.abfragezeitpunkt = ret2
        


        self.data = data
        return CSVEXPORT
