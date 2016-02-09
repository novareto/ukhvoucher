# -*- coding: utf-8 -*-

import uvclight
from uuid import uuid1
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
from zope.interface import Interface

from ..interfaces import IVouchersCreation, IDisablingVouchers
from ..interfaces import IModel, IModelContainer, IAdminLayer, IUserLayer
from ..interfaces import IAccount, IJournalize
from ..models import Voucher, JournalEntry
from .. import _, resources, DISABLED
from ..apps import UserRoot


MULTI = set()

MULTI_DISABLED = set((
    "vouchers",
))


@menuentry(IDocumentActions, order=10)
class DisableVouchers(Form):
    context(Interface)
    name('disable_vouchers')
    layer(IAdminLayer)
    require('manage.vouchers')
    title(u'Disable vouchers')

    ignoreContent = True
    ignoreRequest = False

    @property
    def fields(self):
        fields = Fields(IDisablingVouchers) + Fields(IJournalize)
        fields['vouchers'].mode = 'multidisabled'
        return fields

    def update(self):
        resources.ukhvouchers.need()

    @property
    def action_url(self):
        return self.request.path

    @action(_(u'Disable'))
    def handle_save(self):
        data, errors = self.extractData()
        journal_note = data.pop('note')
        if errors:
            self.flash(_(u"An error occured"))
            return FAILURE

        for voucher in data['vouchers']:
            voucher.status = DISABLED

        # journalize
        session = get_session('ukhvoucher')
        entry = JournalEntry(
            jid=str(uuid1()),
            date=datetime.now(),
            userid=self.request.principal.id,
            action=u"Disabled vouchers : %s" % ', '.join(data['vouchers']),
            note=journal_note)
        session.add(entry)
            
        self.flash(_(u"Voucher(s) disabled"))
        self.redirect(self.application_url())
        return SUCCESS

    @action(_(u'Cancel'))
    def handle_cancel(self):
        self.redirect(self.url(self.context))
        return SUCCESS


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

        journal = Fields(IJournalize)
        journal['note'].ignoreContent = True
                
        return fields + journal

    def update(self):
        resources.ukhvouchers.need()

    @property
    def action_url(self):
        return self.request.path

    @action(_(u'Add'))
    def handle_save(self):
        data, errors = self.extractData()
        journal_note = data.pop('note')
        
        if errors:
            self.flash(_(u'An error occurred.'))
            return FAILURE

        # create it
        item = self.context.model(**data)
        self.context.add(item)

        # redirect
        base_url = self.url(self.context)
        self.flash(_(u'Added with success.'))

        # journalize
        entry = JournalEntry(
            jid=str(uuid1()),
            date=datetime.now(),
            userid=self.request.principal.id,
            action=u"Add : %s" % self.context.model.__label__,
            note=journal_note)
        self.context.add(entry)

        # redirect
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

        journal = Fields(IJournalize)
        journal['note'].ignoreContent = True

        return fields + journal

    def update(self):
        resources.ukhvouchers.need()

    @property
    def action_url(self):
        return self.request.path

    @action(_(u'Update'))
    def handle_save(self):
        data, errors = self.extractData()
        journal_note = data.pop('note')
        
        if errors:
            self.flash(_(u"An error occured"))
            return FAILURE

        # apply new content values
        apply_data_event(self.fields, self.getContentData(), data)
        self.flash(_(u"Content updated"))

        # journalize
        entry = JournalEntry(
            jid=str(uuid1()),
            date=datetime.now(),
            userid=self.request.principal.id,
            action=u"Edited : %s" % self.context.__label__,
            note=journal_note)
        self.context.add(entry)

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

    fields = Fields(IVouchersCreation) + Fields(IJournalize)

    @property
    def action_url(self):
        return self.request.path

    def update(self):
        resources.ukhvouchers.need()

    @action(_(u'Demand'))
    def handle_save(self):
        data, errors = self.extractData()
        journal_note = data.pop('note')

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

            # journalize
            entry = JournalEntry(
                jid=str(uuid1()),
                date=datetime.now(),
                userid=self.request.principal.id,
                action=u"Created %n vouchers" % number,
                note=journal_note)
            session.add(entry)

            # redirect
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
