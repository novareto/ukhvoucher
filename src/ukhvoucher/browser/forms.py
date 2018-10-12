# -*- coding: utf-8 -*-

import uvclight
from uuid import uuid1
from datetime import datetime

from cromlech.sqlalchemy import get_session
from dolmen.forms.base.components import _marker
from dolmen.forms.base.utils import apply_data_event
from dolmen.menu import menuentry
from ul.auth import require
from uvc.design.canvas import IDocumentActions
from uvc.design.canvas.menus import AddMenu
from uvc.entities.browser import IContextualActionsMenu, IDocumentActions
from uvclight import Form, Fields, SUCCESS, FAILURE
from uvclight import action, layer, name, title, context, menu, order
from zope.interface import Interface

from ..interfaces import IVouchersCreation, IDisablingVouchers
from ..interfaces import IModel, IModelContainer, IAdminLayer, IUserLayer
from ..interfaces import IAccount, IJournalize, IJournalEntry, IJournalEntryExt
from ..interfaces import IKontakt
from ..models import Voucher, JournalEntry, Vouchers, Addresses, Invoices, Invoice, Accounts, Journal
from .. import _, resources, DISABLED, CREATED, MANUALLY_CREATED
from ..apps import UserRoot


MULTI = set()

MULTI_DISABLED = set((
    "vouchers_",
))


#class DisableVoucherMenuItem(uvclight.MenuItem):
#    menu(IContextualActionsMenu)
#    context(Vouchers)
#    title(u'Berechtigungsscheine sperren')
#    name('disable_vouchers')
#    order(50)


#@menuentry(AddMenu, order=10)
class CreateModel(Form):
    name('add')
    context(IModelContainer)
    layer(IAdminLayer)
    require('manage.vouchers')
    title(u'Objekt hinzufügen')

    dataValidators = []

    @property
    def label(self):
        labeltext = u''
        label = self.context.model.__label__
        if label == 'Address':
            labeltext = u'Neue Adresse hinzufügen'
        if label == 'Account':
            labeltext = u'Neuen Benutzer hinzufügen'
        if label == 'Kontingent':
            labeltext = u'Zuordnung des Kontingents neu erstellen'
        if label == 'Zuordnung':
            labeltext = u'Neue Zuordnung von Berechtigungsscheinen erstellen'
        return labeltext

    def getErrorField(self, error):
        return ""

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

        if hasattr(self.context.model, 'widget_arrangements'):
            self.context.model.widget_arrangements(fields)

        if isinstance(self.context, Invoices):
            fields = fields.omit('creation_date')

        return fields + journal

    def update(self):
        resources.ukhvouchers.need()
        resources.ehcss.need()

    def updateWidgets(self):
        super(CreateModel, self).updateWidgets()
        #import pdb; pdb.set_trace()
        if 'form.field.vouchers' in self.fieldWidgets:
            field_id = self.fieldWidgets.get('form.field.vouchers')
            field_id.template = uvclight.get_template('select.cpt', __file__)

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
        if isinstance(self.context, Invoices):
            if data.get('oid') == '':
                data.pop('oid')
        if isinstance(self.context, Accounts):
            data['rollen'] = ''
            data['merkmal'] = 'E'
        item = self.context.model(**data)
        self.context.add(item)
        if 'oid' in data and data['oid'] != '':
            oid = data['oid']
        else:
            session = get_session('ukhvoucher')
            session.flush()
            oid = item.oid
        # journalize
        if str(self.context.model.__label__) == "Kontingent":
            aktion = u"Kontingente manuell angelegt"
        elif str(self.context.model.__label__) == "Address":
            aktion = u"Adresse angelegt"
        elif str(self.context.model.__label__) == "Account":
            aktion = u"Neuen Benutzer angelegt"
        elif str(self.context.model.__label__) == "Zuordnung":
            aktion = u"Neue Zuordnung angelegt"
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
        if isinstance(self.context, Invoices):
            self.flash('Die Zuordnung wurde unter der Nummer %s gespeichert' % oid)
        self.redirect(self.application_url())
        return SUCCESS

    @action(_(u'Abbrechen'))
    def handle_cancel(self):
        self.redirect(self.application_url())
        return SUCCESS


