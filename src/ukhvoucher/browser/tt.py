# -*- coding: utf-8 -*-

import uvclight
from ul.auth import require
from dolmen.forms.table.components import TableFormCanvas, TableActions
from dolmen.forms.base import Actions, Fields
from dolmen.forms.base.markers import NO_VALUE
from uvc.design.canvas import managers

from .search import Search
from .views import ContainerIndex
from .. import _
from ..interfaces import IModel, IModelContainer


class CancelVouchers(TableFormCanvas):
    #uvclight.context(IVouchers)

    fields = Fields()

    actions = Actions()
    tableActions = TableActions()

    batchSize = 10
    createBatch = False

    @property
    def tableFields(self):
        return self.context.getContent().listing_attrs

    def getItems(self):
        return self.context.results or []


from zope import interface
from cromlech.sqlalchemy import get_session
from ukhvoucher import models
from ..interfaces import IAdminLayer
from ukhvoucher import DISABLED, CREATED
from datetime import datetime

class GenerationView(uvclight.Page):
    uvclight.context(interface.Interface)
    uvclight.layer(IAdminLayer)
    uvclight.name('disable.charge')
    require('manage.vouchers')
    template = uvclight.get_template('generation_view.cpt', __file__)

    def getGenerations(self):
        rc = []
        session = get_session('ukhvoucher')
        generations = session.query(models.Generation).filter(
            models.Voucher.generation_id == models.Generation.oid,
            models.Voucher.user_id == int(self.request.principal.oid)).all()
        for generation in generations:
            for voucher in generation.voucher:
                if voucher.status.strip() == CREATED:
                    if generation not in rc:
                        rc.append(generation)
        return rc


class DCharge(uvclight.View):
    uvclight.context(interface.Interface)
    uvclight.layer(IAdminLayer)
    require('manage.vouchers')

    def update(self):
        gen_id = self.request.form.get('gen_id', None)
        if gen_id:
            session = get_session('ukhvoucher')
            generation = session.query(models.Generation).get(gen_id)
            for x in generation.voucher:
                if x.status.strip() == CREATED:
                    x.status = DISABLED

            entry = models.JournalEntry(
                date=datetime.now().strftime('%Y-%m-%d'),
                userid=self.request.principal.id,
                action=u"Charge Gelöscht",
                oid=str(self.context.oid),
                note="")
            session.add(entry)
        self.flash(u'Es wurden alle Gutscheine der Charge %s gesperrt.' % gen_id)
        self.redirect(self.application_url())

