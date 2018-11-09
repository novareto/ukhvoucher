# -*- coding: utf-8 -*-
import json
import uvclight

from os import path
from uvc.api import api
from ul.auth import require
from ..apps import UserRoot
from datetime import datetime, timedelta
from dolmen.forms import base
from docxtpl import DocxTemplate
from zope import interface, schema
from ..interfaces import IUserLayer
from cromlech.browser import getSession
from cromlech.sqlalchemy import get_session
from uvc.design.canvas import IAboveContent
from ukhvoucher.interfaces import K10, IBankverbindung
from time import localtime, strftime
from ..resources import ukhvouchers
from ukhvoucher.models import FWBudget, FWKto, JournalEntry

PATH = path.dirname(__file__)
PFAD = "%s/ehffw.docx" % PATH
PFAD2 = "%s/ehffwabw.docx" % PATH


def getData(oid, zeitpunkt=None):
    session = get_session('ukhvoucher')
    import datetime
    from ukhvoucher.vocabularies import get_default_abrechnungszeitraum
    if zeitpunkt:
        default_zeitraum = get_default_abrechnungszeitraum(zeitpunkt)
    else:
        default_zeitraum = get_default_abrechnungszeitraum(zeitpunkt=datetime.datetime(2019, 1, 1))
    print "default zeitraum:", default_zeitraum
    q = session.query(FWBudget).filter(
        FWBudget.user_id == oid,
        FWBudget.datum >= default_zeitraum.von,
        FWBudget.datum <= default_zeitraum.bis
    )
    if q.count() == 1:
        return q.one()
    return None


def getKto(oid, session=None):
    if not session:
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
        data = {}
        kto = getKto(self.request.principal.oid)
        if kto:
            data['iban'] = kto.iban.strip()
            data['bank'] = kto.bank.strip()
            data['kontoinhaber'] = kto.kto_inh.strip()
        ukhvouchers.need()
        if getData(self.request.principal.oid):
            self.redirect(self.url(self.context, 'at'))
            return
        session = getSession()
        if 'ffw' in session:
            data.update(json.loads(session['ffw']))
        self.setContentData(base.DictDataManager(data))

    @property
    def fields(self):
        fields = api.Fields(K10).omit('bestaetigung') + api.Fields(IBankverbindung) # + api.Fields(K10).select('bestaetigung')
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
            for x in errors:
                if x.title == "There were errors.":
                    x.title = u"Ihre Angaben sind unvollständig."
                if x.title == "Missing required value.":
                    x.title = "Bitte geben sie eine Zahl ein."
            self.submissionError = errors
            if 'form.field.iban' in errors.keys():
                error = errors.get('form.field.iban')
                error.title = u"Bitte geben Sie eine gültige IBAN ein."
            if 'form.field.kontoinhaber' in errors.keys():
                error = errors.get('form.field.kontoinhaber')
                error.title = u"Bitte tragen Sie einen Kontoinhaber ein."
            if 'form.field.bank' in errors.keys():
                error = errors.get('form.field.bank')
                error.title = u"Bitte tragen Sie einen Kreditinstitut ein."
            return

        #print "##################################################"
        #print data
        #daten_vorperiode = getData(oid=self.request.principal.oid, zeitpunkt=FAKE_DATE - timedelta(days=365 * 2))
        #print lulu.einsatzk
        #print "##################################################"
        
        
        
        datum = strftime("%d.%m.%Y", localtime())
        data['datum'] = datum
        jahr = strftime("%Y", localtime())
        jahr = "2019" # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if jahr == "2017" or jahr == "2018":
            verw_zweck = "Erste-Hilfe-Budget 2017/18"
        if jahr == "2019" or jahr == "2020":
            verw_zweck = "Erste-Hilfe-Budget 2019/20"
        data['verw_zweck'] = verw_zweck
        #data['last_budget'] = "0,0"
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

    begr = schema.TextLine(
        title=u"Begründung",
        required=False,
    )


