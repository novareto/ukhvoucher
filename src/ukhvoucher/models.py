# -*- coding: utf-8 -*-

from . import Base
from .interfaces import IVoucher, IInvoice, IAddress, IAccount, ICategory
from .interfaces import IModel, IModelContainer, IIdentified

import uvclight
from cromlech.sqlalchemy import get_session
from dolmen.sqlcontainer import SQLContainer
from sqlalchemy import *
from sqlalchemy.orm import relation, backref, relationship
from uvc.content.interfaces import IContent
from zope.interface import implementer
from zope.location import Location


@implementer(IModel, IIdentified, IAddress)
class Address(Base, Location):

    __tablename__ = 'addresses'
    __schema__ = IAddress
    __label__ = u"Address"
    
    # complete me
    oid = Column('oid', Integer, primary_key=True, autoincrement=True)
    address = Column('name', String)
    user_id = Column('user_id', String, ForeignKey('accounts.oid'))

    @property
    def title(self):
        return "Address %s for user %s" % (self.oid, self.user_id)
    

@implementer(IModel, IIdentified, ICategory)
class Category(Base, Location):

    __tablename__ = 'categories'
    __schema__ = ICategory
    __label__ = u"Category"

    oid = Column('oid', String, primary_key=True)
    kat1 = Column('kat1', Boolean)
    kat2 = Column('kat2', Boolean)
    kat3 = Column('kat3', Boolean)
    kat4 = Column('kat4', Boolean)
    kat5 = Column('kat5', Boolean)

    @property
    def title(self):
        return "Category %s" % self.oid

    
@implementer(IModel, IIdentified, IAccount)
class Account(Base, Location):

    __tablename__ = 'accounts'
    __schema__ = IAccount
    __label__ = u"Account"
    model = Address

    oid = Column('oid', String, primary_key=True)
    email = Column('email', String)
    name = Column('name', String)
    password = Column('password', String)

    @property
    def title(self):
        return "%s (%s)" % (self.email, self.oid)

    @property
    def categories(self):
        session = get_session('ukhvoucher')
        return session.query(Category).filter(Category.oid == self.oid).all()


@implementer(IModel, IIdentified, IVoucher)
class Voucher(Base, Location):

    __tablename__ = 'vouchers'
    __schema__ = IVoucher
    __label__ = u"Voucher"

    oid = Column('oid', String, primary_key=True)
    creation_date = Column('creation_date', DateTime)
    status = Column('status', String)
    user_id = Column('user_id', String, ForeignKey('accounts.oid'))
    invoice_id = Column('invoice_id', ForeignKey('invoices.oid'))

    # relations
    user = relationship('Account')
    invoice = relationship('Invoice', backref='vouchers')

    @property
    def title(self):
        return "Voucher %s for user %s" % (self.oid, self.user_id)

    
@implementer(IModel, IIdentified, IInvoice)
class Invoice(Base, Location):

    __tablename__ = 'invoices'
    __schema__ = IInvoice
    __label__ = u"Invoice"

    oid = Column('oid', String, primary_key=True)

    @property
    def title(self):
        return "Invoice %s" % self.oid
    
    
@implementer(IContent, IModelContainer)
class Accounts(SQLContainer):
    __label__ = u"Accounts"

    model = Account
    listing_attrs = uvclight.Fields(Account.__schema__).select(
        'oid', 'email', 'name')

    def key_reverse(self, obj):
        return str(obj.oid)
    

@implementer(IContent, IModelContainer)
class Addresses(SQLContainer):
    __label__ = u"Addresses"

    model = Address
    listing_attrs = uvclight.Fields(Address.__schema__).select(
        'oid', 'user_id')

    def key_reverse(self, obj):
        return str(obj.oid)


@implementer(IContent, IModelContainer)
class Vouchers(SQLContainer):
    __label__ = u"Vouchers"

    model = Voucher
    listing_attrs = uvclight.Fields(Voucher.__schema__).select(
        'oid', 'status', 'user_id')

    def key_reverse(self, obj):
        return str(obj.oid)


@implementer(IContent, IModelContainer)
class Invoices(SQLContainer):
    __label__ = u"Invoices"

    model = Invoice
    listing_attrs = uvclight.Fields(Invoice.__schema__).select(
        'oid')
    
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
