# -*- coding: utf-8 -*-

from . import Base
from .interfaces import IVoucher, IInvoice, IAddress, IAccount, ICategory
from .interfaces import IModel, IModelContainer, IIdentified
from . import _
from zope.location import ILocation, Location, LocationProxy, locate

import uvclight
from urllib import quote, unquote
from cromlech.sqlalchemy import get_session
from dolmen.sqlcontainer import SQLContainer
from sqlalchemy import *
from sqlalchemy.orm import relationship, backref
from uvc.content.interfaces import IContent
from zope.interface import implementer
from zope.location import Location

from sqlalchemy import types


schema = ''
schema = 'UKHINTERN.'

print "SCHEMA", schema


class StrippedString(types.TypeDecorator):
    '''
    Returns CHAR values with spaces stripped
    '''

    impl = types.String

    def process_bind_param(self, value, dialect):
        "No-op"
        return value

    def process_result_value(self, value, dialect):
        "Strip the trailing spaces on resulting values"
        return value.rstrip()

    def copy(self):
        "Make a copy of this type"
        return StrippedString(self.impl.length)



@implementer(IModel, IIdentified, IAddress)
class Address(Base, Location):

    __tablename__ = 'z1ehradr_t'
    __schema__ = IAddress
    __label__ = _(u"Address")

    if schema:
        __table_args__ = {"schema": schema[:-1]}

    oid = Column('oid', Integer, primary_key=True, autoincrement=True)
    name1 = Column('iknam1', String(28))
    name2 = Column('iknam2', String(28))
    name3 = Column('iknam3', String(28))
    street = Column('ikstr', String(46))
    number = Column('ikhnr', String(3))
    mnr = Column('trgmnr', String(15))
    zip_code = Column('ikhplz', String(5))
    city = Column('ikhort', String(24))
    user_id = Column('user_id', Integer, ForeignKey(schema + 'Z1EXT9AA.oid'))

    @property
    def title(self):
        return "Adresse des Benutzers %s" % (self.oid)

    # search attributes
    search_attr = "name1"
    searchable_attrs = ("oid", "name1", "street", 'zip_code', 'city')

    mnr = ""


class JournalEntry(Base):
    __tablename__ = 'Z1EHRJRN_T'
    if schema:
        __table_args__ = {"schema": schema[:-1]}

    jid = Column('jrnoid', Integer, primary_key=True)
    date = Column('jrn_dat', DateTime)
    action = Column('aktion', String(20))
    userid = Column('user_id', String(30))
    note = Column('text', String(500))
    oid = Column('oid', Integer)


class AddressEinrichtung(Base):
    __tablename__ = 'z1ext9ac'
    if schema:
        __table_args__ = {"schema": schema[:-1]}

    oid = Column('enrrcd', String, primary_key=True)
    mnr = Column('enrnum', String)
    name1 = Column('iknam1', String(28))
    name2 = Column('iknam2', String(28))
    name3 = Column('iknam3', String(28))
    street = Column('ikstr', String(46))
    number = Column('ikhnr', String(3))
    zip_code = Column('ikhplz', String(5))
    city = Column('ikhort', String(24))


class AddressTraeger(Base):
    __tablename__ = 'z1ext9ab'
    if schema:
        __table_args__ = {"schema": schema[:-1]}

    oid = Column('trgrcd', String, primary_key=True)
    mnr = Column('trgmnr', String)
    name1 = Column('iknam1', String(28))
    name2 = Column('iknam2', String(28))
    name3 = Column('iknam3', String(28))
    street = Column('ikstr', String(46))
    number = Column('ikhnr', String(3))
    zip_code = Column('ikhplz', String(5))
    city = Column('ikhort', String(24))


@implementer(IModel, IIdentified, ICategory)
class Category(Base, Location):

    __tablename__ = 'z1ehrkat_t'
    __schema__ = ICategory
    __label__ = _(u"Kategorie")

    if schema:
        __table_args__ = {"schema": schema[:-1]}

    oid = Column('oid', String, primary_key=True)
    kat1 = Column('kat1', Boolean)
    kat2 = Column('kat2', Boolean)
    kat3 = Column('kat3', Boolean)
    kat4 = Column('kat4', Boolean)
    kat5 = Column('kat5', Boolean)
    kat6 = Column('kat6', Boolean)
    kat7 = Column('kat7', Boolean)

    @property
    def title(self):
        return "Kategorie %s" % self.oid

    # search attributes
    search_attr = "oid"
    searchable_attrs = ("oid",)


@implementer(IModel, IIdentified, IAccount)
class Account(Base, Location):

    __tablename__ = 'Z1EXT9AA'
    __schema__ = IAccount
    __label__ = _(u"Account")
    if schema:
        __table_args__ = {"schema": schema[:-1]}

    model = Address

    oid = Column('oid', Integer, primary_key=True)
    email = Column('email', String)
    login = Column('login', String, primary_key=True)
    az = Column('az', String, primary_key=True)
    vname = Column('vname', String)
    nname = Column('nname', String)
    phone = Column('tlnr', String)
    rechte = Column('rechte', String)
    password = Column('passwort', String)
    merkmal = Column('merkmal', String)

    @property
    def title(self):
        return "%s (%s)" % (self.email, self.oid)

    @property
    def categories(self):
        session = get_session('ukhvoucher')
        return session.query(Category).filter(Category.oid == self.oid).all()

    # search attributes
    search_attr = "oid"
    searchable_attrs = ("oid", "email", "name")

