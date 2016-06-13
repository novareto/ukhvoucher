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

class GenerationView(uvclight.Page):
    uvclight.context(interface.Interface)
    uvclight.layer(IAdminLayer)
    require('manage.vouchers')
    template = uvclight.get_template('generation_view.cpt', __file__)

    def getGenerations(self):
        session = get_session('ukhvoucher')
        generations = session.query(models.Generation).filter(
            models.Voucher.generation_id == models.Generation.oid,
            models.Voucher.user_id == int(self.request.principal.oid)).all()
        return generations

