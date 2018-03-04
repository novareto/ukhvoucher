# -*- coding: utf-8 -*-

import json
import uvclight
import datetime

from ukhvoucher import CREATED
from ukhvoucher.apps import UserRoot
from ukhvoucher.models import Voucher, Generation
from ukhvoucher.interfaces import IUserLayer
from ukhvoucher.interfaces import K1, K2, K3, K4, K5, K6, K7, K8, K9, K10, K11

from dolmen.forms.base.markers import FAILURE
from dolmen.forms.base import Action, SuccessMarker, Actions

from sqlalchemy.sql.functions import max
from cromlech.sqlalchemy import get_session
from .. import resources

from dolmen.forms.base.errors import Error


FEHLER01a = u"""
<h2> Ihre Angaben sind nicht plausibel. </h2>
<h3> Bitte prüfen Sie Ihre Angaben hinsichtlich der </h3>
<h3> - Anzahl der Beschäftigten </h3>
<h3> - Anzahl der angegebenen Standorte </h3>
<h3> Bitte beachten Sie, dass nur die Standorte zu berücksichtigen sind, </h3>
<h3> an denen gleichzeitig mindestens zwei Beschäftigte tätig sind. </h3>
<h3> Bei Fragen zur Antragsstellung wenden Sie sich bitte an das Service-Telefon </h3>
<h3> (069 29972-440, montags bis freitags von 7:30 bis 18:00 Uhr E-Mail: erste-hilfe@ukh.de).</h3>
"""

FEHLER01b = u"""
<h2> Ihre Angaben sind nicht plausibel. </h2>
<h3> Bitte prüfen Sie Ihre Angaben hinsichtlich der </h3>
<h3> - Anzahl der Kindergruppen </h3>
<h3> - Anzahl der angegebenen Kita Standorte </h3>
<h3> Die Anzahl der Standorte darf nicht größer sein als die Anzahl der Gruppen. </h3>
"""

FEHLER01c = u"""
<h2> Ihre Angaben sind nicht plausibel. </h2>
<h3> Bitte prüfen Sie Ihre Angaben hinsichtlich der </h3>
<h3> - Anzahl der Einsatzkräfte </h3>
<h3> - Anzahl der Betreuer </h3>
<h3> Die Anzahl der Betreuer darf nicht größer sein als die Anzahl der Einsatzkräfte. </h3>
"""

FEHLER02 = u"""
<h2> Es ist ein Fehler aufgetreten. </h2>
<h3> Bitte bestätigen Sie die Richtigkeit ihrer Angabe! </h3>
"""

FEHLER03 = u"""
<h2> Es ist ein Fehler aufgetreten. </h2>
<h3> Bitte bestätigen Sie die Richtigkeit ihrer Angaben! </h3>
"""

FEHLER04 = u"""
<h2> Es ist ein Fehler aufgetreten. </h2>
<h3> Eine Zahl ist kleiner oder gleich "0" </h3>
<h3> Bitte prüfen Sie Ihre Angaben! </h3>
"""

FEHLER04a = u"""
<h2> Es ist ein Fehler aufgetreten. </h2>
<h3> Anzahl Beschäftigte / Standorte Verwaltung und </h3>
<h3> Anzahl Beschäftigte / Standorte Technischer Bereich,</h3>
<h3> beide Bereiche wurden mit "0" angegeben.</h3>
<h3> Bitte prüfen Sie Ihre Angaben! </h3>
"""

FEHLER04b = u"""
<h2> Es ist ein Fehler aufgetreten. </h2>
<h3> Eine Zahl Anzahl Beschäftigte / Standorte Verwaltung ist kleiner oder gleich "0" </h3>
<h3> Bitte prüfen Sie Ihre Angaben! </h3>
"""

FEHLER04c = u"""
<h2> Es ist ein Fehler aufgetreten. </h2>
<h3> Eine Zahl Anzahl Beschäftigte / Standorte Technischer Bereich ist kleiner oder gleich "0" </h3>
<h3> Bitte prüfen Sie Ihre Angaben! </h3>
"""

