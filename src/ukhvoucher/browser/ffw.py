# -*- coding: utf-8 -*-
import uvclight
import json


from os import path
from uvc.api import api
from ul.auth import require
from ..apps import UserRoot
from datetime import datetime
from dolmen.forms import base
from docxtpl import DocxTemplate
from zope import interface, schema
from ..interfaces import IUserLayer
from cromlech.browser import getSession
from cromlech.sqlalchemy import get_session
from uvc.design.canvas import IAboveContent
from ukhvoucher.interfaces import K10, IBankverbindung
from time import localtime, strftime
from ..resources import ukhvouchers, masked_input
from ukhvoucher.models import FWBudget, FWKto, JournalEntry

PATH = path.dirname(__file__)
PFAD = "%s/ehffw.docx" % PATH


def getData(oid):
    session = get_session('ukhvoucher')
    q = session.query(FWBudget).filter(FWBudget.user_id == oid)
    if q.count() == 1:
        return q.one()
    return None


def getKto(oid):
    session = get_session('ukhvoucher')
    q = session.query(FWKto).filter(FWKto.user_id == oid)
    if q.count() == 1:
        return q.one()
    return None


class AT(api.Page):
    """ Page Already THERE"""
    uvclight.layer(IUserLayer)
    uvclight.context(UserRoot)
    require('users.access')

    label = u"Budgetantrag für Erste-Hilfe-Lehrgänge in der Freiwilligen Feuerwehr"
    template = uvclight.get_template('download.cpt', __file__)

    def update(self):
        budget = getData(self.request.principal.oid)
        kto = getKto(self.request.principal.oid)
        betrag = budget.budget
        restbudget = budget.budget_vj
        zahlbetrag = betrag - restbudget
        betrag = "%0.2f" % float(betrag)
        restbudget = "%0.2f" % float(restbudget)
        zahlbetrag = "%0.2f" % float(zahlbetrag)
        dat = {
            'zahlbetrag': zahlbetrag,
            'kontoinhaber': kto.kto_inh,
            'last_budget': restbudget,
            'einsatzkraefte': budget.einsatzk,
            'datum': budget.datum,
            'betrag': betrag,
            'iban': kto.iban,
            'verw_zweck': kto.verw_zweck,
            'betreuer': budget.jugendf,
            'bank': kto.bank}
        self.data = dat


class InfoDownload(api.View):
    uvclight.layer(IUserLayer)
    uvclight.context(UserRoot)
    require('users.access')
    uvclight.name('info.pdf')

    def make_response(self, result):
        response = self.responseFactory(app_iter=result)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = "%s" % (
            'attachment; filename="INFO.pdf"'
        )
        return response

    def render(self):
        info_file = "%s/%s" % (PATH, 'ffw_info.pdf')
        with open(info_file, 'rb') as info:
            return info.read()


class FFWForm(api.Form):
    uvclight.layer(IUserLayer)
    uvclight.context(UserRoot)
    require('users.access')
    label = u"Budgetantrag für Erste-Hilfe-Lehrgänge in der Freiwilligen Feuerwehr"
    ignoreContent = False

    def update(self):
        ukhvouchers.need()
        if getData(self.request.principal.oid):
            self.redirect(self.url(self.context, 'at'))
            return
        session = getSession()
        if 'ffw' in session:
            data = json.loads(session['ffw'])
            self.setContentData(base.DictDataManager(data))

    @property
    def fields(self):
        fields = api.Fields(K10).omit('last_budget', 'bestaetigung') + api.Fields(IBankverbindung) # + api.Fields(K10).select('bestaetigung')
        fields['einsatzkraefte'].htmlAttributes = {'maxlength': 5}
        fields['betreuer'].htmlAttributes = {'maxlength': 5}
        fields['kontoinhaber'].htmlAttributes = {'maxlength': 50}
        fields['bank'].htmlAttributes = {'maxlength': 50}
        fields['iban'].htmlAttributes = {'maxlength': 22}
        return fields

    @api.action(u'Vorschau')
    def handle_preview(self):
        data, errors = self.extractData()
        if errors:
            if 'form.field.iban' in errors.keys():
                error = errors.get('form.field.iban')
                error.title = u"Bitte geben Sie eine gültige IBAN ein"
            if 'form.field.kontoinhaber' in errors.keys():
                error = errors.get('form.field.kontoinhaber')
                error.title = u"Bitte tragen Sie einen Kontoinhaber ein"
            if 'form.field.bank' in errors.keys():
                error = errors.get('form.field.bank')
                error.title = u"Bitte tragen Sie einen Kreditinstitut ein"
            return
        datum = strftime("%d.%m.%Y", localtime())
        data['datum'] = datum
        jahr = strftime("%Y", localtime())
        if jahr == "2017" or jahr == "2018":
            verw_zweck = "Erste-Hilfe-Budget 2017/18"
        if jahr == "2019" or jahr == "2020":
            verw_zweck = "Erste-Hilfe-Budget 2019/20"
        data['verw_zweck'] = verw_zweck
        data['last_budget'] = "0,0"
        rep = data['last_budget'].replace(',','.')
        data['last_budget'] = rep
        betrag = (float(data['einsatzkraefte']) * 0.1 + float(data['betreuer'])) * (30.75 + 6.15)
        zahlbetrag = betrag - float(data['last_budget'])
        if float(data['last_budget']) > float(betrag):
            self.flash(u'Achtung! Stimmen die Angaben zum Restbudget?', type="error")
            return
        data['betrag'] = "%0.2f" % float(betrag)
        data['last_budget'] = "%0.2f" % float(data['last_budget'])
        data['zahlbetrag'] = "%0.2f" % float(zahlbetrag)
        session = getSession()
        session['ffw'] = json.dumps(data)
        self.redirect(self.url(self.context, 'ffw'))


