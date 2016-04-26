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
from uvclight import action, layer, name, title, context, menu, order
from ul.auth import require
from dolmen.forms.base.components import _marker
from zope.interface import Interface

from ..interfaces import IVouchersCreation, IDisablingVouchers
from ..interfaces import IModel, IModelContainer, IAdminLayer, IUserLayer
from ..interfaces import IAccount, IJournalize
from ..models import Voucher, JournalEntry, Vouchers, Addresses
from .. import _, resources, DISABLED, CREATED
from ..apps import UserRoot
from uvc.entities.browser import IContextualActionsMenu, IDocumentActions


MULTI = set()

MULTI_DISABLED = set((
    "vouchers",
))


class DisableVoucherMenuItem(uvclight.MenuItem):
    menu(IContextualActionsMenu)
    context(Vouchers)
    title(u'Berechtigungsscheine sperren')
    name('disable_vouchers')
    order(50)


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
            self.flash(_(u'Es ist ein Fehler aufgetreten!'))
            return FAILURE


        if isinstance(self.context, Addresses):
            if data.get('oid') == '':
                data.pop('oid')
        print data
        item = self.context.model(**data)
        self.context.add(item)
        if 'oid' in data:
            oid = data['oid']
        else:
            session = get_session('ukhvoucher')
            session.flush()
            oid = item.oid

        # journalize
        if str(self.context.model.__label__) == "Kategorie":
            aktion = u"Kategorien manuell angelegt"
        elif str(self.context.model.__label__) == "Address":
            aktion = u"Adresse angelegt"
        elif str(self.context.model.__label__) == "Account":
            aktion = u"Neuen Benutzer angelegt"
        else:
            aktion = str(self.context.model.__label__)
        entry = JournalEntry(
            date=datetime.now().strftime('%Y-%m-%d'),
            userid=self.request.principal.id,
            action=aktion,
            #action=u"Bearbeitet: %s" % self.context.model.__label__,
            oid=oid,
            note=journal_note)
        self.context.add(entry)
        self.flash(_(u'Eintrag in der Historie hinzugefügt.'))
        self.redirect(self.application_url())
        return SUCCESS

    @action(_(u'Abbrechen'))
    def handle_cancel(self):
        self.redirect(self.application_url())
        return SUCCESS


@menuentry(IDocumentActions, order=10)
class EditModel(Form):
    context(IModel)
    name('edit')
    layer(IAdminLayer)
    require('manage.vouchers')
    title(u'Bearbeiten')

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

    @action(_(u'Änderung übernehmen'))
    def handle_save(self):
        data, errors = self.extractData()
        journal_note = data.pop('note')

        if errors:
            self.flash(_(u'Es ist ein Fehler aufgetreten!'))
            return FAILURE

        # apply new content values
        apply_data_event(self.fields, self.getContentData(), data)
        #self.flash(_(u"Content updated"))

        # journalize
        session = get_session('ukhvoucher')
        if str(self.context.__label__) == "Kategorie":
            aktion = u"Kategorien bearbeitet"
        elif str(self.context.__label__) == "Address":
            aktion = u"Adresse bearbeitet"
        elif str(self.context.__label__) == "Account":
            aktion = u"Benutzer bearbeitet"
        else:
            aktion = str(self.context.__label__)
        entry = JournalEntry(
            date=datetime.now().strftime('%Y-%m-%d'),
            userid=self.request.principal.id,
            action=aktion,
            oid=str(self.context.oid),
            note=journal_note)
        session.add(entry)
        self.flash(_(u'Eintrag in der Historie hinzugefügt.'))

        #entry = JournalEntry(
        #    date=datetime.now(),# .strftime('%Y-%m-%d'),
        #    userid=self.request.principal.id,
        #    action=u"Edited : %s" % self.context.__label__,
        #    oid=data['oid'],
        #    note=journal_note)
        #session = get_session('ukhvoucher')
        ##session.add(entry)

        self.redirect(self.application_url())
        return SUCCESS

    @action(_(u'Abbrechen'))
    def handle_cancel(self):
        self.redirect(self.application_url())
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

