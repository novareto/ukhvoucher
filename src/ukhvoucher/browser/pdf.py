# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de

import uvclight
import tempfile
import ukhvoucher


from os import path
from ..apps import UserRoot
from time import gmtime, strftime
from ..interfaces import IUserLayer


from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black
from reportlab.graphics.barcode import code39


class PDF(uvclight.Page):
    uvclight.layer(IUserLayer)
    uvclight.context(UserRoot)
    uvclight.auth.require('users.access')

    def make_response(self, result):
        response = self.responseFactory(app_iter=result)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = "%s" % (
            'attachment; filename="gutschein.pdf"'
        )
        return response

    def render(self):
        tmp = tempfile.TemporaryFile()
        c = canvas.Canvas(tmp, pagesize=A4)
        c.setAuthor("UKH")
        c.setTitle(u'Rehamanagement')
        schriftart = "Helvetica"
        schriftartfett = "Helvetica-Bold"
        datum = strftime("%d.%m.%Y", gmtime())
        principal = self.request.principal
        adr = principal.getAddress()
        z1 = 1
        z2 = len(principal.getVouchers())
        for voucher in principal.getVouchers():
            c.setFont(schriftart, 12)
            bcp = '%s/static/logo_ukh.JPG' % path.dirname(ukhvoucher.__file__)
            c.drawImage(bcp, 15.5 * cm, 27.2 * cm, width=4.5 * cm, height=1.3 * cm)
            # Eigene Adresse
            c.setFont(schriftart, 9)
            c.drawString(15.5 * cm, 26.0 * cm, u'Leonardo-da-Vinci-Allee 20')
            c.drawString(15.5 * cm, 25.6 * cm, u'60486 Frankfurt')
            c.drawString(15.5 * cm, 25.2 * cm, u'Telefon')
            c.drawString(17.3 * cm, 25.2 * cm, u'069 29972-440')
            c.drawString(15.5 * cm, 24.8 * cm, u'Fax')
            c.drawString(17.3 * cm, 24.8 * cm, u'069 29972-8440')
            c.drawString(15.5 * cm, 24.4 * cm, u'Internet')
            c.drawString(17.3 * cm, 24.4 * cm, u'www.ukh.de')
            c.drawString(15.5 * cm, 24.0 * cm, u'E-Mail')
            c.drawString(17.3 * cm, 24.0 * cm, u'ukh@ukh.de')
            c.drawString(15.5 * cm, 23.2 * cm, u'Durchwahl')
            c.drawString(17.3 * cm, 23.2 * cm, u'069 29972-440')
            # Adressdaten
            c.setFont(schriftartfett, 12)
            x = 23.5
            # Namensfelder werden nur ausgegeben wenn diese gefuellt sind
            mnr = '1.50.12/00002'
            c.drawString(2.5 * cm, x * cm, u'Mitglieds-Nr.: ' + mnr)
            x = x - 1.0
            # Namensfelder werden nur ausgegeben wenn diese gefuellt sind
            c.drawString(2.5 * cm, x * cm, adr.name1 + adr.name2)
            x = x - 0.5
            c.drawString(2.5 * cm, x * cm, adr.name3)
            x = x - 0.5
            c.drawString(2.5 * cm, x * cm, adr.street + ' ' + adr.number)
            x = x - 0.5
            c.drawString(2.5 * cm, x * cm, adr.zip_code + ' ' + adr.city)
            #####################################################
            # Überschrift
            c.setFillColor(black)
            c.setFont(schriftartfett, 14)
            c.drawString(2.5 * cm, 18.5 * cm, u'Gutschein / Berechtigungsschein ' + str(z1) + ' von ' + str(z2))
            # Überschrift 2. Zeile
            c.setFont(schriftartfett, 10)
            y = 16.9
            c.drawString(2.5 * cm, y * cm, u'Diese Bescheinigung berechtigt eine Person zu einer einmaligen Teilnahme an einer')
            y = y - 0.6
            c.drawString(2.5 * cm, y * cm, u'Erste-Hilfe-Aus- und Fortbildung im Sinne der Unfallverhütungsvorschrift')
            y = y - 0.6
            c.drawString(2.5 * cm, y * cm, u'(UVV) DGUV Vorschrift 1 "Grundsätze der Prävention"')
            y = y - 1.2
            c.drawString(2.5 * cm, y * cm, u'Ausstellungsdatum: ' + datum)
            y = y - 2.5
            #####################################################
            # TEST                                              #
            #####################################################
            # Barcode Value....
            # Mitgliedsnummer (TEST)
            bc1 = '1501200002'
            # Gutscheinnummer
            zz = str(z1)
            if len(zz) == 1:
                bc2 = '00' + zz
            if len(zz) == 2:
                bc2 = '0' + zz
            if len(zz) == 3:
                bc2 = zz
            # Gültigkeit
            bc3 = '0506'
            barcode_value = bc1 + bc2 + bc3
            barcode = code39.Extended39(barcode_value, barWidth = 0.2 * mm, barHeight = 10 * mm)
            barcode.drawOn(c, 19 * mm, 120 * mm)
            c.drawString(2.5 * cm, 11.0 * cm, barcode_value)
            #####################################################
            z1 = z1 + 1
            # Seitenumbruch
            c.showPage()
        # ENDE und Save
        c.save()
        tmp.seek(0)
        return tmp.read()
