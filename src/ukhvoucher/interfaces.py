# -*- coding: utf-8 -*-

import grokcore.component as grok
from . import VOCABULARIES
from ukhtheme.uvclight import IDGUVRequest
from ukhvoucher import _
from uvc.content.interfaces import IContent
from zope import schema
from zope.interface import Interface, Attribute
from zope.location import ILocation
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

    address = schema.TextLine(
        title=_(u"Address"),
        required=True,
    )


class IInvoice(Interface):

    vouchers = schema.Set(
        value_type=schema.Choice(source=get_source('vouchers')),
        title=_(u"Vouchers"),
        required=True,
    )


class IVoucher(Interface):

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
