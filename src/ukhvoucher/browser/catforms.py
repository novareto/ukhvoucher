# -*- coding: utf-8 -*-


import uvclight
import datetime

from ukhvoucher.apps import UserRoot
from ukhvoucher.models import Voucher
from ukhvoucher.interfaces import IUserLayer
from ukhvoucher.interfaces import IKG1, IKG2, IKG3

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
        def insert(form, amount):
            session = get_session('ukhvoucher')
            now = datetime.datetime.now()
            principal = form.request.principal
            oid = int(session.query(max(Voucher.oid)).one()[0]) + 1
            if not oid:
                oid = 0
            for i in range(amount):
                oid += 1 
                voucher = Voucher()
                voucher.oid = oid
                voucher.creation_date = now
                voucher.status = "created"
                voucher.cat = form._iface.getName()
                voucher.user_id = principal.id
                session.add(voucher)
        data, errors = form.extractData()
        if errors:
            form.submissionError = errors
            return FAILURE
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
    label = u"KG1"
    
    def calculate(self, mitarbeiter, standorte):
        if standorte <= 1:
            standorte = 2
        return (mitarbeiter * 5 / 100) + standorte


class IKG2Form(KGBaseForm):
    _iface = IKG2
    label = u"KG2"
    
    def calculate(self, mitarbeiter, standorte):
        if standorte <= 1:
            standorte = 2
        return (mitarbeiter * 10 / 100) + standorte
