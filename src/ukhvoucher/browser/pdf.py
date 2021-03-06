# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de

import uvclight
import tempfile
import ukhvoucher

from os import path
from ..apps import UserRoot
from ukhvoucher import CREATED, MANUALLY_CREATED
#from time import gmtime, strftime
from ..interfaces import IUserLayer


from reportlab.pdfgen import canvas
from reportlab.lib.units import cm, mm
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import black
from reportlab.graphics.barcode import code128
from cromlech.sqlalchemy import get_session
from ukhvoucher import models
from sqlalchemy import and_


class PDF(uvclight.Page):
    uvclight.layer(IUserLayer)
    uvclight.context(UserRoot)
    uvclight.auth.require('users.access')

    def getAccount(self, login):
        if '-' in login:
            mnr, az = login.split('-')
        else:
            mnr = login
            az = "eh"
        session = get_session('ukhvoucher')
        return session.query(models.Account).filter(
                and_(models.Account.login == mnr, models.Account.az == az)
                ).one()

    def make_response(self, result):
        response = self.responseFactory(app_iter=result)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = "%s" % (
            'attachment; filename="berechtigungsschein.pdf"'
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
        pz = 0
        #z2 = len(principal.getVouchers())
        for voucher in principal.getVouchers(cat=self.request.form.get('cat')):
            from ukhvoucher.apps import USERS
            if voucher.generation.user.strip() not in USERS.keys():
                account = self.getAccount(voucher.generation.user_login or voucher.generation.autor.strip())
            if voucher.status.strip() == CREATED or voucher.status.strip() == MANUALLY_CREATED:
            #if voucher.status.strip() == CREATED:
                pz = pz + 1
                ikg = str(voucher.cat.strip())
                # ######################################
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
                c.drawString(17.3 * cm, 24.8 * cm, u'069 29972-8626')
                c.drawString(15.5 * cm, 24.4 * cm, u'Internet')
                c.drawString(17.3 * cm, 24.4 * cm, u'www.ukh.de')
                c.drawString(15.5 * cm, 24.0 * cm, u'E-Mail')
                c.drawString(17.3 * cm, 24.0 * cm, u'portal-erste-hilfe@ukh.de')
                # Adressdaten
                c.setFont(schriftartfett, 12)
                x = 23.5
                # Namensfelder werden nur ausgegeben wenn diese gefuellt sind
                mnr = adr.mnr.strip()
                if mnr != '':
                    if ikg == 'K7':
                        c.drawString(2.5 * cm, x * cm, u'Einrichtungsnummer: ' + mnr)
                    elif ikg == 'K9':
                        c.drawString(2.5 * cm, x * cm, u'Mitglieds- oder Betriebsnummer: ' + mnr)
                    else:
                        c.drawString(2.5 * cm, x * cm, u'Mitgliedsnummer: ' + mnr)
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
                if ikg == 'K1':
                    kattext = u'1 (K1) - Verwaltung, Büro'
                elif ikg == 'K2':
                    kattext = u'2 (K2) - Sonstige Betriebe'
                elif ikg == 'K3':
                    kattext = u'3 (K3) - Kindertageseinrichtungen'
                elif ikg == 'K4':
                    kattext = u'4 (K4) - Bauhof / Entsorgung'
                elif ikg == 'K5':
                    kattext = u'5 (K5) - Beschäftigte und Einrichtungen mit erhöhter Gefährdung'
                elif ikg == 'K6':
                    kattext = u'6 (K6) - Einrichtungen mit besonders hoher Gefährdung'
                elif ikg == 'K7':
                    kattext = u'7 (K7) - Schulen'
                elif ikg == 'K8':
                    kattext = u'8 (K8) - Schulpersonal'
                elif ikg == 'K9':
                    kattext = u'9 (K9) - Schulbetreuung'
                elif ikg == 'K10':
                    kattext = u'10 (K10) - Freiwillige Feuerwehren'
                elif ikg == 'K11':
                    kattext = u'11 (K11) - Gesundheitsdienste'
                elif ikg == 'K13':
                    kattext = u'13 (K13) - Kindertageseinrichtungen'
                else:
                    kattext = u''
                c.setFillColor(black)
                c.setFont(schriftartfett, 12)
                c.drawString(2.5 * cm, 18.5 * cm, u'Berechtigungsschein ')  # + str(z1) + ' von ' + str(z2))
                c.drawString(2.5 * cm, 17.9 * cm, u'Kontingent ' + kattext)
                # Überschrift 2. Zeile
                c.setFont(schriftartfett, 10)
                y = 16.8
                c.drawString(2.5 * cm, y * cm, u'Diese Bescheinigung berechtigt eine Person zu einer einmaligen Teilnahme an einer')
                y = y - 0.6
                if ikg == 'K3':
                    c.drawString(3.0 * cm, y * cm, u'-    Erste-Hilfe-Aus- oder Fortbildung oder')
                    y = y - 0.6
                    c.drawString(3.0 * cm, y * cm, u'-    Erste-Hilfe-Schulung in Bildungs- und Betreuungseinrichtungen für Kinder')
                    y = y - 0.6
                    c.drawString(2.5 * cm, y * cm, u'im Sinne des DGUV Grundsatzes 304-001')
                    y = y - 1.9
                elif ikg == 'K7':
                    c.drawString(2.5 * cm, y * cm, u'Erste-Hilfe-Fortbildung im Sinne des DGUV Grundsatzes 304-001')
                    y = y - 0.6
                    c.drawString(2.5 * cm, y * cm, u'oder einer Erste-Hilfe-Fortbildung Schule.')
                    y = y - 1.2
                    c.drawString(2.5 * cm, y * cm, u'Lehrgangsgebühren für die Erste-Hilfe-Ausbildung werden nicht übernommen.')
                    y = y - 1.3
                elif ikg == 'K9':
                    c.drawString(3.0 * cm, y * cm, u'-    Erste-Hilfe-Aus- oder Fortbildung oder')
                    y = y - 0.6
                    c.drawString(3.0 * cm, y * cm, u'-    Erste-Hilfe-Schulung in Bildungs- und Betreuungseinrichtungen für Kinder')
                    y = y - 0.6
                    c.drawString(2.5 * cm, y * cm, u'im Sinne des DGUV Grundsatzes 304-001')
                    y = y - 1.9
                elif ikg == 'K13':
                    c.drawString(3.0 * cm, y * cm, u'-    Erste-Hilfe-Aus- oder Fortbildung oder')
                    y = y - 0.6
                    c.drawString(3.0 * cm, y * cm, u'-    Erste-Hilfe-Schulung in Bildungs- und Betreuungseinrichtungen für Kinder')
                    y = y - 0.6
                    c.drawString(2.5 * cm, y * cm, u'im Sinne des DGUV Grundsatzes 304-001')
                    y = y - 1.9
                else:
                    c.drawString(2.5 * cm, y * cm, u'Erste-Hilfe-Aus- oder Fortbildung im Sinne des DGUV Grundsatzes 304-001.')
                    y = y - 3.1
                # Datum der Erstellung
                d = str(voucher.creation_date)
                tag = d[8:10]
                monat = d[5:7]
                jahr = d[:4]
                erstelldatum = tag + '.' + monat + '.' + jahr
                c.drawString(2.5 * cm, y * cm, u'Ausstellungsdatum: ' + erstelldatum)
                y = y - 0.6
                if jahr <= '2018':
                    c.drawString(2.5 * cm, y * cm, u'Gültigkeit für einen Lehrgang zwischen 01.01.2017 und 31.12.2018')
                if jahr == '2019' or jahr == '2020':
                    c.drawString(2.5 * cm, y * cm, u'Gültigkeit für einen Lehrgang zwischen 01.01.2019 und 31.12.2020')
                if jahr == '2021' or jahr == '2022':
                    c.drawString(2.5 * cm, y * cm, u'Gültigkeit für einen Lehrgang zwischen 01.01.2021 und 31.12.2022')
                y = y - 0.6
                c.drawString(2.5 * cm, y * cm, u'Der Berechtigungsschein ist spätestens bei Lehrgangsteilnahme der ermächtigten Stelle')
                y = y - 0.6
                c.drawString(2.5 * cm, y * cm, u'zu übermitteln. Die ermächtigte Stelle hat diesen der Rechnung beizufügen.')
                y = y - 2.7
                # Barcode Value....
                barcode_value = str(voucher.oid)
                barcode = code128.Code128(barcode_value, barWidth = 0.4 * mm, barHeight = 9 * mm)
                #barcode = code128.Code128(barcode_value, barWidth = 0.2 * mm, barHeight = 10 * mm)
                barcode.drawOn(c, 19 * mm, 90 * mm)
                y = 8.5
                c.drawString(2.5 * cm, y * cm, 'Nummer des Berechtigungsscheins:')
                y = y - 0.6
                c.drawString(2.5 * cm, y * cm, barcode_value)
                #Ansprechpartner
                telnummer = account.vorwahl.strip() + ' ' + account.phone.strip()
                titel = account.titel.strip()
                y = y - 3.0
                c.drawString(2.5 * cm, y *cm, u'Ansprechpartner')
                y = y - 0.8
                if titel != '':
                    c.drawString(2.5 * cm, y * cm, "%s %s %s %s" % (account.anrede.strip(), account.titel.strip(), account.vname.strip(), account.nname.strip()))
                else:
                    c.drawString(2.5 * cm, y * cm, "%s %s %s" % (account.anrede.strip(), account.vname.strip(), account.nname.strip()))
                y = y - 0.5
                c.drawString(2.5 * cm, y * cm, "Telefon: %s" % telnummer)
                y = y - 0.5
                c.drawString(2.5 * cm, y * cm, "E-Mail: %s" % (account.email.strip()))
                z1 = z1 + 1
                # Seitenumbruch
                c.showPage()
        if pz == 0:
            ikg = str(voucher.cat.strip())
            # ######################################
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
            c.drawString(17.3 * cm, 24.8 * cm, u'069 29972-8626')
            c.drawString(15.5 * cm, 24.4 * cm, u'Internet')
            c.drawString(17.3 * cm, 24.4 * cm, u'www.ukh.de')
            c.drawString(15.5 * cm, 24.0 * cm, u'E-Mail')
            c.drawString(17.3 * cm, 24.0 * cm, u'portal-erste-hilfe@ukh.de')
            # Adressdaten
            c.setFont(schriftartfett, 12)
            x = 23.5
            # Namensfelder werden nur ausgegeben wenn diese gefuellt sind
            mnr = adr.mnr.strip()
            if mnr != '':
                if ikg == 'K7':
                    c.drawString(2.5 * cm, x * cm, u'Einrichtungsnummer: ' + mnr)
                elif ikg == 'K9':
                    c.drawString(2.5 * cm, x * cm, u'Mitglieds- oder Betriebsnummer: ' + mnr)
                else:
                    c.drawString(2.5 * cm, x * cm, u'Mitgliedsnummer: ' + mnr)
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
            c.setFillColor(black)
            c.setFont(schriftartfett, 12)
            c.drawString(2.5 * cm, 18.5 * cm, u'Es stehen keine Berechtigungsscheine zur Verfügung!')
            c.drawString(2.5 * cm, 17.5 * cm, u'Möglicherweise sind alle Berechtigungsscheine aufgebraucht.')
            c.drawString(2.5 * cm, 16.9 * cm, u'Bitte setzen Sie sich gegebenenfalls mit der Unfallkasse Hessen')
            c.drawString(2.5 * cm, 16.3 * cm, u'unter der oben genannten Telefonnummer in Verbindung.')
        # ENDE und Save
        c.save()
        tmp.seek(0)
        return tmp.read()


class PDFOnlyBarcode(uvclight.Page):
    uvclight.layer(IUserLayer)
    uvclight.context(UserRoot)
    uvclight.auth.require('users.access')

    def make_response(self, result):
        response = self.responseFactory(app_iter=result)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = "%s" % (
            'attachment; filename="barcode.pdf"'
        )
        return response

    def render(self):
        tmp = tempfile.TemporaryFile()
        c = canvas.Canvas(tmp, pagesize=A4)
        c.setAuthor("UKH")
        c.setTitle(u'Erste-Hilfe')
        schriftart = "Helvetica"
        schriftartfett = "Helvetica-Bold"
        #datum = strftime("%d.%m.%Y", gmtime())
        principal = self.request.principal
        adr = principal.getAddress()
        LK1 = []
        LK2 = []
        LK3 = []
        LK4 = []
        LK5 = []
        LK6 = []
        LK7 = []
        LK8 = []
        LK9 = []
        LK10 = []
        LK11 = []
        LK13 = []
        for voucher in principal.getVouchers(cat=self.request.form.get('cat')):
            #if voucher.status.strip() == CREATED:
            if voucher.status.strip() == CREATED or voucher.status.strip() == MANUALLY_CREATED:
                if str(voucher.cat.strip()) == "K1":
                    LK1.append(str(voucher.oid))
                elif str(voucher.cat.strip()) == "K2":
                    LK2.append(str(voucher.oid))
                elif str(voucher.cat.strip()) == "K3":
                    LK3.append(str(voucher.oid))
                elif str(voucher.cat.strip()) == "K4":
                    LK4.append(str(voucher.oid))
                elif str(voucher.cat.strip()) == "K5":
                    LK5.append(str(voucher.oid))
                elif str(voucher.cat.strip()) == "K6":
                    LK6.append(str(voucher.oid))
                elif str(voucher.cat.strip()) == "K7":
                    LK7.append(str(voucher.oid))
                elif str(voucher.cat.strip()) == "K8":
                    LK8.append(str(voucher.oid))
                elif str(voucher.cat.strip()) == "K9":
                    LK9.append(str(voucher.oid))
                elif str(voucher.cat.strip()) == "K10":
                    LK10.append(str(voucher.oid))
                elif str(voucher.cat.strip()) == "K11":
                    LK11.append(str(voucher.oid))
                elif str(voucher.cat.strip()) == "K13":
                    LK13.append(str(voucher.oid))

        for bcode in [['K1', LK1], ['K2', LK2], ['K3', LK3], ['K4', LK4], ['K5', LK5],
                      ['K6', LK6], ['K7', LK7], ['K8', LK8], ['K9', LK9], ['K10', LK10],
                      ['K11', LK11], ['K13', LK13]]:
            x = 2
            x1 = 2.6
            y = 24
            y1 = y - 0.5
            if len(bcode[1]) > 0:
                ty = 28
                c.setFont(schriftartfett, 34)
                c.drawString(15.5 * cm, 27 * cm, bcode[0])
                c.setFont(schriftartfett, 11)
                # Namensfelder werden nur ausgegeben wenn diese gefuellt sind
                mnr = adr.mnr.strip()
                if mnr != '':
                    if bcode[0] == 'K7':
                        c.drawString(x1 * cm, ty * cm, u'Einrichtungsnummer: ' + mnr)
                    elif bcode[0] == 'K9':
                        c.drawString(x1 * cm, ty * cm, u'Mitglieds- oder Betriebsnummer: ' + mnr)
                    else:
                        c.drawString(x1 * cm, ty * cm, u'Mitgliedsnummer: ' + mnr)
                ty = ty - 0.7
                # Namensfelder werden nur ausgegeben wenn diese gefuellt sind
                c.drawString(x1 * cm, ty * cm, adr.name1.strip() + ' ' + adr.name2.strip())
                ty = ty - 0.5
                c.drawString(x1 * cm, ty * cm, adr.name3.strip())
                ty = ty - 0.5
                c.drawString(x1 * cm, ty * cm, adr.street.strip() + ' ' + adr.number.strip())
                ty = ty - 0.5
                c.drawString(x1 * cm, ty * cm, str(adr.zip_code) + ' ' + adr.city.strip())
                #####################################################
                c.setFont(schriftart, 10)
                for code in bcode[1]:
                    barcode = code128.Code128(code, barWidth = 0.4 * mm, barHeight = 9 * mm)
                    barcode.drawOn(c, x * cm, y * cm)
                    c.drawString(x1 * cm, y1 * cm, bcode[0] + '   ' + str(code))
                    x = x + 4
                    x1 += 4
                    if x == 18:
                        y = y - 3
                        y1 = y - 0.5
                        x = 2
                        x1 = x + 0.6
                    if y <= 2:
                        c.showPage()
                        y = 24
                        y1 = y - 0.5
                c.showPage()
        c.showPage()
        # ENDE und Save
        c.save()
        tmp.seek(0)
        return tmp.read()