class IFFW(interface.Interface):

    best = schema.Bool(
        title=u"Bestätigung",
    )


class FFW(api.Form):
    uvclight.layer(IUserLayer)
    uvclight.context(UserRoot)
    require('users.access')
    label = u"Budgetantrag für Erste-Hilfe-Lehrgänge in der Freiwilligen Feuerwehr"

    fields = uvclight.Fields(IFFW)

    @property
    def template(self):
        return uvclight.get_template('ffwform.cpt', __file__)

    def update(self):
        session = getSession()
        self.data = json.loads(session['ffw'])

    @api.action(u'Absenden', identifier="send")
    def handle_save(self):
        data, errors = self.extractData()
        if not data.get('best'):
            self.flash(u'Bitte bestätigen Sie Ihre Angaben.', type="error")
            return
        if errors:
            return

        from ukhvoucher.utils import send_mail
        adr = self.request.principal.getAddress()
        acc = self.request.principal.getAccount()
        doc = DocxTemplate(PFAD)
        data = self.data
        context = {
            'einsatzkraefte': unicode(data.get('einsatzkraefte')),
            'betreuer': unicode(data.get('betreuer')),
            'betrag': str(data.get('betrag')),
            'restbudget': str(data.get('last_budget')),
            'zahlbetrag': str(data.get('zahlbetrag')),
            'kreditinstitut': data.get('bank'),
            'kontoinhabe': data.get('kontoinhaber'),
            'verwendungszweck': data.get('verw_zweck'),
            'iban': data.get('iban'),
            'titel': acc.titel.strip(),
            'vname': acc.vname.strip(),
            'nname': acc.nname.strip(),
            'name1': adr.name1.strip(),
            'name2': adr.name2.strip(),
            'name3': adr.name3.strip(),
            'strasse': adr.street.strip(),
            'nr': adr.number.strip(),
            'plz': adr.zip_code,
            'ort': adr.city.strip(),
            'datum': data.get('datum'),
        }
        doc.render(context)
        filename = '/tmp/Budgetantrag_FFW_' + adr.name1.encode('utf-8').strip() + ' ' + adr.name2.encode('utf-8').strip() + ' ' + adr.name3.encode('utf-8').strip() + '.docx'
        doc.save(filename)
        text = u"Für das Mitglied %s %s %s hat %s %s folgenden Budgetantrag gestellt." % (adr.name1.strip(), adr.name2.strip(), adr.name3.strip(), acc.vname.strip(), acc.nname.strip())
        send_mail('extranet@ukh.de', ('b.svejda@ukh.de', 'portal-erste-hilfe@ukh.de'), u"Budgetantrag Erste-Hilfe-Feuerwehr", text=text, files=(filename,))
        budget = FWBudget(
            user_id=self.request.principal.oid,
            einsatzk=data.get('einsatzkraefte'),
            jugendf=data.get('betreuer'),
            budget=data.get('betrag'),
            budget_vj=data.get('last_budget'),
            datum=data.get('datum'),
        )
        kto = FWKto(
            user_id=self.request.principal.oid,
            iban=data.get('iban').replace(' ', ''),
            bank=data.get('bank'),
            verw_zweck=data.get('verw_zweck'),
            kto_inh=data.get('kontoinhaber')
        )
        entry = JournalEntry(
            date=datetime.now().strftime('%Y-%m-%d'),
            userid=self.request.principal.id,
            action=u"Feuerwehrbudget angelegt.",
            oid=self.request.principal.oid,
            note='')
        session = get_session('ukhvoucher')
        session.add(budget)
        session.add(kto)
        session.add(entry)
        self.flash(u'Ihr Budgetantrag wurde an die Unfallkasse Hessen gesendet.')
        self.redirect(self.application_url())

    @api.action(u'Abbrechen', identifier="cancel")
    def handle_cancel(self):
        data, errors = self.extractData()
        self.redirect(self.url(self.context, 'ffwform'))


class INFO(uvclight.Viewlet):
    uvclight.layer(IUserLayer)
    uvclight.context(UserRoot)
    uvclight.viewletmanager(IAboveContent)

    @property
    def available(self):
        if self.request.principal.id == 'user.unauthenticated':
            return False
        from ukhvoucher.interfaces import K10
        return K10 in self.request.principal.getCategory()

    def render(self):
        return "<div class'pull-right'> <a target='_blank' href='info.pdf' class='btn btn-primary'> Info Feuerwehr </a> </div>"
