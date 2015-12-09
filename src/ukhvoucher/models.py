# -*- coding: utf-8 -*-

from . import Base
from .interfaces import IVoucher, IInvoice, IAddress, IAccount, ICategory
from .interfaces import IModel, IModelContainer, IIdentified
from . import _

import uvclight
from cromlech.sqlalchemy import get_session
from dolmen.sqlcontainer import SQLContainer
from sqlalchemy import *
from sqlalchemy.orm import relationship, backref
from uvc.content.interfaces import IContent
from zope.interface import implementer
from zope.location import Location


@implementer(IModel, IIdentified, IAddress)
class Address(Base, Location):

    __tablename__ = 'addresses'
    __schema__ = IAddress
    __label__ = _(u"Address")

    oid = Column('oid', Integer, primary_key=True, autoincrement=True)
    name1 = Column('name1', String)
    name2 = Column('name2', String)
    name3 = Column('name3', String)
    street = Column('street', String)
    number = Column('number', String)
    zip_code = Column('zip', String)
    city = Column('city', String)
    user_id = Column('user_id', String, ForeignKey('accounts.oid'))

    @property
    def title(self):
        return "Address %s for user %s" % (self.oid, self.user_id)

    # search attributes
    search_attr = "name1"
    searchable_attrs = ("oid", "name1", "street", 'zip_code', 'city')


@implementer(IModel, IIdentified, ICategory)
class Category(Base, Location):

    __tablename__ = 'categories'
    __schema__ = ICategory
    __label__ = _(u"Category")

    oid = Column('oid', String, primary_key=True)
    kat1 = Column('kat1', Boolean)
    kat2 = Column('kat2', Boolean)
    kat3 = Column('kat3', Boolean)
    kat4 = Column('kat4', Boolean)
    kat5 = Column('kat5', Boolean)

    @property
    def title(self):
        return "Category %s" % self.oid

    # search attributes
    search_attr = "oid"
    searchable_attrs = ("oid",)


@implementer(IModel, IIdentified, IAccount)
class Account(Base, Location):

    __tablename__ = 'accounts'
    __schema__ = IAccount
    __label__ = _(u"Account")
    model = Address

    oid = Column('oid', String, primary_key=True)
    email = Column('email', String)
    name = Column('name', String)
    phone = Column('phone', String)
    password = Column('password', String)

    @property
    def title(self):
        return "%s (%s)" % (self.email, self.oid)

    @property
    def categories(self):
        session = get_session('ukhvoucher')
        return session.query(Category).filter(Category.oid == self.oid).all()

    # search attributes
    search_attr = "email"
    searchable_attrs = ("oid", "email", "name")


@implementer(IModel, IIdentified, IVoucher)
class Voucher(Base, Location):

    __tablename__ = 'vouchers'
    __schema__ = IVoucher
    __label__ = _(u"Vouchers")

    oid = Column('oid', Integer, primary_key=True)
    creation_date = Column('creation_date', DateTime)
    status = Column('status', String)
    cat = Column('cat', String)
    user_id = Column('user_id', String, ForeignKey('accounts.oid'))
    invoice_id = Column('invoice_id', ForeignKey('invoices.oid'))

    # relations
    user = relationship('Account')
    invoice = relationship(
        'Invoice', backref=backref('vouchers', collection_class=set))

    @property
    def title(self):
        return "Gutschein %s" % self.oid

    # search attributes
    search_attr = "oid"
    searchable_attrs = ("oid", "status", "user_id")


@implementer(IModel, IIdentified, IInvoice)
class Invoice(Base, Location):

    __tablename__ = 'invoices'
    __schema__ = IInvoice
    __label__ = _(u"Invoice")

    oid = Column('oid', String, primary_key=True)
    description = Column('description', String)

    @property
    def title(self):
        return "Invoice %s" % self.oid

    search_attr = "oid"
    searchable_attrs = ("oid", "description")


@implementer(IContent, IModelContainer)
class Accounts(SQLContainer):
    __label__ = _(u"Accounts")

    model = Account
    listing_attrs = uvclight.Fields(Account.__schema__).select(
        'oid', 'email', 'name')

    def key_reverse(self, obj):
        return str(obj.oid)


@implementer(IContent, IModelContainer)
class Addresses(SQLContainer):
    __label__ = _(u"Addresses")

    model = Address
    listing_attrs = uvclight.Fields(Address.__schema__).select(
        'oid', 'user_id', 'name1', 'name2', 'zip_code', 'city')

    def key_reverse(self, obj):
        return str(obj.oid)


@implementer(IContent, IModelContainer)
class Vouchers(SQLContainer):
    __label__ = _(u"Vouchers")

    model = Voucher
    listing_attrs = uvclight.Fields(Voucher.__schema__).select(
        'oid', 'cat', 'status', 'user_id')

    def key_reverse(self, obj):
        return 'Voucher %s' % obj.oid


@implementer(IContent, IModelContainer)
class Invoices(SQLContainer):
    __label__ = u"Invoices"

    model = Invoice
    listing_attrs = uvclight.Fields(Invoice.__schema__).select(
        'oid', 'description', 'vouchers')

    def key_reverse(self, obj):
        return str(obj.oid)


@implementer(IContent, IModelContainer)
class Categories(SQLContainer):
    __label__ = u"Categories"

    model = Category
    listing_attrs = uvclight.Fields(Category.__schema__).select(
        'oid', 'kat1', 'kat2', 'kat3', 'kat4', 'kat5')

    def key_reverse(self, obj):
        return str(obj.oid)
