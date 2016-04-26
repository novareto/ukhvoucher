# -*- coding: utf-8 -*-

import json
import uvclight
import datetime

from ukhvoucher import CREATED
from ukhvoucher.apps import UserRoot
from ukhvoucher.models import Voucher, Generation
from ukhvoucher.interfaces import IUserLayer
from ukhvoucher.interfaces import IKG1, IKG2, IKG3, IKG4, IKG5, IKG6, IKG7, IKG8, IKG9

from dolmen.forms.base.markers import FAILURE
from dolmen.forms.base import Action, SuccessMarker, Actions

from sqlalchemy.sql.functions import max
from cromlech.sqlalchemy import get_session


class CancelAction(Action):

    def __call__(self, form):
        url = form.application_url()
        return SuccessMarker('Aborted', True, url=url)


class CalculateInsert(Action):

    def __call__(self, form):
        data, errors = form.extractData()
        if 'merkmal' in data:
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
            form.submissionError = errors
            return FAILURE

        def insert(form, amount):
            now = datetime.datetime.now()
            principal = form.request.principal
            session = get_session('ukhvoucher')
            try:
                oid = int(session.query(max(Voucher.oid)).one()[0]) + 1
            except:
                oid = 100000

            try:
                p = int(session.query(max(Generation.oid)).one()[0]) + 1
            except:
                p=1
            print "GENERATION OID", p
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
        return SuccessMarker('Success', True, url=url)


class KGBaseForm(uvclight.Form):
    uvclight.context(UserRoot)
    uvclight.layer(IUserLayer)
    uvclight.auth.require('users.access')
    uvclight.baseclass()

    actions = Actions(
        CalculateInsert(u'Berechnen und eintragen', identifier="calculate"),
        CancelAction(u'Abbrechen')
    )

    @property
    def fields(self):
        return uvclight.Fields(self._iface)


class IKG1Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 1 (K1) - Verwaltung, Büro                                 #
    # # Berechnung:                                                                #
    # # 5% der Beschäftigten (immer aufrunden !!!) KEIN Mathematisches runden!     #
    # # + 1 pro zusätzlichem Standort                                              #
    # # Standorte -1 (Der Hauptsitz wird abgezogen!)                               #
    # # mindestens 2 * Standorte                                                   #
    # ##############################################################################
    _iface = IKG1
    label = u""

    def calculate(self, mitarbeiter, standorte):
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


class IKG2Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 2 (K2) - Sonstige Betriebe                                #
    # # Berechnung:                                                                #
    # # 10% der Beschäftigten (immer aufrunden !!!) KEIN Mathematisches runden!    #
    # # + 1 pro zusätzlichem Standort                                              #
    # # Standorte -1 (Der Hauptsitz wird abgezogen!)                               #
    # # mindestens 2 * Standorte                                                   #
    # ##############################################################################
    _iface = IKG2
    label = u""

    def calculate(self, mitarbeiter, standorte):
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


class IKG3Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 3 (K3) - Kindertageseinrichtungen                         #
    # # Berechnung:                                                                #
    # # Gruppen + Kitas                                                            #
    # # mindestens 2 * Standorte                                                   #
    # ##############################################################################
    _iface = IKG3
    label = u""

    def calculate(self, gruppen, kitas):
        ergebniseingabe = gruppen + kitas
        mindestmenge_2_je_standort = kitas * 2
        kontingent = ergebniseingabe
        if mindestmenge_2_je_standort > kontingent:
            kontingent = mindestmenge_2_je_standort
        return kontingent


class IKG4Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 4 (K4) - Bauhof Entsorgung                                #
    # # Berechnung:                                                                #
    # # Kolonnen: Eingabe = Ausgabe                                                #
    # ##############################################################################
    _iface = IKG4
    label = u""

    def calculate(self, kolonne):
        return kolonne


class IKG5Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 5 (K5) - Erhöhte Gefährdung                               #
    # # Berechnung:                                                                #
    # # 50% der Beschäftigten (immer aufrunden !!!) KEIN Mathematisches runden!    #
    # ##############################################################################
    _iface = IKG5
    label = u""

    def calculate(self, merkmal, mitarbeiter):
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


class IKG6Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 6 (K6) - Besonders hohe Gefährdung                        #
    # # Berechnung:                                                                #
    # # Kolonnen: Eingabe = Ausgabe                                                #
    # ##############################################################################
    _iface = IKG6
    label = u""

    def calculate(self, merkmal, mitarbeiter):
        return mitarbeiter


class IKG7Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 7 (K7) - Lehrkräfte                                       #
    # # Berechnung:                                                                #
    # # 15% der Beschäftigten (immer aufrunden !!!) KEIN Mathematisches runden!    #
    # ##############################################################################
    _iface = IKG7
    label = u""

    def calculate(self, lehrkraefte):
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


class IKG8Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 8 (K8) - Schulstandorte                                   #
    # # Berechnung:                                                                #
    # # Standort: Eingabe = Ausgabe                                                #
    # ##############################################################################
    _iface = IKG8
    label = u""

    def calculate(self, mitarbeiter):
        return mitarbeiter


class IKG9Form(KGBaseForm):
    # ##############################################################################
    # # Kontingentgruppe 9 (K9) - Schulbetreuung                                   #
    # # Berechnung:                                                                #
    # # Gruppen: Eingabe = Ausgabe                                                 #
    # ##############################################################################
    _iface = IKG9
    label = u""

    def calculate(self, gruppen):
        return gruppen