@implementer(IModel, IIdentified, IVoucher)
class Voucher(Base, Location):

    __tablename__ = 'z1ehrvch_t'
    __schema__ = IVoucher
    __label__ = _(u"Vouchers")
    if schema:
        __table_args__ = {"schema": schema[:-1]}

    oid = Column('vch_oid', Integer, primary_key=True)
    creation_date = Column('erst_dat', DateTime)
    status = Column('status', String)
    cat = Column('kat', String)
    user_id = Column('user_id', Integer, ForeignKey(schema + 'Z1EXT9AA.oid'))
    invoice_id = Column('rech_oid', Integer, ForeignKey(schema + 'z1ehrrch_t.rech_oid'))
    generation_id = Column('gen_oid', Integer, ForeignKey(schema + 'z1ehrbgl_t.bgl_oid'))

    # relations
    user = relationship('Account')

    @property
    def title(self):
        return "Gutschein %s" % self.oid

    # search attributes
    search_attr = "oid"
    searchable_attrs = ("oid", "status", "user_id")

    @property
    def displayData(self):
        import json
        rc = []
        data = json.loads(self.generation.data)
        if isinstance(data, dict):
            for k, v in json.loads(self.generation.data).items():
                rc.append("%s: %s" % (k, v))
            return '; '.join(rc)
        return data



@implementer(IModel, IIdentified, IInvoice)
class Invoice(Base, Location):

    __tablename__ = 'z1ehrrch_t'
    __schema__ = IInvoice
    __label__ = _(u"Invoice")
    if schema:
        __table_args__ = {"schema": schema[:-1]}

    oid = Column('rech_oid', Integer, primary_key=True)
    reason = Column('grund', StrippedString)
    description = Column('text', String)

    vouchers = relationship(
        Voucher, collection_class=set,
        backref=backref('invoice', uselist=False))

    @property
    def title(self):
        return "Rechnung %s" % self.oid

    search_attr = "rech_oid"
    searchable_attrs = ("oid", "reason")


class Generation(Base):
    __tablename__ = 'z1ehrbgl_t'
    if schema:
        __table_args__ = {"schema": schema[:-1]}

    oid = Column('bgl_oid', Integer, primary_key=True)
    date = Column('vcb_dat', DateTime)
    type = Column('kat', String(20))
    data = Column('text', String(500))
    user = Column('user_id', Integer, ForeignKey(schema + 'Z1EXT9AA.oid'))
    uoid = Column('oid', Integer)

    voucher = relationship("Voucher", backref=backref('generation') )




@implementer(IContent, IModelContainer)
class Accounts(SQLContainer):
    __label__ = _(u"Accounts")

    model = Account
    listing_attrs = uvclight.Fields(Account.__schema__).select(
        'oid', 'login', 'email', 'name')

    def key_converter(self, id):
        keys = unquote(id)
        try:
            oid, login, az = keys.split(' ')
            return oid, login, az
        except ValueError:
            return None

    def key_reverse(self, obj):
        return quote('%s %s %s' % (obj.oid, obj.login, obj.az))



@implementer(IContent, IModelContainer)
class Addresses(SQLContainer):
    __label__ = _(u"Addresses")

    model = Address
    listing_attrs = uvclight.Fields(Address.__schema__).select(
        'oid', 'user_id', 'name1', 'name2', 'zip_code', 'city')

    def key_reverse(self, obj):
        return str(obj.oid)

    def key_converter(self, id):
        return int(id)


@implementer(IContent, IModelContainer)
class Vouchers(SQLContainer):
    __label__ = _(u"Vouchers")

    model = Voucher
    listing_attrs = uvclight.Fields(Voucher.__schema__).select(
        'oid', 'cat', 'status', 'user_id', 'displayData')

    def key_reverse(self, obj):
        return '%s' % obj.oid

    def key_converter(self, id):
        return int(id)


@implementer(IContent, IModelContainer)
class Invoices(SQLContainer):
    __label__ = u"Rechnungen"

    model = Invoice
    listing_attrs = uvclight.Fields(Invoice.__schema__).select(
        'oid', 'description', 'vouchers')

    def key_reverse(self, obj):
        return str(obj.oid)

    def key_converter(self, id):
        return int(id)


@implementer(IContent, IModelContainer)
class Categories(SQLContainer):
    __label__ = u"Kategorien"

    model = Category
    listing_attrs = uvclight.Fields(Category.__schema__).select(
        'oid', 'kat1', 'kat2', 'kat3', 'kat4', 'kat5', 'kat6', 'kat7')

    def key_reverse(self, obj):
        return str(obj.oid)

    def key_converter(self, id):
        return int(id)
