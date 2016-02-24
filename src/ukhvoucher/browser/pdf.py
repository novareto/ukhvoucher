# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de

import uvclight
import tempfile
import ukhvoucher

from os import path
from ..apps import UserRoot
from ukhvoucher import CREATED
#from time import gmtime, strftime
from ..interfaces import IUserLayer


from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black
from reportlab.graphics.barcode import code128


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
        c.setTitle(u'Erste Hilfe')
        schriftart = "Helvetica"
        schriftartfett = "Helvetica-Bold"
        #datum = strftime("%d.%m.%Y", gmtime())
        principal = self.request.principal
        adr = principal.getAddress()
        account = principal.getAccount()
        z1 = 1
        #z2 = len(principal.getVouchers())
        for voucher in principal.getVouchers(cat=self.request.form.get('cat')):
            if voucher.status.strip() == CREATED:
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
                mnr = adr.mnr.strip()
                if mnr != '':
                    c.drawString(2.5 * cm, x * cm, u'Mitglieds-Nr.: ' + mnr)
                x = x - 1.0
                # Namensfelder werden nur ausgegeben wenn diese gefuellt sind
                c.drawString(2.5 * cm, x * cm, adr.name1.strip() + ' ' + adr.name2.strip())
                x = x - 0.5
                c.drawString(2.5 * cm, x * cm, adr.name3.strip())
                x = x - 0.5
                c.drawString(2.5 * cm, x * cm, adr.street.strip() + ' ' + adr.number.strip())
                x = x - 0.5
                c.drawString(2.5 * cm, x * cm, str(adr.zip_code) + ' ' + adr.city.strip())
                #####################################################
                # Überschrift
                ikg = str(voucher.cat.strip())
                if ikg == 'IKG1':
                    kattext = u'Verwaltung, Büro'
                elif ikg == 'IKG2':
                    kattext = u'Andere Betriebe'
                elif ikg == 'IKG3':
                    kattext = u'Kinderbetreuungseinrichtungen'
                elif ikg == 'IKG4':
                    kattext = u'Entsorgung/Bauhof'
                elif ikg == 'IKG5':
                    kattext = u'Einrichtungen mit spezieller Gefährdung'
                elif ikg == 'IKG6':
                    kattext = u'Einrichtungen mit spezieller Gefährdung'
                elif ikg == 'IKG7':
                    kattext = u'Schulen'
                elif ikg == 'IKG8':
                    kattext = u'Schulstandorte'
                elif ikg == 'IKG9':
                    kattext = u'Schulbetreuung'
                else:
                    kattext = u''
                c.setFillColor(black)
                c.setFont(schriftartfett, 14)
                c.drawString(2.5 * cm, 18.5 * cm, u'Gutschein / Berechtigungsschein ')  # + str(z1) + ' von ' + str(z2))
                c.drawString(2.5 * cm, 17.9 * cm, u'Kontingentgruppe: ' + str(voucher.cat.strip()) + ' ' + kattext)
                # Überschrift 2. Zeile
                c.setFont(schriftartfett, 10)
                y = 16.8
                c.drawString(2.5 * cm, y * cm, u'Diese Bescheinigung berechtigt eine Person zu einer einmaligen Teilnahme an einer')
                y = y - 0.6
                c.drawString(2.5 * cm, y * cm, u'Erste-Hilfe-Aus- oder Fortbildung im Sinne der Unfallverhütungsvorschrift')
                y = y - 0.6
                c.drawString(2.5 * cm, y * cm, u'(UVV) DGUV Vorschrift 1 "Grundsätze der Prävention"')
                y = y - 1.2
                # Datum der Erstellung
                d = str(voucher.creation_date)
                tag = d[8:10]
                monat = d[5:7]
                jahr = d[:4]
                erstelldatum = tag + '.' + monat + '.' + jahr
                c.drawString(2.5 * cm, y * cm, u'Ausstellungsdatum: ' + erstelldatum)
                y = y - 2.5
                # Barcode Value....
                barcode_value = str(voucher.oid)
                barcode = code128.Code128(barcode_value, barWidth = 0.2 * mm, barHeight = 10 * mm)
                barcode.drawOn(c, 19 * mm, 120 * mm)
                c.drawString(2.5 * cm, 11.0 * cm, barcode_value)

                #Ansprechpartner
                c.drawString(2.5 * cm, 9.0 *cm, u'Ansprechpartner')
                c.drawString(2.5 * cm, 8.0 * cm, "%s %s" % (account.vname.strip(), account.nname.strip()))
                c.drawString(2.5 * cm, 7.5 * cm, "%s" % (account.phone.strip()))
                c.drawString(2.5 * cm, 7.0 * cm, "%s" % (account.email.strip()))
                z1 = z1 + 1
                # Seitenumbruch
                c.showPage()
        # ENDE und Save
        c.save()
        tmp.seek(0)
        return tmp.read()
