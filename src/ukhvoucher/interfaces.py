# -*- coding: utf-8 -*-

import grokcore.component as grok
from . import VOCABULARIES
from ukhtheme.uvclight import IDGUVRequest
from ukhvoucher import _
from zope import schema
from zope.interface import Interface, Attribute
from zope.schema.interfaces import IContextSourceBinder
from zope.interface import taggedValue
from cromlech.sqlalchemy import get_session
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from plone.memoize import ram
from time import time
from uvc.validation import validation


HK1 = u"""
<h2>K1: Verwaltung / Büro</h2>
<h4><u>Beschäftigte:</u></h4>
<p>Bitte tragen Sie <u>alle</u> bei der UKH versicherten Beschäftigten ein, die in Ihren Verwaltungsbereichen
   arbeiten. Zählen Sie dazu die Personen, nicht die Vollzeitstellen. Beamte sind keine Beschäftigten
   und werden daher nicht mitgezählt.</p>
<h4><u>Standorte:</u></h4>
<p>Tragen Sie bitte ein, an wie vielen räumlich abgeschlossenen Arbeitsorten mindestens zwei versicherte
   Beschäftigte anwesend sind. Abgeschlossene Arbeitsorte sind zum Beispiel getrennte Gebäude,
   jedoch nicht verschiedene Stockwerke oder Abteilungen innerhalb eines Gebäudes.</p>
<p>Felder mit <b>*</b> sind Pflichtfelder, diese müssen gefüllt werden.</p>
"""

HK2 = u"""
<h2>K2: Sonstige Betriebe und Hochschulen</h2>
<h4><u>Sonstige Betriebe:</u></h4>
<p>Alle Betriebe, die nicht in der Hauptsache Verwaltungs- oder Bürobetriebe sind beispielsweise:</p>
<p>-  Technische Betriebe</p>
<p>-  Landwirtschaftliche und gärtnerische Betriebe</p>
<p>-  Hauswirtschaftliche Betriebe</p>
<p>-  Betriebe für öffentliche Sicherheit und Ordnung mit Streifendienst</p>
<p>-  Zoos (ohne Beschäftigte in der Tierpflege)</p>
<p>-  Theater- und Musikbetriebe</p>
<p>-  Betreuungseinrichtungen (ohne Kindertagesstätten, -krippen, Schulbetreuung)</p>
<p>-  Entsorgungsbetriebe und Bauhöfe ohne Einteilung in Kolonnen</p>
<br>
<p>Bitte beachten Sie hier die Besonderheiten für verschiedene Betriebsarten wie beispielsweise:</p>
<p>-  Kinderbetreuungseinrichtungen (K3), Schulpersonal der Schulträger (K8) und Schulbetreuung (K9)</p>
<p>-  Betriebe mit Beschäftigten in Kolonnen (K4)</p>
<p>-  Betriebe mit besonderer Gefährdung (K5, K6)</p>
<p>-  Betriebe mit beruflich qualifizierten Ersthelfern wie Gesundheits- und Pflegediensten, Schwimmbädern (K11)</p>
<h4><u>Beschäftigte:</u></h4>
<p>Bitte tragen Sie <u>alle</u> bei der UKH versicherten beschäftigten Personen (ohne Beamte) ein, die in
   anderen Bereichen als Verwaltung / Büros arbeiten abzüglich</p>
<p>a) Beschäftigte in Kindertageseinrichtungen</p>
<p>b) Beschäftigte in Kolonnen (Bauhof, Entsorgung)</p>
<p>c) Beschäftigte mit spezieller Gefährdung gemäß aufgeführtem Sonderkontingent</p>
<h4><u>Standorte:</u></h4>
<p>Tragen Sie bitte ein, an wie vielen räumlich abgeschlossenen Arbeitsorten mindestens zwei versicherte
   Beschäftigte anwesend sind. Abgeschlossene Arbeitsorte sind zum Beispiel getrennte Gebäude,
   jedoch nicht verschiedene Stockwerke oder Abteilungen innerhalb eines Gebäudes.</p>
<p>Felder mit <b>*</b> sind Pflichtfelder, diese müssen gefüllt werden.</p>
"""

HK3 = u"""
<h2>K3: Kindertageseinrichtungen</h2>
<h4><u>Kindergruppen:</u></h4>
<p>Bitte tragen Sie ein, wie viele Kindergruppen in Ihren Einrichtungen  maximal gleichzeitig betrieben werden.
   Beispiel: 4 Vormittagsgruppen und 2 Nachmittagsgruppen sind maximal 4 Gruppen gleichzeitig.</p>
<p>Tragen Sie bitte ein, an wie vielen räumlich abgeschlossenen Arbeitsorten mindestens zwei versicherte Beschäftigte
   anwesend sind. Abgeschlossene Arbeitsorte sind zum Beispiel getrennte Gebäude,
   jedoch nicht verschiedene Stockwerke oder Abteilungen innerhalb eines Gebäudes.</p>
<p>Felder mit <b>*</b> sind Pflichtfelder, diese müssen gefüllt werden.</p>
"""

