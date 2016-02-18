# -*- coding: utf-8 -*-

import grokcore.component as grok
from . import VOCABULARIES
from ukhtheme.uvclight import IDGUVRequest
from ukhvoucher import _
from zope import schema
from zope.interface import Interface, Attribute
from zope.schema.interfaces import IContextSourceBinder
from cromlech.sqlalchemy import get_session
from zope.schema.vocabulary import SimpleTerm, SimpleVocabulary
from plone.memoize import forever, ram
from time import time



@grok.provider(IContextSourceBinder)
def get_oid(context):
    from ukhvoucher.models import Accounts, AddressTraeger, Address, AddressEinrichtung
    rc = []
    rcc = []
    session = get_session('ukhvoucher')
    @ram.cache(lambda *args: time() // (600 * 60))
    def getValue():
        print " IAM CALLED"
        for x in session.query(Address):
            rc.append(SimpleTerm(x.oid, x.oid, "%s - %s - %s %s" % (x.oid, x.mnr, x.name1, x.name2)))
            rcc.append(x.oid)
        for x in session.query(AddressTraeger):
            if x.oid not in rcc:
                rc.append(SimpleTerm(x.oid, x.oid, "%s - %s - %s %s" % (x.oid, x.mnr, x.name1, x.name2)))
        for x in session.query(AddressEinrichtung):
            rc.append(SimpleTerm(x.oid, x.oid, "%s - %s - %s %s" % (x.oid, x.mnr, x.name1, x.name2)))
        return SimpleVocabulary(rc)
    return getValue()


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
        SimpleTerm(u'Ablehnung, da keine Teilnehmercodes anbei',
                   u'Ablehnung, da keine Teilnehmercodes anbei',
                   u'Ablehnung, da keine Teilnehmercodes anbei'),
        SimpleTerm(u'Ablehnung, da nicht ausreichend Teilnehmercodes anbei',
                   u'Ablehnung, da nicht ausreichend Teilnehmercodes anbei',
                   u'Ablehnung, da nicht ausreichend Teilnehmercodes anbei'),
        SimpleTerm(u'Ablehnung, da doppelte Teilnehmercodes eingereicht wurden',
                   u'Ablehnung, da doppelte Teilnehmercodes eingereicht wurden',
                   u'Ablehnung, da doppelte Teilnehmercodes eingereicht wurden'),
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
        SimpleTerm(u'Kuerzung, da nicht ausreichend Teilnehmercodes anbei',
                   u'Kuerzung, da nicht ausreichend Teilnehmercodes anbei',
                   u'Kürzung, da nicht ausreichend Teilnehmercodes anbei'),
        SimpleTerm(u'Kuerzung, da doppelte Teilnehmercodes eingereicht wurden',
                   u'Kuerzung, da doppelte Teilnehmercodes eingereicht wurden',
                   u'Kürzung, da doppelte Teilnehmercodes eingereicht wurden'),
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
        SimpleTerm(IKG1.getName(), IKG1.getName(), IKG1.getDoc()),
        SimpleTerm(IKG2.getName(), IKG2.getName(), IKG2.getDoc()),
        SimpleTerm(IKG3.getName(), IKG3.getName(), IKG3.getDoc()),
        SimpleTerm(IKG4.getName(), IKG4.getName(), IKG4.getDoc()),
        SimpleTerm(IKG5.getName(), IKG5.getName(), IKG5.getDoc()),
        SimpleTerm(IKG6.getName(), IKG6.getName(), IKG6.getDoc()),
        SimpleTerm(IKG7.getName(), IKG7.getName(), IKG7.getDoc()),
        SimpleTerm(IKG8.getName(), IKG8.getName(), IKG8.getDoc()),
        SimpleTerm(IKG9.getName(), IKG9.getName(), IKG9.getDoc()),
        ]
    return SimpleVocabulary(rc)