#@menuentry(IDocumentActions, order=10)
class EditModel(Form):
    context(IModel)
    name('edit')
    layer(IAdminLayer)
    require('manage.vouchers')
    title(u'Bearbeiten')

    ignoreContent = False
    ignoreRequest = True

    @property
    def label(self):
        labeltext = u''
        label = self.context.__label__
        if label == 'Address':
            labeltext = u'Adresse bearbeiten'
        if label == 'Account':
            labeltext = u'Benutzer bearbeiten'
        if label == 'Kontingent':
            labeltext = u'Zuordnung der Kontingente bearbeiten'
        if label == 'Zuordnung':
            labeltext = u'Zuordnung von Berechtigungsscheinen bearbeiten'
        return labeltext

    def updateWidgets(self):
        super(EditModel, self).updateWidgets()
        #import pdb; pdb.set_trace()
        if 'form.field.vouchers' in self.fieldWidgets:
            field_id = self.fieldWidgets.get('form.field.vouchers')
            field_id.template = uvclight.get_template('select.cpt', __file__)

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

        if hasattr(self.context, 'widget_arrangements'):
            self.context.widget_arrangements(fields)
        return fields + journal

    def update(self):
        resources.ukhvouchers.need()
        resources.ehcss.need()

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

        if isinstance(self.context, Invoice):
            data.pop('oid')
        apply_data_event(self.fields, self.getContentData(), data)

        # journalize
        session = get_session('ukhvoucher')
        if str(self.context.__label__) == "Kontingent":
            aktion = u"Kontingente bearbeitet"
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
        self.redirect(self.url(self.context.__parent__))
        return SUCCESS

    @action(_(u'Abbrechen'))
    def handle_cancel(self):
        self.redirect(self.url(self.context.__parent__))
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
    description = u"Bitte geben Sie Ihre Stammdaten an:"

    fields = Fields(IAccount).select('anrede', 'titel', 'vname', 'nname', 'vorwahl', 'phone', 'email', 'funktion')
    fields['vname'].htmlAttributes = {'maxlength': 30}
    fields['nname'].htmlAttributes = {'maxlength': 30}
    fields['vorwahl'].htmlAttributes = {'maxlength': 6}
    fields['phone'].htmlAttributes = {'maxlength': 15}
    fields['email'].htmlAttributes = {'maxlength': 79}
    fields['funktion'].htmlAttributes = {'maxlength': 50}
    fields['titel'].htmlAttributes = {'maxlength': 15}

    def __init__(self, context, request, content=_marker):
        super(EditAccount, self).__init__(context, request)
        resources.ehcss.need()
        content = self.request.principal.getAccount(invalidate=True)
        self.setContentData(content)

    @property
    def actions(self):
        actions = super(EditAccount, self).actions
        na = actions.omit('cancel')
        ca = CancelAction(u'Abbrechen')
        na.append(ca)
        return na

    def getErrorField(self, error):
        return ""


class ChangePW(EditAccount):
    uvclight.name('change_pw')
    uvclight.title(u'Passwort ändern')
    label = u"Passwort ändern"
    description = u"Hier können Sie ihr Passwort ändern"
    ignoreContent = False

    fields = Fields(IAccount).select('password')


#@menuentry(IDocumentActions, order=10)
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
    fields['number'].htmlAttributes = {'maxlength': 3}

    @property
    def action_url(self):
        return self.request.path

    def update(self):
        resources.ukhvouchers.need()
        resources.ehcss.need()

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

            p = int(session.query(max(Generation.oid)).one()[0] or 0) + 1

            generation = Generation(
                oid=p,
                date=now.strftime('%Y-%m-%d'),
                type=data['kategorie'],
                data=json.dumps('Manuelle Erzeugung'),
                user=str(self.context.oid),
                user_az=self.context.az,
                user_login=self.context.login,
                uoid=oid
            )

            for idx in range(number):
                voucher = Voucher(
                    creation_date=datetime.now().strftime('%Y-%m-%d'),
                    status=MANUALLY_CREATED,
                    cat = data['kategorie'],
                    user_id=self.context.oid,
                    user_az=self.context.az,
                    user_login=self.context.login,
                    generation_id=p,
                    oid=oid)
                oid += 1
                session.add(voucher)
            session.add(generation)

            # journalize
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
        resources.ehcss.need()
        #resources.chosenajaxe.need()

    @property
    def action_url(self):
        return self.request.path