HK4 = u"""
<h2>K4: In Kolonnen tätige Beschäftigte</h2>
<h4><u>Kolonnen:</u></h4>
<p>Bitte tragen Sie die maximale Zahl der Kolonnen ein, in denen Beschäftigte in der Entsorgung oder im Bauhof
   außerhalb gleichzeitig tätig sind.</p>
<p>Hinweis: Die übrigen Beschäftigten des Betriebs, die an festen Standorten tätig sind, sind mit der Personenzahl
   unter dem Kontingent 2 "Sonstige Betriebe" zu erfassen.</p>
<p>Felder mit <b>*</b> sind Pflichtfelder, diese müssen gefüllt werden.</p>
"""

HK5 = u"""
<h2>K5: Beschäftigte und Einrichtungen mit erhöhter Gefährdung</h2>
<h4><u>Beschäftigte:</u></h4>
<p>Bitte tragen Sie die bei der UKH versicherten Beschäftigten ein, die eine Tätigkeit mit erhöhter Gefährdung ausüben.</p>
<p>Beachten Sie bitte auch, dass diese Personen in keinem anderen Kontingent aufzuführen sind.</p>
<p>Hinweise zu Tätigkeiten mit erhöhter Gefährdung entnehmen Sie bitte den Informationen unter dem Button "Info".</p>
<p>Felder mit <b>*</b> sind Pflichtfelder, diese müssen gefüllt werden.</p>
"""

HK6 = u"""
<h2>K6: Betriebe mit besonders hoher Gefährdung</h2>
<h4><u>Beschäftigte:</u></h4>
<p>Bitte tragen Sie die bei der UKH versicherten Beschäftigten ein, die eine Tätigkeit mit besonders hoher Gefährdung ausüben.</p>
<p>Beachten Sie bitte auch, dass diese Personen in keinem anderen Kontingent aufzuführen sind.</p>
<p>Hinweise zu Tätigkeiten mit besonders hoher Gefährdung entnehmen Sie bitte den Informationen unter dem Button "Info".</p>
<br>
<p>Für Kommunen gilt: </p>
<p>Hier sind Beschäftigte in Abwasserbetrieben (Arbeiten im Kanalnetz) und auf Deponien anzugeben.</p>
<p>Beschäftigte in der Wasserversorgung (Arbeiten in Schächten) sind hier nur anzugeben, wenn für diesen Personenkreis
   die fachliche Zuständigkeit der Unfallkasse Hessen - nicht der BG ETEM - gegeben ist.</p>
<p>Felder mit <b>*</b> sind Pflichtfelder, diese müssen gefüllt werden.</p>
"""

HK7 = u"""
<h2>K7: Schulen (nur Lehrkräfte)</h2>
<h4><u>Lehrkräfte:</u></h4>
<p>Bitte tragen Sie die Zahl der Lehrkräfte ein, die an der Schule und ggf. an den Außenstellen der Schule tätig sind.
   Wir übernehmen Lehrgangsgebühren für die Teilnahme an</p>
<p>-  Erste-Hilfe-Fortbildungen im Sinne des DGUV Grundsatzes 304-001</p>
<p>-  Erste-Hilfe-Fortbildungen Schule</p>
<p>für 15 % des gesamten Kollegiums in einem Zeitraum von 2 Jahren.</p>
<p>Hinweis: Bitte zählen Sie Personal in anderen Bereichen, bspw. in der Schulbetreuung, Reinigung,
   Sekretariat oder Hausmeister nicht mit. Für dieses Personal beantragt der Arbeitgeber die Kostenübernahme
   der Lehrgangsgebühren bei der zuständigen Fach-Berufsgenossenschaft oder bei uns als Mitgliedsunternehmen.</p>
<p>Felder mit <b>*</b> sind Pflichtfelder, diese müssen gefüllt werden.</p>
"""

HK8 = u"""
<h2>K8: Schulpersonal der Schulträger </h2>
<h4><u>Standorte:</u></h4>
<p>Bitte tragen Sie ein, an wie vielen Schulstandorten Personal in den Bereichen Reinigung,
   Sekretariat oder Hausmeister beschäftigt wird.</p>
<p>Als Schulstandort gilt eine Schule, wobei Außenstellen von Schulen als eigener Standort gezählt werden.</p>
<p>Felder mit <b>*</b> sind Pflichtfelder, diese müssen gefüllt werden.</p>
"""

HK9 = u"""
<h2>K9: Schulbetreuung</h2>
<h4><u>Gruppen:</u></h4>
<p>Bitte tragen Sie ein, wie viele Schulbetreuungsgruppen höchstens gleichzeitig betrieben werden.
   Beispiel: 3 Gruppen dienstags und 2 Gruppen donnerstags sind 3 Gruppen gleichzeitig.</p>
<p>Felder mit <b>*</b> sind Pflichtfelder, diese müssen gefüllt werden.</p>
"""