class IVouchersCreation(Interface):

    number = schema.Int(
        title=_(u"Anzahl der Gutscheine"),
        description=_(u"Wie viele Gutscheine sollen angelegt werden?"),
        required=True,
        )

    kategorie = schema.Choice(
        title=u"Kategorie",
        description=u"Für welche Kategorie wollen sie Gutscheine anlegen",
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
        title=_(u"Gutscheine"),
        required=True,
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

#    oid = schema.TextLine(
#        title=_(u"Unique identifier"),
#        description=_(u"Internal identifier"),
#        required=True,
#    )

    oid = schema.Choice(
        title=_(u"Unique identifier"),
        description=_(u"Eindeutiger Schlüssel OID"),
        required=True,
        source=get_oid,
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
        default=u"00",
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

    phone = schema.TextLine(
        title=_(u"Phone"),
        description=u"Bitte geben Sie hier Ihre Telefonnummer für Rückfragen an.",
        required=True,
    )

    email = schema.TextLine(
        title=_(u"E-Mail"),
        description=u"Ihre E-Mailadresse benötigen Sie später beim Login.",
        required=True,
    )

    password = schema.Password(
        title=_(u"Password for observation access"),
        description=u"Bitte vergeben Sie ein Passwort.",
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
        title=_(u"Kategorie 8 - Angestellte in Schulen"),
        required=True,
    )

    kat9 = schema.Bool(
        title=_(u"Kategorie 9 - Schulbetreuung"),
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
        required=True,
    )

    number = schema.TextLine(
        title=_(u"Address Number"),
        required=True,
    )

    zip_code = schema.TextLine(
        title=_(u"Address Zip"),
        required=True,
    )

    city = schema.TextLine(
        title=_(u"Address City"),
        required=True,
    )


class IInvoice(Interface):

    oid = schema.TextLine(
        title=_(u"Unique Invoice identifier"),
        description=_(u"Internal identifier of the invoice"),
        required=True,
        defaultFactory=getInvoiceId,
    )

    vouchers = schema.Set(
        value_type=schema.Choice(source=get_source('vouchers')),
        title=_(u"Vouchers"),
        required=True,
    )

    reason = schema.Choice(
        title=_(u'Begründung'),
        description=_(u'Sind sie mit den Gutscheinen der Rechnung nicht einverstanden?'),
        source=get_reason,
        required = False,
    )

    description = schema.Text(
        title=_('Beschreibung'),
        required=False,
    )



class IVoucher(Interface):

    oid = schema.TextLine(
        title=_(u"Unique Invoice identifier"),
        description=_(u"Internal identifier of the invoice"),
        required=True,
    )

    creation_date = schema.Datetime(
        title=_(u"Creation date"),
        required=True,
    )

    status = schema.TextLine(
        title=_(u"Status"),
        required=True,
    )

    user_id = schema.TextLine(
        title=_(u"User id"),
        #source=get_source('accounts'),
        required=True,
    )

    invoice_id = schema.TextLine(
        title=_(u"Invoice id"),
        #source=get_source('invoices'),
        required=True,
    )


class IKG1(Interface):
    u"""Verwaltung, Büro"""

    mitarbeiter = schema.Int(
        title=_(u"Beschäftigte"),
    )

    standorte = schema.Int(
        title=_(u"Standorte"),
    )


class IKG2(Interface):
    u"""Andere Betriebe"""

    mitarbeiter = schema.Int(
        title=_(u"Beschäftigte"),
    )

    standorte = schema.Int(
        title=_(u"Standorte"),
    )


class IKG3(Interface):
    u"""Kinderbetreuungseinrichtungen"""

    gruppen = schema.Int(
        title=_(u"Anzahl der Kindergruppen"),
    )

    kitas = schema.Int(
        title=_(u"Anzahl Kommunale Kitas"),
    )


class IKG4(Interface):
    u"""Entsorgung / Bauhof (Kolonne)"""

    kolonne = schema.Int(
        title=_(u"Anzahl der Kolonnen"),
    )


class IKG5(Interface):
    u"""Einrichtungen mit spezieller Gefährdung"""

    merkmal = schema.Choice(
        title=u"Welches Merkmal trifft für die besondere Gefährdung zu:",
        values=(u'',
                u'Beschaeftigte im Freilichtmuseum Hessenpark',
                u'Beschaeftigte in der Tierpflege'))

    mitarbeiter = schema.Int(
        title=_(u"Beschäftigte"),
    )


class IKG6(Interface):
    u"""Beschäftigte und Einrichtungen mit spezieller Gefährdung"""

    merkmal = schema.Choice(
        title=u"Welches Merkmal trifft für die besondere Gefährdung zu:",
        values=(u'',
                u'mit Waldarbeiten Beschaeftigte von Hessen-Forst',
                u'im Strassendienst Beschaeftigte von Hessen mobil',
                u'im Aussendienst Beschaeftigte bei der Hessischen Verwaltung fuer Bodenmanagement',
                u'mit Arbeiten im Kanalnetz Beschaeftigte in Abwasserbetrieben',
                u'mit Arbeiten im Schaechten Beschaeftigte in Wasserversorgungsbetrieben',
                u'auf Deponien Beschaeftigte',
                u'Beschaeftigte von N*ICE (ohne Leiharbeitnehmer)'))

    mitarbeiter = schema.Int(
        title=_(u"Beschäftigte"),
    )


class IKG7(Interface):
    u"""Schulen"""

    mitarbeiter = schema.Int(
        title=_(u"Anzahl Lehrkräfte"),
    )


class IKG8(Interface):
    u"""Angestellte in Schulen"""

    mitarbeiter = schema.Int(
        title=_(u"Angestellte Personen"),
    )


class IKG9(Interface):
    u"""Schulbetreuung"""

    mitarbeiter = schema.Int(
        title=_(u"Angestellte Personen"),
    )


class IVoucherSearch(Interface):

    oid = schema.Choice(
        source=get_source('all_vouchers'),
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
        title=_(u"Unique Invoice identifier"),
        description=_(u"Internal identifier of the invoice"),
        required=False,
        source=get_source('invoices'),
    )

    reason = schema.Choice(
        title=_(u'Begründung'),
        description=_(u'Sind sie mit den Gutscheinen der Rechnung nicht einvers\
tanden?'),
        source=get_reason,
        required=False,
    )
