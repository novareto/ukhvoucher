# -*- coding: utf-8 -*-

from uuid import uuid1

import json
import uvclight
import datetime

from ukhvoucher.apps import UserRoot
from ukhvoucher.models import Voucher, Generation
from ukhvoucher.interfaces import IUserLayer
from ukhvoucher.interfaces import IKG1, IKG2, IKG3, IKG4, IKG5, IKG6, IKG7

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

            p = 1
            p = int(session.query(max(Generation.oid)).one()[0]) + 1
            print "GENERATION OID", 2
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
                    status = "created",
                    cat = form._iface.getName(),
                    user_id = principal.id,
                    generation_id = p,
                    )
                session.add(voucher)

            session.add(generation)
        amount = form.calculate(**data)
        insert(form, amount)
        form.flash(u'Wir haben %s Gutscheine erzeugt.', type="info")
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
    _iface = IKG1
    label = u""
    def calculate(self, mitarbeiter, standorte):
        if standorte <= 1:
            standorte = 2
        return (mitarbeiter * 5 / 100) + standorte


class IKG2Form(KGBaseForm):
    _iface = IKG2
    label = u""
    def calculate(self, mitarbeiter, standorte):
        if standorte <= 1:
            standorte = 2
        return (mitarbeiter * 10 / 100) + standorte


class IKG3Form(KGBaseForm):
    _iface = IKG3
    label = u""

    def calculate(self, gruppen, kitas):
        if kitas <= 1:
            kitas = 2
        return (gruppen + kitas)


class IKG4Form(KGBaseForm):
    _iface = IKG4
    label = u""

    def calculate(self, kolonne):
        return kolonne


class IKG5Form(KGBaseForm):
    _iface = IKG5
    label = u""

    def calculate(self, mitarbeiter):
        if mitarbeiter <= 1:
            mitarbeiter = 2
        return (mitarbeiter / 2)


class IKG6Form(KGBaseForm):
    _iface = IKG6
    label = u""

    def calculate(self, mitarbeiter):
        return mitarbeiter


class IKG7Form(KGBaseForm):
    _iface = IKG7
    label = u""

    def calculate(self, mitarbeiter):
        return mitarbeiter * 15 / 100