HK10 = u"""
<h2>K10: Freiwillige Feuerwehren</h2>
<h4><u>Aktive Einsatzkräfte:</u></h4>
<p>Bitte tragen Sie die Summe der aktiven Einsatzkräfte aus allen Orts- oder Stadtteilfeuerwehren ein.
   Die UKH übernimmt die Kosten für Erste-Hilfe-Lehrgänge über 9 Unterrichtseinheiten für 10 % der
   aktiven Einsatzkräfte im Zeitraum von 2 Jahren.</p>
<h4><u>Jugendbetreuer/innen:</u></h4>
<p>Bitte tragen Sie auch hier alle Jugendbetreuer/innen der Orts- oder Stadtteilfeuerwehren ein.
   Die UKH übernimmt für alle einmal in 2 Jahren die Kosten der Erste-Hilfe-Lehrgänge.</p>
<h4><u>Höhe des in 2017/18 nicht verbrauchten Budgets (siehe Themenspeicher)</u></h4>
<p>Bitte tragen Sie die Höhe des in 2017/18 nicht benötigten Budgets ein. Noch
vorhandenes Budget wird Ihnen auf den Folgezeitraum 2019/20 angerechnet.</p>
<p>Felder mit <b>*</b> sind Pflichtfelder, diese müssen gefüllt werden.</p>
"""

HK11 = u"""
<h2>K11: Gesundheitsdienste</h2>
<p>Gesundheitsdienste brauchen neben dem medizinischen Personal nur dann betriebliche Ersthelfer,
   wenn Bereiche so aus dem medizinischen Betrieb ausgelagert sind, dass die Ersthelfer nicht erreichbar sind.</p>
<h4><u>Beschäftigte in der Verwaltung</u></h4>
<p>Bitte tragen Sie hier nur die Zahl derjenigen Beschäftigten in der Verwaltung ein,
   die an einem anderen Standort als das medizinische Personal tätig sind.</p>
<h4><u>Beschäftigte im technischen Bereich</u></h4>
<p>Bitte tragen Sie hier nur die Zahl derjenigen Beschäftigten ein, die an einem anderen Standort als das medizinische Personal tätig sind.
   Zum technischen Bereich zählen Labore, Werkstätten, Wäschereien und Küchen.</p>
<h4><u>Standorte</u></h4>
<p>Bitte tragen Sie nur Standorte für die jeweiligen Bereiche ein, die vom Medizinbetrieb getrennt sind.
   Als eigene Standorte gelten räumlich abgeschlossene Arbeitsorte, an denen mindestens zwei versicherte
   Beschäftigte anwesend sind.
   Verschiedene Stockwerke oder Abteilungen innerhalb eines Gebäudes zählen nicht als abgeschlossene Arbeitsorte.</p>
<p>Felder mit <b>*</b> sind Pflichtfelder, diese müssen gefüllt werden.</p>
"""

RESTBUDGET = u"""
<p>Bitte tragen Sie die Höhe des in 2017/18 nicht benötigten Budgets ein.
   Noch vorhandenes Budget wird Ihnen auf den Folgezeitraum 2019/20 angerechnet.</p>
<p>Bitte denken Sie daran, dass Sie ggf. noch Geld für noch nicht abgerechnete Erste-Hilfe-Lehrgänge aus dem Vorjahr benötigen.
   Geben Sie uns deshalb hier lediglich die Höhe des nicht mehr benötigten Budgets aus dem letzten Antragszeitraum an.</p>
<p><b>Beispiel:</b></p>
<p>Budget im letzten Antragszeitraum: 5000 €</p>
<p>Abgerechnete Erste-Hilfe-Lehrgänge: 3000 €</p>
<p>Derzeitig ermitteltes Restbudget: 5000 € - 3000 € = 2000 €</p>
<p>Noch nicht abgerechnete Erste-Hilfe-Lehrgänge: 500 €</p>
<p><b>Höhe des nicht mehr benötigten Budgets: 2000 € - 500 € = 1500 €</b></p>
"""


