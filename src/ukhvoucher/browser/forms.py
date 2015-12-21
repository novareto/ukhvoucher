# -*- coding: utf-8 -*-

import uvclight

from datetime import datetime
from cromlech.sqlalchemy import get_session
from dolmen.forms.base.utils import apply_data_event
from dolmen.menu import menuentry

from uvc.design.canvas.menus import AddMenu
from uvc.design.canvas import IDocumentActions
from uvclight import Form, Fields, SUCCESS, FAILURE
from uvclight import action, layer, name, title, context
from ul.auth import require
from dolmen.forms.base.components import _marker

from ..interfaces import IVouchersCreation
from ..interfaces import IModel, IModelContainer, IAdminLayer, IUserLayer
from ..interfaces import IAccount
from ..models import Voucher
from .. import _, resources
from ..apps import UserRoot


MULTI = set()

MULTI_DISABLED = set((
    "vouchers",
))


@menuentry(AddMenu, order=10)
class CreateModel(Form):
    name('add')
    context(IModelContainer)
    layer(IAdminLayer)
    require('manage.vouchers')
    title(u'Objekt hinzufügen')

    dataValidators = []

    @property
    def fields(self):
        fields = Fields(self.context.model.__schema__)
        for field in fields:
            if field.identifier in MULTI:
                field.mode = 'multiselect'
            elif field.identifier in MULTI_DISABLED:
                field.mode = 'multidisabled'
        return fields

    def update(self):
        resources.ukhvouchers.need()

    @property
    def action_url(self):
        return self.request.path

    @action(_(u'Add'))
    def handle_save(self):
        data, errors = self.extractData()

        if errors:
            self.flash(_(u'An error occurred.'))
            return FAILURE

        # create it
        item = self.context.model(**data)
        self.context.add(item)

        # redirect
        base_url = self.url(self.context)
        self.flash(_(u'Added with success.'))
        self.redirect(base_url)
        return SUCCESS

    @action(_(u'Abbrechen'))
    def handle_cancel(self):
        base_url = self.url(self.context)
        self.redirect(base_url)
        return SUCCESS


@menuentry(IDocumentActions, order=10)
class EditModel(Form):
    context(IModel)
    name('edit')
    layer(IAdminLayer)
    require('manage.vouchers')
    title(u'Edit')

    ignoreContent = False
    ignoreRequest = True

    @property
    def fields(self):
        fields = Fields(self.context.__schema__)
        for field in fields:
            if field.identifier in MULTI:
                field.mode = 'multiselect'
            elif field.identifier in MULTI_DISABLED:
                field.mode = 'multidisabled'
        return fields

    def update(self):
        resources.ukhvouchers.need()

    @property
    def action_url(self):
        return self.request.path

    @action(_(u'Update'))
    def handle_save(self):
        data, errors = self.extractData()
        if errors:
            self.flash(_(u"An error occured"))
            return FAILURE

        apply_data_event(self.fields, self.getContentData(), data)
        self.flash(_(u"Content updated"))
        self.redirect(self.application_url())
        return SUCCESS

    @action(_(u'Cancel'))
    def handle_cancel(self):
        self.redirect(self.url(self.context))
        return SUCCESS


class ModelIndex(uvclight.Form):
    uvclight.name('index')
    uvclight.layer(IAdminLayer)
    uvclight.context(IModel)
    require('manage.vouchers')
    mode = 'display'

    ignoreContent = False
    ignoreRequest = True

    @property
    def label(self):
        return self.context.title

    @property
    def fields(self):
        fields = Fields(self.context.__schema__)
        return fields


class EditAccount(uvclight.EditForm):
    uvclight.name('edit_account')
    uvclight.layer(IUserLayer)
    uvclight.context(UserRoot)
    require('users.access')
    uvclight.title('Stammdaten')
    label = u"Stammdaten"
    description = u"Bitte geben Sie uns Ihre Stammdaten für Rückfragen"

    fields = Fields(IAccount).select('vname', 'nname', 'phone', 'email')

    def __init__(self, context, request, content=_marker):
        super(EditAccount, self).__init__(context, request)
        content = self.request.principal.getAccount()
        self.setContentData(content)


@menuentry(IDocumentActions, order=10)
class AskForVouchers(Form):
    context(IAccount)
    name('ask.vouchers')
    layer(IAdminLayer)
    require('manage.vouchers')
    title(u'Ask for vouchers')

    ignoreContent = True
    ignoreRequest = True

    fields = Fields(IVouchersCreation)

    @property
    def action_url(self):
        return self.request.path

    def update(self):
        resources.ukhvouchers.need()

    @action(_(u'Demand'))
    def handle_save(self):
        data, errors = self.extractData()
        if errors:
            self.flash(_(u"An error occured"))
            return FAILURE

        number = data.get('number', 0)
        if number:
            session = get_session('ukhvoucher')
            for idx in range(number, 0):
                voucher = Voucher(
                    creation_date=datetime.now(),
                    status='Pending',
                    user_id=self.context.oid)
                session.add(voucher)

            self.flash(_(u"Demanded %i vouchers" % number))
            self.redirect(self.application_url())
            return SUCCESS
        else:
            self.flash(_(u"The demand must be for at least 1 voucher."))
            self.redirect(self.url(self.context))
            return FAILURE

    @action(_(u'Cancel'))
    def handle_cancel(self):
        self.redirect(self.url(self.context))
        return SUCCESS
