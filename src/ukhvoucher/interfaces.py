# -*- coding: utf-8 -*-

import grokcore.component as grok
from . import VOCABULARIES
from ukhtheme.uvclight import IDGUVRequest
from ukhvoucher import _
from zope import schema
from zope.interface import Interface, Attribute
from zope.schema.interfaces import IContextSourceBinder


def get_source(name):
    @grok.provider(IContextSourceBinder)
    def source(context):
        return VOCABULARIES[name](context)
    return source


class IVouchersCreation(Interface):

    number = schema.Int(
        title=_(u"Number of vouchers"),
        description=_(u"Number of vouchers to query"),
        required=True,
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


class IAccount(Interface):

    oid = schema.TextLine(
        title=_(u"Unique identifier"),
        description=_(u"Internal identifier"),
        required=True,
    )

    name = schema.TextLine(
        title=_(u"Fullname"),
        description=_(u"Please give your Fullname here"),
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
    )

    description = schema.TextLine(
        title=_('Beschreibung'),
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

    user_id = schema.Choice(
        title=_(u"User id"),
        source=get_source('accounts'),
        required=True,
    )

    invoice_id = schema.Choice(
        title=_(u"Invoice id"),
        source=get_source('invoices'),
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

