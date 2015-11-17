# -*- coding: utf-8 -*-

import uvclight

from datetime import datetime
from cromlech.sqlalchemy import get_session
from dolmen.forms.base.markers import NO_VALUE
from dolmen.forms.base.errors import Error
from dolmen.forms.base import SuccessMarker
from dolmen.forms.base import makeAdaptiveDataManager
from dolmen.forms.base.utils import set_fields_data, apply_data_event
from dolmen.forms.crud.actions import message
from dolmen.menu import menuentry, order

from uvc.design.canvas.menus import AddMenu
from uvc.design.canvas import IContextualActionsMenu, IPersonalMenu
from uvc.design.canvas import IDocumentActions
from uvclight.form_components.fields import Captcha
from uvclight import Form, EditForm, DeleteForm, Fields, SUCCESS, FAILURE
from uvclight import action, layer, name, title, get_template, context
from ul.auth import require

from ..interfaces import IVouchersCreation
from ..interfaces import IModel, IModelContainer, IAdminLayer
from ..interfaces import IAccount, IVoucher, IInvoice, IAddress
from .. import _, resources


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
        return Fields(self.context.__schema__)

    @property
    def action_url(self):
        return self.request.path

    def update(self):
        resources.ukhvouchers.need()

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
    def fields(self):
        return Fields(self.context.__schema__)


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
