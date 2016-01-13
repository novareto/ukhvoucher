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
from plone.memoize import forever



@grok.provider(IContextSourceBinder)
def get_oid(context):
    from sqlalchemy.sql.functions import max
    from ukhvoucher.models import Accounts, AddressTraeger, Address, AddressEinrichtung
    rc = []
    session = get_session('ukhvoucher')
    if isinstance(context, Accounts):
        try:
            oid = int(session.query(max(Address.oid)).one()[0]) + 1
        except:
            oid = 999000000000001
        oid = 999000000000001

        rc = [SimpleTerm(oid, oid, u'%s neues Unternehmen' % str(oid))]
    @forever.memoize
    def getValue():
        for x in session.query(Address):
            rc.append(SimpleTerm(x.oid, x.oid, "%s - %s - %s %s" % (x.oid, x.mnr, x.name1, x.name2)))
        for x in session.query(AddressTraeger):
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
        SimpleTerm(u'', u'', u'OK'),
        SimpleTerm(u'Teilnehmer != Rechnung', u'Teilnehmer != Rechnung', u'Teilnehmer != Rechnung'),
        SimpleTerm(u'Rechnungssumme falsch', u'Rechnungssumme falsch', u'Rechnungssumme falsch'),
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
        ]
    return SimpleVocabulary(rc)


class IVouchersCreation(Interface):

    number = schema.Int(
        title=_(u"Number of vouchers"),
        description=_(u"Number of vouchers to query"),
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
        title=_(u"Vouchers"),
        required=True,
    )


class IJournalize(Interface):

    note = schema.TextLine(
        title=_(u"Note"),
        description=u"Journal note.",
        required=False,
    )
    

class IAccount(Interface):

#    oid = schema.TextLine(
#        title=_(u"Unique identifier"),
#        description=_(u"Internal identifier"),
#        required=True,
#    )

    oid = schema.Choice(
        title=_(u"Unique identifier"),
        description=_(u"Internal identifier"),
        required=True,
        source=get_oid,
    )

    login = schema.TextLine(
        title=_(u"Benutzerkennung"),
        description=_(u"Benutzerkennung"),
        required=True,
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


class IAddress(Interface):

    oid = schema.TextLine(
        title=_(u"Unique user identifier"),
        description=_(u"Internal identifier of the user"),
        required=True,
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

    reason = schema.Choice(
        title=_(u'Begründung'),
        description=_(u'Bitte geben wählen Sie hier aus warum Sie mit der Rechnung nicht einverstanden sein'),
        source=get_reason,
        required = False,
    )

    description = schema.Text(
        title=_('Beschreibung'),
        required=False,
    )

    vouchers = schema.Set(
        value_type=schema.Choice(source=get_source('vouchers')),
        title=_(u"Vouchers"),
        required=True,
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

    mitarbeiter = schema.Int(
        title=_(u"Beschäftigte"),
    )


class IKG6(Interface):
    u"""Beschäftigte und Einrichtungen mit spezieller Gefährdung"""

    mitarbeiter = schema.Int(
        title=_(u"Beschäftigte"),
    )


class IKG7(Interface):
    u"""Schulen"""

    mitarbeiter = schema.Int(
        title=_(u"Anzahl Lehrkräfte"),
    )