#    def updateWidgets(self):
#        super(DisableVouchers, self).updateWidgets()
#        if 'form.field.vouchers' in self.fieldWidgets:
#            field_id = self.fieldWidgets.get('form.field.vouchers')
#            import pdb; pdb.set_trace()
#            field_id.template = uvclight.get_template('select.cpt', __file__)

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


MT = u"""Der Erste-Hilfe-Benutzer

%s

%s
%s


bittet um Kontaktaufnahme zum Thema: %s

Der Benutzer hat folgende Nachricht hinterlassen:

%s


Folgende Kontaktdaten stehen zur Verfügung:

%s
%s
%s
"""

class Kontakt(uvclight.Form):
    uvclight.layer(IUserLayer)
    uvclight.context(UserRoot)
    uvclight.auth.require('zope.Public')

    fields = uvclight.Fields(IKontakt)
    title = u"Anfrage"
    label = u"Bitte senden Sie uns Ihre Nachricht."

    @action(u'Senden')
    def handle_send(self):
        data, errors = self.extractData()
        if errors:
            return
        from ukhvoucher.utils import send_mail
        adr = self.request.principal.getAddress()
        acu = self.request.principal.getAccount()
        adrname = adr.name1.strip() + ' ' + adr.name2.strip() + ' ' + adr.name3.strip()
        adrstrasse = adr.street.strip() + ' ' + str(adr.number.strip())
        adrplzort = str(adr.zip_code) + ' ' + adr.city
        acuname = acu.vname + ' ' + acu.nname
        acutel = acu.vorwahl.strip() + ' ' + acu.phone.strip()
        text = MT % (adrname, adrstrasse, adrplzort, data[u'betreff'], data[u'text'], acuname, acutel, acu.email)
        send_mail('extranet@ukh.de', ('portal-erste-hilfe@ukh.de',), u"Kontaktformular Erste Hilfe", text=text)
        self.flash(u'Ihre Nachricht wurde an die Unfallkasse Hessen gesendet.')
        self.redirect(self.application_url())

    @action(u'Abbrechen')
    def handle_cancel(self):
        self.redirect(self.application_url())
        return SUCCESS


class JournalEntryAdd(uvclight.Form):
    uvclight.name('add')
    uvclight.layer(IAdminLayer)
    uvclight.context(Journal)
    require('manage.vouchers')

    fields = (
        uvclight.Fields(IJournalEntryExt) +
        uvclight.Fields(IJournalEntry).omit('date', 'userid', 'oid', 'action'))

    label = "Add a new journal entry"

    @action(u'Senden')
    def handle_send(self):
        data, errors = self.extractData()
        if errors:
            return

        # journalize
        data['date'] = datetime.now().strftime('%Y-%m-%d')
        data['userid'] = self.request.principal.id
        data['oid'] = self.request.principal.getAddress().oid
        entry = JournalEntry(**data)
        self.context.add(entry)

        self.flash(u'Neue Notiz erfolgreich angelegt!')
        self.redirect(self.url(self.context))


class JournalEntryDelete(uvclight.Form):
    uvclight.name('delete')
    uvclight.layer(IAdminLayer)
    uvclight.context(JournalEntry)
    require('manage.vouchers')

    fields = uvclight.Fields()

    @property
    def label(self):
        return "Delete journal entry n°%i" % self.context.jid
    
    @action(u'Delete')
    def handle_send(self):
        back = self.url(self.context.__parent__)
        self.context.__parent__.delete(self.context)
        self.flash(u'Deleted')
        self.redirect(back)