class KontingentValidator(object):

    def __init__(self, fields, form):
        self.form = form
        self.fields = fields
        self.errors = []

    def validate(self, data):
        if data.get('bestaetigung') is False:
            if len(data) == 2:
                self.errors.append(Error(FEHLER02, identifier="form",),)
            else:
                self.errors.append(Error(FEHLER03, identifier="form",),)
        if data.get('bestaetigung') is True:
            # Nulleingabe
            # K11
            # Nulleingabe in beiden Bereichen K11
            verwaltung = True
            technik = True
            if data.get('ma_verwaltung') == 0  and data.get('st_verwaltung') == 0:
                verwaltung = False
            if data.get('ma_technik') == 0  and data.get('st_technik') == 0:
                technik = False
            if  verwaltung == False and technik == False:
                self.errors.append(Error(FEHLER04a, identifier="form",),)
                return self.errors
            # Nulleingabe Verwaltung K11
            if verwaltung == True:
                for x in ['ma_verwaltung', 'st_verwaltung']:
                    if data.get(x) is not None:
                        if data.get(x) == 0:
                            self.errors.append(Error(FEHLER04b, identifier="form",),)
                            return self.errors
            # Nulleingabe Technik K11
            if technik == True:
                for x in ['ma_technik', 'st_technik']:
                    if data.get(x) is not None:
                        if data.get(x) == 0:
                            self.errors.append(Error(FEHLER04c, identifier="form",),)
                            return self.errors
            # Nulleingabe die anderen Kontingente
            for x in ['mitarbeiter', 'standorte', 'kitas', 'gruppen', 'kolonne', 'lehrkraefte',
                      'schulstandorte', 'einsatzkraefte', 'betreuer']:
                if data.get(x) is not None:
                    if data.get(x) <= 0:
                        print x, data.get(x)
                        self.errors.append(Error(FEHLER04, identifier="form",),)
                        return self.errors
            if len(data) == 3:
                # K1 und K2
                if data.get('mitarbeiter'):
                    mitarbeiter = data.get('mitarbeiter')
                    standorte = data.get('standorte')
                    if str(mitarbeiter).isdigit() and str(standorte).isdigit():
                        mitarbeiter = mitarbeiter / 2
                        if mitarbeiter < standorte:
                            self.errors.append(Error(FEHLER01a, identifier="form",),)
                            return self.errors
                # K3
                if data.get('kitas'):
                    kitas = data.get('kitas')
                    gruppen = data.get('gruppen')
                    if str(kitas).isdigit() and str(gruppen).isdigit():
                        if int(gruppen) < int(kitas):
                            self.errors.append(Error(FEHLER01b, identifier="form",),)
                            return self.errors
                # K10
                if data.get('einsatzkraefte'):
                    ek = data.get('einsatzkraefte')
                    bt = data.get('betreuer')
                    if str(ek).isdigit() and str(bt).isdigit():
                        if int(ek) < int(bt):
                            self.errors.append(Error(FEHLER01c, identifier="form",),)
                            return self.errors

            # K11
            if len(data) == 5:
                if data.get('ma_verwaltung'):
                    z = 0
                    for i in range(2):
                        if z == 0:
                            mitarbeiter = data.get('ma_verwaltung')
                            standorte = data.get('st_verwaltung')
                        if z == 1:
                            mitarbeiter = data.get('ma_technik')
                            standorte = data.get('st_technik')
                        if str(mitarbeiter).isdigit() and str(standorte).isdigit():
                            mitarbeiter = mitarbeiter / 2
                            if mitarbeiter < standorte:
                                if len(self.errors) < 1:
                                    self.errors.append(Error(FEHLER01a, identifier="form",),)
                                    return self.errors
                        z = z + 1
        return self.errors


class CancelAction(Action):

    def __call__(self, form):
        url = form.application_url()
        return SuccessMarker('Aborted', True, url=url)


class CalculateInsert(Action):

    def __call__(self, form):
        data, errors = form.extractData()
        if 'merkmal' in data:
            # Das hier, ist für die Merkmale in K5 und K6 zuständig...
            z = 0
            s = data['merkmal']
            a = [ x for x in iter(s) ]
            merkmal = u'Beschäftigte: '
            for i in a:
                if len(a) > 1:
                    merkmal = merkmal + a[z] + ', '
                else:
                    merkmal = merkmal + a[z]
                z = z + 1
            data['merkmal'] = merkmal
        if errors:
            for x in errors:
                if x.title == "There were errors.":
                    x.title = "Es sind Fehler aufgetreten!"
                if x.title == "Missing required value.":
                    x.title = "Bitte tragen Sie zur Berechnung in diesem Feld eine Zahl ein!"
            form.submissionError = errors
            return FAILURE

        def insert(form, amount):
            now = datetime.datetime.now()
            principal = form.request.principal
            session = get_session('ukhvoucher')
            kat = form._iface.getName()
            cat_vouchers = principal.getVouchers(cat=kat)
            if len(cat_vouchers) > 0:
                form.flash(u'Die Berechtigungsscheine wurde für diese Kategorie bereits erzeugt.', type="info")
                url = form.application_url()
                return SuccessMarker('Success', True, url=url)
            try:
                oid = int(session.query(max(Voucher.oid)).one()[0]) + 1
            except:
                oid = 100000

            try:
                p = int(session.query(max(Generation.oid)).one()[0]) + 1
            except:
                p=1
            generation = Generation(
                oid=p,
                date=now.strftime('%Y-%m-%d'),
                type=form._iface.getName(),
                data=json.dumps(data),
                user=principal.id,
                uoid=oid
            )

            for i in range(amount):
                oid += 1
                voucher = Voucher(
                    oid = oid,
                    creation_date = now.strftime('%Y-%m-%d'),
                    status = CREATED,
                    cat = form._iface.getName(),
                    user_id = principal.oid,
                    generation_id = p,
                    )
                session.add(voucher)

            session.add(generation)
        amount = form.calculate(**data)
        insert(form, amount)
        form.flash(u'Wir haben %s Berechtigungsscheine erzeugt.', type="info")
        url = form.application_url()
        ### INVALIDATION
        principal = uvclight.utils.current_principal()
        principal.getVouchers(invalidate=True)
        return SuccessMarker('Success', True, url=url)

    