class FFW(api.Form):
    uvclight.layer(IUserLayer)
    uvclight.context(UserRoot)
    require('users.access')
    label = u"Budgetantrag für Erste-Hilfe-Lehrgänge in der Freiwilligen Feuerwehr"

    @property
    def fields(self):
        fields = uvclight.Fields(IFFW)
        fields['begr'].htmlAttributes = {'maxlength': 60}
        return fields

    @property
    def template(self):
        return uvclight.get_template('ffwform.cpt', __file__)

    def update(self):
        session = getSession()
        self.data = json.loads(session['ffw'])

    def getOldData(self):

        abweichung = False
        #daten_vorperiode = getData(oid=self.request.principal.oid)
        #daten_vorperiode = getData(oid=self.request.principal.oid, zeitpunkt=FAKE_DATE - timedelta(days=365 * 2))
        daten_vorperiode = getData(oid=self.request.principal.oid, zeitpunkt=datetime(2019, 1, 1) - timedelta(days=365 * 2))
        aktuell = float(self.data['einsatzkraefte'])
        vorjahr = float(daten_vorperiode.einsatzk)
        differenz = ((100 * aktuell) / vorjahr) - 100
        if differenz > 10 or differenz < -10:
            abweichung = True
        aktuell = float(self.data['betreuer'])
        vorjahr = float(daten_vorperiode.jugendf)
        differenz = ((100 * aktuell) / vorjahr) - 100
        if differenz > 10 or differenz < -10:
            abweichung = True
        return abweichung


    @api.action(u'Absenden', identifier="send")
    def handle_save(self):
        data, errors = self.extractData()
        if not data.get('best'):
            self.flash(u'Bitte bestätigen Sie Ihre Angaben.')
            return
        if errors:
            return
        abweichung = False
        #daten_vorperiode = getData(oid=self.request.principal.oid, zeitpunkt=FAKE_DATE - timedelta(days=365 * 2))
        daten_vorperiode = getData(oid=self.request.principal.oid, zeitpunkt=datetime(2019, 1, 1) - timedelta(days=365 * 2))
        aktuell = float(self.data['einsatzkraefte'])
        vorjahr = float(daten_vorperiode.einsatzk)
        differenz = ((100 * aktuell) / vorjahr) - 100
        if differenz > 10 or differenz < -10:
            abweichung = True
        aktuell = float(self.data['betreuer'])
        vorjahr = float(daten_vorperiode.jugendf)
        differenz = ((100 * aktuell) / vorjahr) - 100
        if differenz > 10 or differenz < -10:
            abweichung = True
        # ##################################################
        # Was machen wir.... ?????
        # ##################################################
        if abweichung is True:
            la = len(data['begr'])
            if la <= 5:
                self.flash(u'Bitte tragen Sie eine Begründung für die Abweichung zum letzten Budgetantrag ein.')
                return



        #else:
        #    self.flash(u'Wir haben KEINE Abweichung....')
        #    return
            

        print "#########################################"
        print data
        print "#########################################"
        print self.data
        print "#########################################"
        print abweichung
        print "#########################################"

        print "test"
        from ukhvoucher.utils import send_mail
        adr = self.request.principal.getAddress()
        acc = self.request.principal.getAccount()
        doc = DocxTemplate(PFAD)
        begruendung = ''
        if abweichung is True:
            doc = DocxTemplate(PFAD2)
            begruendung = data['begr']
        data = self.data
        context = {
            'einsatzkraefte': unicode(data.get('einsatzkraefte')),
            'betreuer': unicode(data.get('betreuer')),
            'begruendung': unicode(begruendung),
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
            #'datum': '03.03.2019',  # ------>  NUR TEST
        }
        doc.render(context)
        filename = '/tmp/Budgetantrag_FFW_' + adr.name1.encode('utf-8').strip() + ' ' + adr.name2.encode('utf-8').strip() + ' ' + adr.name3.encode('utf-8').strip() + '.docx'
        doc.save(filename)
        text = u"Für das Mitglied %s %s %s hat %s %s folgenden Budgetantrag gestellt." % (adr.name1.strip(), adr.name2.strip(), adr.name3.strip(), acc.vname.strip(), acc.nname.strip())
        send_mail('extranet@ukh.de', ('b.svejda@ukh.de', 'portal-erste-hilfe@ukh.de'), u"Budgetantrag Erste-Hilfe-Feuerwehr", text=text, files=(filename,))
        #send_mail('extranet@ukh.de', ('m.seibert@ukh.de',), u"Budgetantrag Erste-Hilfe-Feuerwehr", text=text, files=(filename,))
        budget = FWBudget(
            user_id=self.request.principal.oid,
            einsatzk=data.get('einsatzkraefte'),
            jugendf=data.get('betreuer'),
            budget=data.get('betrag'),
            budget_vj=data.get('last_budget'),
            #datum=data.get('datum'),
            #datum=datetime.now().strftime('%Y-%m-%d'),
            datum='2019-03-03',  # ------>  NUR TEST
        )
        session = get_session('ukhvoucher')
        kto_alt = getKto(self.request.principal.oid, session=session) 
        if kto_alt:
            #kto_alt.iban = data.get('iban').replace(' ', ''),
            #kto_alt.bank = data.get('bank'),
            #kto_alt.verw_zweck = data.get('verw_zweck'),
            #kto_alt.kto_inh = data.get('kontoinhaber')
            session.delete(kto_alt)
            session.flush()
            #kto_alt.user_id=self.request.principal.oid,
        
        kto = FWKto(
            user_id=self.request.principal.oid,
            iban=data.get('iban').replace(' ', ''),
            bank=data.get('bank'),
            verw_zweck=data.get('verw_zweck'),
            kto_inh=data.get('kontoinhaber')
        )
        session.add(kto)
        entry = JournalEntry(
            #date=datetime.now().strftime('%Y-%m-%d'),
            date='2019-03-03',  # ------>  NUR TEST
            userid=self.request.principal.id,
            action=u"Feuerwehrbudget angelegt.",
            oid=self.request.principal.oid,
            note='')
        session.add(budget)
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