from dolmen.forms.base import Action, SuccessMarker
class CancelAction(Action):
    """Cancel the current form and return on the default content view.
     """
    def __call__(self, form):
        url = form.application_url()
        return SuccessMarker('Aborted', True, url=url)


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

    @property
    def actions(self):
        actions = super(EditAccount, self).actions
        #import pdb; pdb.set_trace()
        #if 'abbrechen' not in actions.keys():
        #    actions.extend(CancelAction(u"Abbrechen"))
        return actions.omit('cancel')


@menuentry(IDocumentActions, order=10)
class AskForVouchers(Form):
    context(IAccount)
    name('ask.vouchers')
    layer(IAdminLayer)
    require('manage.vouchers')
    title(u'Berechtigungsscheine bearbeiten')
    label = 'Berechtigungsscheine erzeugen'
    description = "Beschreibung"

    ignoreContent = True
    ignoreRequest = True

    fields = Fields(IVouchersCreation) + Fields(IJournalize)

    @property
    def action_url(self):
        return self.request.path

    def update(self):
        resources.ukhvouchers.need()

    @action(_(u'Erstellen'))
    def handle_save(self):
        data, errors = self.extractData()
        journal_note = data.pop('note')
        now = datetime.now()

        if errors:
            self.flash(_(u'Es ist ein Fehler aufgetreten!'))
            return FAILURE
        number = data.get('number', 0)
        if number:
            session = get_session('ukhvoucher')
            try:
                from sqlalchemy.sql.functions import max
                oid = int(session.query(max(Voucher.oid)).one()[0]) + 1
            except:
                oid = 100000
            from ukhvoucher.models import Generation
            import json

            p = int(session.query(max(Generation.oid)).one()[0]) + 1
            generation = Generation(
                oid=p,
                date=now.strftime('%Y-%m-%d'),
                type=data['kategorie'],
                data=json.dumps('Manuelle Erzeugung'),
                user=self.request.principal.id,
                uoid=oid
            )

            for idx in range(number):
                voucher = Voucher(
                    creation_date=datetime.now().strftime('%Y-%m-%d'),
                    status=CREATED,
                    cat = data['kategorie'],
                    user_id=self.context.oid,
                    generation_id=p,
                    oid=oid)
                oid += 1
                session.add(voucher)
            session.add(generation)

            # journalize
            entry = JournalEntry(
                date=datetime.now().strftime('%Y-%m-%d'),
                userid=self.request.principal.id,
                action=u"Berechtigungsscheine manuell erstellt",
                #action=u"Add:%s" % self.context.model.__label__,
                oid=str(self.context.oid),
                note=journal_note)
            session.add(entry)

            # redirect
            self.flash(_(u"%s Berechtigungsscheine erstellt" % number))
            self.redirect(self.application_url())
            return SUCCESS
        else:
            self.flash(_(u"The demand must be for at least 1 voucher."))
            self.redirect(self.url(self.context))
            return FAILURE

    @action(_(u'Abbrechen'))
    def handle_cancel(self):
        self.redirect(self.application_url())
        return SUCCESS


class DisableVouchers(Form):
    context(Interface)
    name('disable.vouchers')
    layer(IAdminLayer)
    require('manage.vouchers')
    title(u'Berechtigungsscheine sperren')
    label = 'Berechtigungsscheine sperren'
    description = "Beschreibung"

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

    @action(_(u'Berechtigungsscheine sperren'))
    def handle_save(self):
        data, errors = self.extractData()
        journal_note = data.pop('note')
        if errors:
            self.flash(_(u'Es ist ein Fehler aufgetreten!'))
            return FAILURE
        for voucher in data['vouchers']:
            voucher.status = DISABLED

        # journalize
        session = get_session('ukhvoucher')
        entry = JournalEntry(
            date=datetime.now().strftime('%Y-%m-%d'),
            userid=self.request.principal.id,
            #userid="admin", #str(self.request.principal.id),
            action=u"%s Berechtigungsscheine gesperrt" % len(data['vouchers']),
            oid=self.context.oid,
            note=journal_note)
        session.add(entry)

        self.flash(_(u"Berechtigungsschein(e) gesperrt"))
        self.redirect(self.application_url())
        return SUCCESS

    @action(_(u'Abbrechen'))
    def handle_cancel(self):
        self.redirect(self.application_url())
        return SUCCESS