from zope.interface import Interface

class KGBaseForm(uvclight.Form):
    #uvclight.context(UserRoot)
    #uvclight.layer(IUserLayer)
    uvclight.context(Interface)
    uvclight.auth.require('users.access')
    #template = uvclight.get_template('catform.cpt', __file__)
    uvclight.baseclass()

    actions = Actions(
        CalculateInsert(u'Berechnen und eintragen', identifier="calculate"),
        CancelAction(u'Abbrechen')
    )

    @property
    def fields(self):
        fields = uvclight.Fields(self._iface)
        if 'bestaetigung' in fields.keys():
            fields['bestaetigung'].mode = "checkbox"
        return fields

    @property
    def formErrors(self):
        return [x for x in self.errors if x.identifier == "form"]

    def getErrorField(self, error):
        return ""
        field_name = error.identifier.split('.')[-1:][0]
        field = self.fields.get(field_name)
        return field.title


class K1Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 1 (K1) - Verwaltung, Büro                                 #
    # # Berechnung:                                                                #
    # # 5% der Beschäftigten (immer aufrunden !!!) KEIN Mathematisches runden!     #
    # # + 1 pro zusätzlichem Standort                                              #
    # # Standorte -1 (Der Hauptsitz wird abgezogen!)                               #
    # # mindestens 2 * Standorte                                                   #
    # ##############################################################################
    _iface = K1
    label = u""
    dataValidators = [KontingentValidator]

    #@property
    #def fields(self):
    #    fields = uvclight.Fields(self._iface)
    #    fields['mitarbeiter'].htmlAttributes = {'max': 999}
    #    #    fields['mitarbeiter'].htmlAttributes['max'] = 999
    #    #    #fields['mitarbeiter'].htmlAttributes['maxlength'] = 3
    #    return fields

    def calculate(self, mitarbeiter, standorte, bestaetigung):
        originalstandorte = standorte
        standorte = standorte - 1
        # Immer Aufrunden !
        mitarbeiter = float(mitarbeiter)
        ma = mitarbeiter * 5 / 100
        mitarbeiter = str(ma)
        lma = len(mitarbeiter) - 2
        rundung = mitarbeiter[lma:]
        mitarbeiter = float(mitarbeiter)
        mitarbeiter = int(mitarbeiter)
        if rundung[:1] == '.':
            rundung = rundung[1:]
        if rundung != '0':
            mitarbeiter = mitarbeiter + 1
        # mitarbeiter + standorte
        ergebniseingabe = mitarbeiter + standorte
        mindestmenge_2_je_standort = originalstandorte * 2
        kontingent = ergebniseingabe
        if mindestmenge_2_je_standort > kontingent:
            kontingent = mindestmenge_2_je_standort
        return kontingent


class K2Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 2 (K2) - Sonstige Betriebe                                #
    # # Berechnung:                                                                #
    # # 10% der Beschäftigten (immer aufrunden !!!) KEIN Mathematisches runden!    #
    # # + 1 pro zusätzlichem Standort                                              #
    # # Standorte -1 (Der Hauptsitz wird abgezogen!)                               #
    # # mindestens 2 * Standorte                                                   #
    # ##############################################################################
    _iface = K2
    label = u""
    dataValidators = [KontingentValidator]

    def calculate(self, mitarbeiter, standorte, bestaetigung):
        originalstandorte = standorte
        standorte = standorte - 1
        mitarbeiter = float(mitarbeiter)
        ma = mitarbeiter * 10 / 100
        mitarbeiter = str(ma)
        lma = len(mitarbeiter) - 2
        rundung = mitarbeiter[lma:]
        mitarbeiter = float(mitarbeiter)
        mitarbeiter = int(mitarbeiter)
        if rundung[:1] == '.':
            rundung = rundung[1:]
        if rundung != '0':
            mitarbeiter = mitarbeiter + 1
        # mitarbeiter + standorte
        ergebniseingabe = mitarbeiter + standorte
        mindestmenge_2_je_standort = originalstandorte * 2
        kontingent = ergebniseingabe
        if mindestmenge_2_je_standort > kontingent:
            kontingent = mindestmenge_2_je_standort
        return kontingent