@grok.provider(IContextSourceBinder)
def get_oid(context):
    from ukhvoucher.models import AddressTraeger, Address, AddressEinrichtung
    rc = []
    rcc = []
    session = get_session('ukhvoucher')
    for x in session.query(Address):
        rc.append(SimpleTerm(int(x.oid), x.oid, "%s - %s - %s %s %s" % (x.oid, x.mnr, x.name1, x.name2, x.name3)))
        rcc.append(int(x.oid))
    @ram.cache(lambda *args: time() // (600 * 60))
    def getValue():
        res = []
        for x in session.query(AddressTraeger):
            res.append(SimpleTerm(int(x.oid), x.oid, "%s - %s - %s %s %s" % (x.oid, x.mnr, x.name1, x.name2, x.name3)))
        for x in session.query(AddressEinrichtung):
            res.append(SimpleTerm(int(x.oid), x.oid, "%s - %s - %s %s %s" % (x.oid, x.mnr, x.name1, x.name2, x.name3)))
        return res
    for term in getValue():
        if term.value not in rcc:
            rc.append(term)
    return SimpleVocabulary(rc)


def getInvoiceId():
    from ukhvoucher.models import Invoice
    from sqlalchemy.sql.functions import max
    session = get_session('ukhvoucher')
    try:
        oid = int(session.query(max(Invoice.oid)).one()[0]) + 1
    except:
        oid = 100000
    return unicode(oid)


@grok.provider(IContextSourceBinder)
def get_reason(context):
    rc = [
        SimpleTerm(u'', u'', u''),
        SimpleTerm(u'Ablehnung, da keine Berechtigungsscheine anbei',
                   u'Ablehnung, da keine Berechtigungsscheine anbei',
                   u'Ablehnung, da keine Berechtigungsscheine anbei'),
        SimpleTerm(u'Ablehnung, da nicht ausreichend Berechtigungsscheine anbei',
                   u'Ablehnung, da nicht ausreichend Berechtigungsscheine anbei',
                   u'Ablehnung, da nicht ausreichend Berechtigungsscheine anbei'),
        SimpleTerm(u'Ablehnung, da doppelte Berechtigungsscheine eingereicht wurden',
                   u'Ablehnung, da doppelte Berechtigungsscheine eingereicht wurden',
                   u'Ablehnung, da doppelte Berechtigungsscheine eingereicht wurden'),
        SimpleTerm(u'Ablehnung, da unterzeichnete Original-Teilnehmerliste fehlt',
                   u'Ablehnung, da unterzeichnete Original-Teilnehmerliste fehlt',
                   u'Ablehnung, da unterzeichnete Original-Teilnehmerliste fehlt'),
        SimpleTerm(u'Ablehnung, da eine falsche Lehrgangsgebuehr zu Grunde gelegt wurde',
                   u'Ablehnung, da eine falsche Lehrgangsgebuehr zu Grunde gelegt wurde',
                   u'Ablehnung, da eine falsche Lehrgangsgebühr zu Grunde gelegt wurde'),
        SimpleTerm(u'Ablehnung, da die fachliche/oertliche Zustaendigkeit der UKH nicht gegeben ist',
                   u'Ablehnung, da die fachliche/oertliche Zustaendigkeit der UKH nicht gegeben ist',
                   u'Ablehnung, da die fachliche/örtliche Zuständigkeit der UKH nicht gegeben ist'),
        SimpleTerm(u'Ablehnung, da 7 UE-Zusatzlehrgang FFW',
                   u'Ablehnung, da 7 UE-Zusatzlehrgang FFW',
                   u'Ablehnung, da 7 UE-Zusatzlehrgang FFW'),
        SimpleTerm(u'Ablehnung, da keine ermaechtigte Stelle',
                   u'Ablehnung, da keine ermaechtigte Stelle',
                   u'Ablehnung, da keine ermächtigte Stelle'),
        SimpleTerm(u'Ablehnung, da kein anerkannter Erste Hilfe-Lehrgang',
                   u'Ablehnung, da kein anerkannter Erste Hilfe-Lehrgang',
                   u'Ablehnung, da kein anerkannter Erste Hilfe-Lehrgang'),
        SimpleTerm(u'Ablehnung, da keine vollstaendigen Unterlagen und Daten',
                   u'Ablehnung, da keine vollstaendigen Unterlagen und Daten',
                   u'Ablehnung, da keine vollständigen Unterlagen und Daten'),
        SimpleTerm(u'Kuerzung, da nicht ausreichend Berechtigungsscheine anbei',
                   u'Kuerzung, da nicht ausreichend Berechtigungsscheine anbei',
                   u'Kürzung, da nicht ausreichend Berechtigungsscheine anbei'),
        SimpleTerm(u'Kuerzung, da doppelte Berechtigungsscheine eingereicht wurden',
                   u'Kuerzung, da doppelte Berechtigungsscheine eingereicht wurden',
                   u'Kürzung, da doppelte Berechtigungsscheine eingereicht wurden'),
        SimpleTerm(u'Kuerzung, da unterzeichnete Original-Teilnehmerliste fehlt',
                   u'Kuerzung, da unterzeichnete Original-Teilnehmerliste fehlt',
                   u'Kürzung, da unterzeichnete Original-Teilnehmerliste fehlt'),
        SimpleTerm(u'Kuerzung, da eine falsche Lehrgangsgebuehr zu Grunde gelegt wurde',
                   u'Kuerzung, da eine falsche Lehrgangsgebuehr zu Grunde gelegt wurde',
                   u'Kürzung, da eine falsche Lehrgangsgebühr zu Grunde gelegt wurde'),
        SimpleTerm(u'Kuerzung, da die fachliche/oertliche Zustaendigkeit der UKH nicht gegeben ist',
                   u'Kuerzung, da die fachliche/oertliche Zustaendigkeit der UKH nicht gegeben ist',
                   u'Kürzung, da die fachliche/örtliche Zuständigkeit der UKH nicht gegeben ist'),
        SimpleTerm(u'Zahlung erfolgt an Mitgliedsunternehmen/-betrieb oder Privatperson/Tagespflegeperson',
                   u'Zahlung erfolgt an Mitgliedsunternehmen/-betrieb oder Privatperson/Tagespflegeperson',
                   u'Zahlung erfolgt an Mitgliedsunternehmen/-betrieb oder Privatperson/Tagespflegeperson'),
    ]
    return SimpleVocabulary(rc)

def get_source(name):
    @grok.provider(IContextSourceBinder)
    def source(context):
        return VOCABULARIES[name](context)
    return source


@grok.provider(IContextSourceBinder)
def get_kategorie(context):
    rc = [
        SimpleTerm(K1.getName(), K1.getName(), K1.getDoc()),
        SimpleTerm(K2.getName(), K2.getName(), K2.getDoc()),
        SimpleTerm(K3.getName(), K3.getName(), K3.getDoc()),
        SimpleTerm(K4.getName(), K4.getName(), K4.getDoc()),
        SimpleTerm(K5.getName(), K5.getName(), K5.getDoc()),
        SimpleTerm(K6.getName(), K6.getName(), K6.getDoc()),
        SimpleTerm(K7.getName(), K7.getName(), K7.getDoc()),
        SimpleTerm(K8.getName(), K8.getName(), K8.getDoc()),
        SimpleTerm(K9.getName(), K9.getName(), K9.getDoc()),
        SimpleTerm(K10.getName(), K10.getName(), K10.getDoc()),
        SimpleTerm(K11.getName(), K11.getName(), K11.getDoc()),
        ]
    return SimpleVocabulary(rc)


class IVouchersCreation(Interface):

    number = schema.Int(
        title=_(u"Anzahl der Berechtigungsscheine"),
        description=_(u"Wie viele Berechtigungsscheine sollen angelegt werden?"),
        required=True,
        )

    kategorie = schema.Choice(
        title=u"Kontingent",
        description=u"Für welche Kontingente wollen sie Berechtigungsscheine anlegen",
        source=get_kategorie,
        )


class IAdminLayer(IDGUVRequest):
    pass


class IUserLayer(IDGUVRequest):
    pass


class IIdentified(Interface):

    oid = Attribute(u"Unique identifier")


class IModel(Interface):

    __schema__ = Attribute(u'schema')
    __label__ = Attribute(u'label')


class IModelContainer(Interface):

    model = Attribute(u'Model')


class IDisablingVouchers(Interface):

    vouchers = schema.Set(
        value_type=schema.Choice(source=get_source('vouchers')),
        title=_(u"Berechtigungsscheine"),
        required=True,
    )


class IJournalEntry(Interface):

    jid = schema.Int(
        title=_(u"Unique journal entry id"),
        required=True,
    )

    date = schema.Datetime(
        title=_(u"Date"),
        required=True,
    )

    action = schema.TextLine(
        title=_(u"Aktion"),
        required=True,
    )

    userid = schema.Choice(
        source=get_source('accounts'),
        title=_(u"User identifier"),
        required=True,
    )

    note = schema.Text(
        title=_(u"Notiz"),
        required=True,
    )

    oid = schema.Int(
        title=_(u"Object id"),
        required=True,
    )



@grok.provider(IContextSourceBinder)
def reason(context):
    rc=[
       SimpleTerm('Charge gesperrt', 'Charge gesperrt', u'Charge gesperrt'),
       SimpleTerm('Fehleingabe', 'Fehleingabe', u'Fehleingabe'),
       SimpleTerm('FFW-Budgetprfung', 'FFW-Budgetprfung', u'FFW-Budgetprüfung'),
       SimpleTerm('Information', 'Information', u'Information'),
       SimpleTerm('Personalfluktuation', 'Personalfluktuation', u'Personalfluktuation'),
       SimpleTerm('zustliche Beschäftigte/Gruppen/Kolonnen', 'zustliche Beschftigte/Gruppen/Kolonnen', u'zusätliche Beschäftigte/Gruppen/Kolonnen'),
       SimpleTerm('zustzliche Standorte', 'zustzliche Standorte', u'zusätzliche Standorte'),
    ]
    return SimpleVocabulary(rc)


def get_journal_entry_title(entry):
    source = reason(None)
    try:
        return source.getTerm(entry).title
    except:
        return entry


class IJournalEntryExt(Interface):

    action = schema.Choice(
        title=u"Betreff",
        required=True,
        source=reason,
    )


class IJournalize(Interface):

    note = schema.TextLine(
        title=_(u"Notiz"),
        description=u"Eintrag in der Historie.",
        required=False,
    )


def gN(context=None):
    if VOCABULARIES:
        return VOCABULARIES['account'](context)
    return u""


class IAccount(Interface):

    oid = schema.TextLine(
        title=_(u"Unique identifier"),
        description=_(u"Eindeutiger Schlüssel OID"),
        required=True,
    )

    login = schema.TextLine(
        title=_(u"Benutzerkennung"),
        description=_(u"Benutzerkennung"),
        required=True,
        defaultFactory=gN,
    )

    az = schema.TextLine(
        title=_(u"Mitbenutzerkennung"),
        description=_(u"Mitbenutzerkennung"),
        required=True,
        default=u"eh",
    )

    anrede = schema.Choice(
        title=_(u"Anrede"),
        description=_(u"Bitte wählen Sie eine Anrede."),
        values = (u'Herr', u'Frau'),
        required = True,
    )

    titel = schema.TextLine(
        title=_(u"Titel"),
        description=_(u"Bitte geben Sie hier Ihren Titel ein."),
        required = False,
    )

    vname = schema.TextLine(
        title=_(u"Vorname"),
        description=_(u"Bitte geben Sie hier Ihren Vornamen ein."),
        required=True,
    )

    nname = schema.TextLine(
        title=_(u"Nachname"),
        description=_(u"Bitte geben Sie hier Ihren Nachnamen ein."),
        required=True,
    )

    vorwahl = schema.TextLine(
        title=_(u"Vorwahl"),
        description=u"Bitte geben Sie hier Ihre Vorwahl ein.",
        required=True,
    )

    phone = schema.TextLine(
        title=_(u"Phone"),
        description=u"Bitte geben Sie hier Ihre Telefonnummer ein.",
        required=True,
    )

    email = schema.TextLine(
        title=_(u"E-Mail"),
        description=u"Bitte geben Sie hier Ihre E-Mail-Adresse ein.",
        required=True,
    )

    funktion = schema.TextLine(
        title=_(u"Funktion"),
        description=u"Welche Funktion bekleiden Sie im Unternehmen.",
        required=True,
    )

    password = schema.Password(
        title=_(u"Password for observation access"),
        description=u"Bitte vergeben Sie ein Passwort. (Mindestlänge 8 Zeichen)",
        required=True,
    )


class ICategory(Interface):

    oid = schema.TextLine(
        title=_(u"Unique user identifier"),
        description=_(u"Internal identifier of the user"),
        required=True,
    )

    kat1 = schema.Bool(
        title=_(u"Kat 1"),
        required=True,
    )

    kat2 = schema.Bool(
        title=_(u"Kat 2"),
        required=True,
    )

    kat3 = schema.Bool(
        title=_(u"Kat 3"),
        required=True,
    )

    kat4 = schema.Bool(
        title=_(u"Kat 4"),
        required=True,
    )

    kat5 = schema.Bool(
        title=_(u"Kat 5"),
        required=True,
    )

    kat6 = schema.Bool(
        title=_(u"Kat 6"),
        required=True,
    )

    kat7 = schema.Bool(
        title=_(u"Kat 7"),
        required=True,
    )

    kat8 = schema.Bool(
        title=_(u"Kat 8"),
        required=True,
    )

    kat9 = schema.Bool(
        title=_(u"Kat 9"),
        required=True,
    )

    kat10 = schema.Bool(
        title=_(u"Kat 10"),
        required=True,
    )

    kat11 = schema.Bool(
        title=_(u"Kat 11"),
        required=True,
    )


class IAddress(Interface):

    oid = schema.TextLine(
        title=_(u"Unique user identifier"),
        description=_(u"Internal identifier of the user"),
        required=False,
    )

    mnr = schema.TextLine(
        title=_(u"Mitgliedsnummer"),
        required=False,
    )

    name1 = schema.TextLine(
        title=_(u"Address Name1"),
        required=True,
    )

    name2 = schema.TextLine(
        title=_(u"Address Name2"),
        required=False,
    )

    name3 = schema.TextLine(
        title=_(u"Address Name3"),
        required=False,
    )

    street = schema.TextLine(
        title=_(u"Address Street"),
        required=False,
    )

    number = schema.TextLine(
        title=_(u"Address Number"),
        required=False,
    )

    zip_code = schema.TextLine(
        title=_(u"Address Zip"),
        required=True,
    )

    city = schema.TextLine(
        title=_(u"Address City"),
        required=True,
    )


def ms(name):
    @grok.provider(IContextSourceBinder)
    def source(context):
        return VOCABULARIES[name](context)
    return source




class IInvoice(Interface):

    oid = schema.TextLine(
        title=_(u"Titel oid Zuordnung"),
        description=_(u"oid Zuordnung"),
        required=False,
    )

    vouchers = schema.Set(
        #value_type=schema.Choice(source=get_source('vouchers')),
        value_type=schema.Choice(source=ms('mysource')),
        #value_type=schema.TextLine(),
        title=_(u"Vouchers"),
        required=True,
    )

    reason = schema.Choice(
        title=_(u'Begründung'),
        description=_(u'Sind sie mit den Berechtigungsscheinen der Rechnung nicht einverstanden?'),
        source=get_reason,
        required = False,
    )

    description = schema.Text(
        title=_('Beschreibung'),
        required=False,
    )

#    creation_date = schema.Datetime(
#        title=_(u"Creation date"),
#        required=True,
#    )


class IVoucher(Interface):

    oid = schema.TextLine(
        title=_(u"Titel oid Berechtigungsschein"),
        description=_(u"oid Berechtigungsschein"),
        required=True,
    )

    creation_date = schema.Datetime(
        title=_(u"Creation date"),
        required=True,
    )

    modification_date = schema.Datetime(
        title=_(u"Modifikationsdatum"),
        required=True,
    )

    status = schema.TextLine(
        title=_(u"Status"),
        required=True,
    )

    user_id = schema.TextLine(
        title=_(u"User id"),
        required=True,
    )

    invoice_id = schema.TextLine(
        title=_(u"Invoice id"),
        required=True,
    )


class K1(Interface):
    u"""Verwaltung, Büro (K1)"""

    mitarbeiter = schema.Int(
        title=_(u"Anzahl Beschäftigte (ohne Beamte)"),
    )

    standorte = schema.Int(
        title=_(u"Anzahl Standorte"),
    )

    bestaetigung = schema.Bool(
        title = _(u"Bestätigung:"),
    )

    taggedValue('infolink',
                'http://www.ukh.de/fileadmin/ukh.de/Erste_Hilfe/Erste_Hilfe_PDF_2016_NEU/UKH_K1_Erste-Hilfe_in_Verwaltungs-und_Buerobetrieben.pdf')
    taggedValue('descr', HK1)


class K2(Interface):
    u"""Sonstige Betriebe und Hochschulen (K2)"""

    mitarbeiter = schema.Int(
        title=_(u"Anzahl Beschäftigte (ohne Beamte)"),
    )

    standorte = schema.Int(
        title=_(u"Anzahl Standorte"),
    )

    bestaetigung = schema.Bool(
        title = _(u"Bestätigung:"),
    )

    taggedValue('infolink',
                'http://www.ukh.de/fileadmin/ukh.de/Erste_Hilfe/Erste_Hilfe_PDF_2016_NEU/UKH_K2_Erste-Hilfe_in_anderen_Betrieben_und_Hochschulen.pdf')
    taggedValue('descr', HK2)


class K3(Interface):
    u"""Kindertageseinrichtungen (K3)"""

    gruppen = schema.Int(
        title=_(u"Anzahl der Kindergruppen"),
    )

    kitas = schema.Int(
        title=_(u"Anzahl Kita Standorte"),
    )

    bestaetigung = schema.Bool(
        title = _(u"Bestätigung:"),
    )

    taggedValue('infolink',
                'http://www.ukh.de/fileadmin/ukh.de/Erste_Hilfe/Erste_Hilfe_PDF_2016_NEU/UKH_K3_Erste-Hilfe_in_Kindertageseinrichtungen.pdf')
    taggedValue('descr', HK3)


class K4(Interface):
    u"""Bauhof / Entsorgung (Kolonnen) (K4)"""

    kolonne = schema.Int(
        title=_(u"Anzahl der Kolonnen"),
    )

    bestaetigung = schema.Bool(
        title = _(u"Bestätigung:"),
    )

    taggedValue('infolink',
                'http://www.ukh.de/fileadmin/ukh.de/Erste_Hilfe/Erste_Hilfe_PDF_2016_NEU/UKH_K4_Erste-Hilfe-fuer_Beschaeftigte_in_Kolonnen.pdf')
    taggedValue('descr', HK4)


class K5(Interface):
    u"""Beschäftigte und Einrichtungen mit erhöhter Gefährdung (K5)"""

    mitarbeiter = schema.Int(
        title=_(u"Anzahl Beschäftigte (ohne Beamte)"),
    )

    bestaetigung = schema.Bool(
        title = _(u"Bestätigung:"),
    )

    taggedValue('infolink',
                'http://www.ukh.de/fileadmin/ukh.de/Erste_Hilfe/Erste_Hilfe_PDF_2016_NEU/UKH_K5_Erste-Hilfe_fuer_Beschaeftigte_und_Einrichtungen_mit_erhoehter_Gefaehrdung.pdf')
    taggedValue('descr', HK5)


class K6(Interface):
    u"""Beschäftigte und Einrichtungen mit besonders hoher Gefährdung (K6)"""

    mitarbeiter = schema.Int(
        title=_(u"Anzahl Beschäftigte (ohne Beamte)"),
    )

    bestaetigung = schema.Bool(
        title = _(u"Bestätigung:"),
    )

    taggedValue('infolink',
                'http://www.ukh.de/fileadmin/ukh.de/Erste_Hilfe/Erste_Hilfe_PDF_2016_NEU/UKH_K6_Erste-Hilfe_fuer_Beschaeftigte_in_Einrichtungen_mit_besonders_hoher_Gefaehrdung.pdf')
    taggedValue('descr', HK6)


class K7(Interface):
    u"""Schulen (nur Lehrkräfte) (K7)"""

    lehrkraefte = schema.Int(
        title=_(u"Anzahl Lehrkräfte (ohne Schulbetreuung, Sekretariat, Reinigungs- und Hausmeistertätigkeiten)"),
    )

    bestaetigung = schema.Bool(
        title = _(u"Bestätigung:"),
    )

    taggedValue('infolink',
                'http://www.ukh.de/fileadmin/ukh.de/Erste_Hilfe/Erste_Hilfe_PDF_2016_NEU/UKH_K7_Erste-Hilfe_fuer_Lehrkraefte_an_Schulen.pdf')
    taggedValue('descr', HK7)


class K8(Interface):
    u"""Schulpersonal der Schulträger (ohne Schulbetreuung) (K8)"""

    schulstandorte = schema.Int(
        title=_(u"Anzahl Schulstandorte"),
    )

    bestaetigung = schema.Bool(
        title = _(u"Bestätigung:"),
    )

    taggedValue('infolink',
                'http://www.ukh.de/fileadmin/ukh.de/Erste_Hilfe/Erste_Hilfe_PDF_2016_NEU/UKH_K8_Erste-Hilfe_fuer_Schulpersonal_der_Schultraeger.pdf')
    taggedValue('descr', HK8)


class K9(Interface):
    u"""Schulbetreuung (K9)"""

    gruppen = schema.Int(
        title=_(u"Anzahl Gruppen"),
    )

    bestaetigung = schema.Bool(
        title = _(u"Bestätigung:"),
    )

    taggedValue('infolink',
                'http://www.ukh.de/fileadmin/ukh.de/Erste_Hilfe/Erste_Hilfe_PDF_2016_NEU/UKH_K9_Erste-Hilfe_fuer_die_Schulbetreuung.pdf')
    taggedValue('descr', HK9)


from zope.schema import ValidationError
import re

class PIntError(ValidationError):
    u""" Bitte tragen Sie eine Zahl ein."""


def validatePInt(value):
    if value:
        checkzahl = re.compile(r'^[0-9]+$').match
        if not bool(checkzahl(value)):
            raise PIntError()
        else:
            if int(value) < 0:
                raise PIntError()
    return True


def validatePFloat(value):
    if value:
        value = value.replace(',', '.')
        try:
            float(value)
            if float(value) < 0:
                raise PIntError()
        except:
            raise PIntError()
    return True

class K10(Interface):
    u"""Freiwillige Feuerwehren (K10)"""

    einsatzkraefte = schema.TextLine(
        title=_(u"Aktive Einsatzkräfte"),
        description=_(u'Bitte tragen Sie die Summe der aktiven Einsatzkräfte (ohne Betreuer/innen der Kindergruppen und Jugendfeuerwehren) ein:'),
        constraint=validatePInt,
    )

    betreuer = schema.TextLine(
        title=_(u"Betreuer/innen der Kindergruppen und Jugendfeuerwehren"),
        description=_(u'Die Anzahl der Betreuer/innen der Kindergruppen und Jugendfeuerwehren (inkl. deren Vertreter/innen):'),
        constraint=validatePInt,
    )

    last_budget = schema.TextLine(
        title=_(u"Höhe des nicht verbrauchten Budgets in €"),
        #description=_(u'Bitte tragen Sie die Höhe des in 2017/18 nicht benötigten Budgets ein. Noch vorhandenes Budget wird Ihnen auf den Folgezeitraum 2019/20 angerechnet.'),
        description=_(RESTBUDGET),
        constraint=validatePFloat,
    )

    bestaetigung = schema.Bool(
        title = _(u"Bestätigung:"),
        description=_(u'')
    )

    taggedValue('infolink',
                'http://www.ukh.de/fileadmin/ukh.de/Erste_Hilfe/Erste_Hilfe_PDF_2016_NEU/UKH_K10_Erste-Hilfe_in_der_Freiwilligen_Feuerwehr.pdf')
    taggedValue('descr', HK10)


class K11(Interface):
    u"""Gesundheitsdienste (K11)"""

    ma_verwaltung = schema.Int(
        title=_(u"Anzahl Beschäftigte (ohne Beamte) in der Verwaltung"),
    )

    st_verwaltung = schema.Int(
        title=_(u"Anzahl Standorte der Verwaltung"),
    )

    ma_technik = schema.Int(
        title=_(u"Anzahl Beschäftigte (ohne Beamte) im technischen Bereich"),
    )

    st_technik = schema.Int(
        title=_(u"Anzahl Standorte des technischen Bereichs"),
    )

    bestaetigung = schema.Bool(
        title = _(u"Bestätigung:"),
    )

    taggedValue('infolink',
                'http://www.ukh.de/fileadmin/ukh.de/Erste_Hilfe/Erste_Hilfe_PDF_2016_NEU/UKH_K11_Erste-Hilfe_in_Gesundheitsdiensten.pdf')
    taggedValue('descr', HK11)


class IVoucherSearch(Interface):

    oid = schema.TextLine(
        #source=get_source('all_vouchers'),
        title=_(u"Vouchers"),
        required=False,
        missing_value=None,
    )

    status = schema.TextLine(
        title=_(u"Status"),
        required=False,
    )

    user_id = schema.Choice(
        title=_(u"User id"),
        source=get_source('accounts'),
        required=False,
    )


class IInvoiceSearch(Interface):

    oid = schema.Choice(
        title=_(u"Zuordnung"),
        required=False,
        source=get_source('invoices'),
    )


@grok.provider(IContextSourceBinder)
def voc_subject(context):
    rc = [
        SimpleTerm(u'',
                   u'',
                   u''),
        SimpleTerm(u'Änderung der Kontaktdaten',
                   u'Aenderung der Kontaktdaten',
                   u'Änderung der Kontaktdaten (Anschrift, Name, Tel., Email)'),
        SimpleTerm(u'Kontingente',
                   u'Kontingente',
                   u'Kontingente'),
        SimpleTerm(u'Berechtigungsscheine',
                   u'Berechtigungsscheine',
                   u'Berechtigungsscheine'),
        SimpleTerm(u'Lehrgangsteilnahme',
                   u'Lehrgangsteilnahme',
                   u'Lehrgangsteilnahme'),
        SimpleTerm(u'Rechnung',
                   u'Rechnung',
                   u'Rechnung'),
        SimpleTerm(u'Materialbestellung',
                   u'Materialbestellung',
                   u'Materialbestellung (Ihre Anfrage wird direkt an ukh@ukh.de weitergeleitet)'),
        SimpleTerm(u'Sonstiges',
                   u'Sonstiges',
                   u'Sonstiges'),
    ]
    return SimpleVocabulary(rc)


class IKontakt(Interface):

    betreff = schema.Choice(
        title=_(u'Betreff'),
        source = voc_subject,
        )

    text = schema.Text(
        title=_(u'Nachricht')
        )


class IBankverbindung(Interface):

    kontoinhaber = schema.TextLine(
        title=u"<h3>Bankverbindung zur Überweisung des Budgets:</h3> <br>Kontoinhaber",
    )

    bank = schema.TextLine(
        title=u"Kreditinstitut",
    )

    iban = schema.TextLine(
        title=u"IBAN",
        constraint=validation.validateIBAN,
    )