class K3Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 3 (K3) - Kindertageseinrichtungen                         #
    # # Berechnung:                                                                #
    # # Gruppen + Kitas                                                            #
    # # mindestens 2 * Standorte                                                   #
    # ##############################################################################
    _iface = K3
    label = u""
    dataValidators = [KontingentValidator]

    def calculate(self, gruppen, kitas, bestaetigung):
        ergebniseingabe = int(gruppen) + int(kitas)
        return ergebniseingabe
        mindestmenge_2_je_standort = kitas * 2
        kontingent = ergebniseingabe
        if mindestmenge_2_je_standort > kontingent:
            kontingent = mindestmenge_2_je_standort
        return kontingent


class K4Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 4 (K4) - Bauhof Entsorgung                                #
    # # Berechnung:                                                                #
    # # Kolonnen: Eingabe = Ausgabe                                                #
    # ##############################################################################
    _iface = K4
    label = u""
    dataValidators = [KontingentValidator]

    def calculate(self, kolonne, bestaetigung):
        return kolonne


class K5Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 5 (K5) - Erhöhte Gefährdung                               #
    # # Berechnung:                                                                #
    # # 50% der Beschäftigten (immer aufrunden !!!) KEIN Mathematisches runden!    #
    # ##############################################################################
    _iface = K5
    label = u""
    dataValidators = [KontingentValidator]

    #def calculate(self, merkmal, mitarbeiter, bestaetigung):
    def calculate(self, mitarbeiter, bestaetigung):
        # Immer Aufrunden !
        mitarbeiter = float(mitarbeiter)
        ma = mitarbeiter * 50 / 100
        mitarbeiter = str(ma)
        lma = len(mitarbeiter) - 2
        rundung = mitarbeiter[lma:]
        mitarbeiter = float(mitarbeiter)
        mitarbeiter = int(mitarbeiter)
        if rundung[:1] == '.':
            rundung = rundung[1:]
        if rundung != '0':
            mitarbeiter = mitarbeiter + 1
        return mitarbeiter


class K6Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 6 (K6) - Besonders hohe Gefährdung                        #
    # # Berechnung:                                                                #
    # # Kolonnen: Eingabe = Ausgabe                                                #
    # ##############################################################################
    _iface = K6
    label = u""
    dataValidators = [KontingentValidator]

    #def calculate(self, merkmal, mitarbeiter, bestaetigung):
    def calculate(self, mitarbeiter, bestaetigung):
        return mitarbeiter


class K7Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 7 (K7) - Lehrkräfte                                       #
    # # Berechnung:                                                                #
    # # 15% der Beschäftigten (immer aufrunden !!!) KEIN Mathematisches runden!    #
    # ##############################################################################
    _iface = K7
    label = u""
    dataValidators = [KontingentValidator]

    def calculate(self, lehrkraefte, bestaetigung):
        mitarbeiter = lehrkraefte
        # Immer Aufrunden !!!!!!!!!!
        mitarbeiter = float(mitarbeiter)
        ma = mitarbeiter * 15 / 100
        mitarbeiter = str(ma)
        lma = len(mitarbeiter) - 2
        rundung = mitarbeiter[lma:]
        mitarbeiter = float(mitarbeiter)
        mitarbeiter = int(mitarbeiter)
        if rundung[:1] == '.':
            rundung = rundung[1:]
        if rundung != '0':
            mitarbeiter = mitarbeiter + 1
        return mitarbeiter

    def update(self):
        print "UPDATE FORM"
        print self.request.form


class K8Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 8 (K8) - Schulstandorte                                   #
    # # Berechnung:                                                                #
    # # Standort: Eingabe = Ausgabe                                                #
    # ##############################################################################
    _iface = K8
    label = u""
    dataValidators = [KontingentValidator]

    def calculate(self, schulstandorte, bestaetigung):
        return schulstandorte


class K9Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 9 (K9) - Schulbetreuung                                   #
    # # Berechnung:                                                                #
    # # Gruppen: Eingabe = Ausgabe                                                 #
    # ##############################################################################
    _iface = K9
    label = u""
    dataValidators = [KontingentValidator]

    def calculate(self, gruppen, bestaetigung):
        return gruppen


class K10Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 10 (K10) - Freiwillige Feuerwehren                        #
    # # Berechnung:                                                                #
    # # Einsatzkräfte: 10% (immer aufrunden !!!) KEIN Mathematisches runden!       #
    # # Betreuer/innen: Eingabe = Ausgabe                                          #
    # ##############################################################################
    _iface = K10
    label = u""
    dataValidators = [KontingentValidator]

    def calculate(self, einsatzkraefte, betreuer, bestaetigung):
        mitarbeiter = einsatzkraefte
        # Immer Aufrunden !
        mitarbeiter = float(mitarbeiter)
        ma = mitarbeiter * 10 / 100
        mitarbeiter = str(ma)
        lma = len(mitarbeiter) - 2
        rundung = mitarbeiter[lma:]
        mitarbeiter = float(mitarbeiter)
        mitarbeiter = int(mitarbeiter)
        if rundung[:1] == '.':
            rundung = rundung[1:]
        if rundung != '0':
            mitarbeiter = mitarbeiter + 1
        # mitarbeiter + betreuer
        return mitarbeiter + betreuer


class K11Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 11 (K11) - Gesundheitsdienste                             #
    # # Berechnung Verwaltung:                                                     #
    # # 5% der Beschäftigten (immer aufrunden !!!) KEIN Mathematisches runden!     #
    # # + 1 pro zusätzlichem Standort                                              #
    # # Standorte -1 (Der Hauptsitz wird abgezogen!)                               #
    # # Berechnung Technische Bereiche:                                            #
    # # 10% der Beschäftigten (immer aufrunden !!!) KEIN Mathematisches runden!    #
    # # + 1 pro zusätzlichem Standort                                              #
    # # Standorte -1 (Der Hauptsitz wird abgezogen!)                               #
    # ##############################################################################
    _iface = K11
    label = u""
    dataValidators = [KontingentValidator]

    def calculate(self, ma_verwaltung, st_verwaltung, ma_technik, st_technik, bestaetigung):
        ##############################################
        ### Verwaltung                             ###
        ##############################################
        if ma_verwaltung <= 0 and st_verwaltung <= 0:
            kontingent1 = 0
        else:
            mitarbeiter = ma_verwaltung
            standorte = st_verwaltung
            ##############################################
            originalstandorte = standorte
            standorte = standorte - 1
            # Immer Aufrunden !
            mitarbeiter = float(mitarbeiter)
            ma = mitarbeiter * 5 / 100
            mitarbeiter = str(ma)
            lma = len(mitarbeiter) - 2
            rundung = mitarbeiter[lma:]
            mitarbeiter = float(mitarbeiter)
            mitarbeiter = int(mitarbeiter)
            if rundung[:1] == '.':
                rundung = rundung[1:]
            if rundung != '0':
                mitarbeiter = mitarbeiter + 1
            # mitarbeiter + standorte
            ergebniseingabe = mitarbeiter + standorte
            mindestmenge_2_je_standort = originalstandorte * 2
            kontingent = ergebniseingabe
            if mindestmenge_2_je_standort > kontingent:
                kontingent = mindestmenge_2_je_standort
            kontingent1 = kontingent
            ##############################################

        ##############################################
        ### Technische Bereiche                    ###
        ##############################################
        if ma_technik <= 0 and st_technik <= 0:
            kontingent2 = 0
        else:
            mitarbeiter = ma_technik
            standorte = st_technik
            ##############################################
            originalstandorte = standorte
            standorte = standorte - 1
            # Immer Aufrunden !
            mitarbeiter = float(mitarbeiter)
            ma = mitarbeiter * 10 / 100
            mitarbeiter = str(ma)
            lma = len(mitarbeiter) - 2
            rundung = mitarbeiter[lma:]
            mitarbeiter = float(mitarbeiter)
            mitarbeiter = int(mitarbeiter)
            if rundung[:1] == '.':
                rundung = rundung[1:]
            if rundung != '0':
                mitarbeiter = mitarbeiter + 1
            # mitarbeiter + standorte
            ergebniseingabe = mitarbeiter + standorte
            mindestmenge_2_je_standort = originalstandorte * 2
            kontingent = ergebniseingabe
            if mindestmenge_2_je_standort > kontingent:
                kontingent = mindestmenge_2_je_standort
            kontingent2 = kontingent
        return kontingent1 + kontingent2
