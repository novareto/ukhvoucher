# -*- coding: utf-8 -*-

import os
import uvclight
import datetime
import ConfigParser

from cromlech.sqlalchemy import get_session
from dolmen.sqlcontainer import SQLContainer as BaseSQLContainer
from sqlalchemy import *
from sqlalchemy import types
from sqlalchemy.orm import relationship, backref
from urllib import quote, unquote
from uvc.content.interfaces import IContent
from zope.interface import implementer
from zope.location import Location
from zope.location.interfaces import ILocation

from . import Base, _, resources
from .interfaces import (
    IJournalEntry, IVoucher, IInvoice, IAddress, IAccount, ICategory,
    IModel, IModelContainer, IIdentified, IVoucherSearch, IInvoiceSearch)


def get_ukh_config():
    path = os.environ.get('UKH_CONFIGURATION')
    if path is None or not os.path.isfile(path):
        raise RuntimeError('Configuration path is not found.')

    config = ConfigParser.ConfigParser()
    config.read([path])
    tablenames = dict(config.items('TABLENAMES'))
    return tablenames


TABLENAMES = get_ukh_config()

schema = TABLENAMES.get('schema', '')


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
        if value:
            return value.rstrip()
        return value

    def copy(self):
        "Make a copy of this type"
        return StrippedString(self.impl.length)


@implementer(IModel, IIdentified, IAddress)
class Address(Base, Location):
    __tablename__ = TABLENAMES['address']
    __schema__ = IAddress
    __label__ = _(u"Address")
    z1ext9aa = TABLENAMES['user']

    oid = Column('oid', Integer, primary_key=True, autoincrement=True)
    name1 = Column('iknam1', String(28))
    name2 = Column('iknam2', String(28))
    name3 = Column('iknam3', String(28))
    street = Column('ikstr', String(46))
    number = Column('ikhnr', String(10))
    mnr = Column('trgmnr', String(15))
    zip_code = Column('ikhplz', String(5))
    city = Column('ikhort', String(24))
    user_id = Column('user_id', Integer)
    user_az = Column('user_az', String)
    user_login = Column('user_login', String())
    #user_id = Column('user_id', Integer, ForeignKey(schema + 'Z1EXT9AA.oid'))
    __table_args__ = (
        ForeignKeyConstraint(
            [user_id, user_az, user_login],
            [schema + z1ext9aa + '.oid',
             schema + z1ext9aa + '.az', schema + z1ext9aa + '.login']),
        {})

    if schema:
        __table_args__ = (
            ForeignKeyConstraint(
                [user_id, user_az, user_login],
                [schema + z1ext9aa + '.oid',
                 schema + z1ext9aa + '.az', schema + z1ext9aa + '.login']),
                {"schema": schema[:-1]})

    @property
    def title(self):
        return "Adresse des Benutzers %s" % (self.oid)

    # search attributes
    search_attr = "name1"
    searchable_attrs = ("oid", "name1", "street", 'zip_code', 'city')

    #mnr = ""

    @staticmethod
    def widget_arrangements(fields):
        fields['oid'].readonly = True
        fields['mnr'].readonly = True
        fields['name1'].htmlAttributes = {'maxlength': 28}
        fields['name2'].htmlAttributes = {'maxlength': 28}
        fields['name3'].htmlAttributes = {'maxlength': 28}
        fields['street'].htmlAttributes = {'maxlength': 46}
        fields['number'].htmlAttributes = {'maxlength': 10}
        fields['zip_code'].htmlAttributes = {'maxlength': 5}
        fields['city'].htmlAttributes = {'maxlength': 24}


@implementer(IJournalEntry, IModel)
class JournalEntry(Base, Location):
    __schema__ = IJournalEntry
    __label__ = "Journal Entry"
    
    #__tablename__ = 'Z1EHRJRN_T'
    __tablename__ = TABLENAMES['journal']
    if schema:
        __table_args__ = {"schema": schema[:-1]}

    jid = Column('jrnoid', Integer, primary_key=True)
    date = Column('jrn_dat', DateTime)
    action = Column('aktion', String(20))
    userid = Column('user_id', String(30))
    note = Column('text', String(500))
    oid = Column('oid', Integer)

    @property
    def title(self):
        return "Journal entry %i" % self.jid

    # search attributes
    search_attr = "jid"
    searchable_attrs = ("jid",)

    @staticmethod
    def widget_arrangements(fields):
        fields['jid'].readonly = True

    
class FWBudget(Base):
    __tablename__ = TABLENAMES['budget']
    if schema:
        __table_args__ = {"schema": schema[:-1]}

    bgt_id = Column('bgt_id', Integer, primary_key=True)
    datum = Column('datum', DateTime)
    einsatzk = Column('einsatzk', Integer)
    jugendf = Column('jugendf', Integer)
    budget= Column('budget', Float)
    budget_vj= Column('budget_vj', Float)
    user_id = Column('user_id', String(30))


class FWKto(Base):
    __tablename__ = TABLENAMES['kto']
    if schema:
        __table_args__ = {"schema": schema[:-1]}

    user_id = Column('user_id', String(30), primary_key=True)
    bank = Column('bank', String(50))
    kto_inh = Column('kto_inh', String(50))
    iban = Column('iban', String(22))
    verw_zweck = Column('verw_zweck', String(30))


class AddressEinrichtung(Base):
    #__tablename__ = 'z1ext9ac'
    __tablename__ = TABLENAMES['adreinr']
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

    def as_dict(self):
        return dict(oid=str(self.oid), mnr=self.mnr, name1=self.name1,
            name2=self.name2, name3=self.name3, street=self.street,
            number=self.number, zip_code=str(self.zip_code), city=self.city
            )


class AddressTraeger(Base):
    #__tablename__ = 'z1ext9ab'
    __tablename__ = TABLENAMES['adrtrae']
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

    #__tablename__ = 'z1ehrkat_t'
    __tablename__ = TABLENAMES['category']
    __schema__ = ICategory
    __label__ = _(u"Kontingent")

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
    kat8 = Column('kat8', Boolean)
    kat9 = Column('kat9', Boolean)
    kat10 = Column('kat10', Boolean)
    kat11 = Column('kat11', Boolean)

    @property
    def title(self):
        return "Kontingent %s" % self.oid
    
    # search attributes
    search_attr = "oid"
    searchable_attrs = ("oid",)

    @staticmethod
    def widget_arrangements(fields):
        fields['oid'].readonly = True


@implementer(IModel, IIdentified, IAccount)
class Account(Base, Location):

    # __tablename__ = 'Z1EXT9AA'
    __tablename__ = TABLENAMES['user']
    __schema__ = IAccount
    __label__ = _(u"Account")
    if schema:
        __table_args__ = {"schema": schema[:-1]}

    model = Address
    oid = Column('oid', Integer, primary_key=True)
    email = Column('email', StrippedString)
    login = Column('login', String, primary_key=True)
    az = Column('az', String, primary_key=True)
    titel = Column('titel', StrippedString)
    funktion = Column('funktion', StrippedString)
    vname = Column('vname', StrippedString)
    nname = Column('nname', StrippedString)
    phone = Column('tlnr', StrippedString)
    vorwahl = Column('vwhl', StrippedString)
    anrede = Column('anr', StrippedString)
    rechte = Column('rechte', String)
    password = Column('passwort', String)
    merkmal = Column('merkmal', String)
    rollen = Column('rollen', String)

    @property
    def title(self):
        return "Benutzerkennung: %s, (OID der Einrichtung: %s)" % (
            self.login, self.oid)
    
    @property
    def categories(self):
        session = get_session('ukhvoucher')
        return session.query(Category).filter(Category.oid == self.oid).all()

    # search attributes
    search_attr = "oid"
    searchable_attrs = ("oid", "email", "name")

    @staticmethod
    def widget_arrangements(fields):
        fields['oid'].readonly = True
        fields['login'].readonly = True
        fields['az'].readonly = True
        fields['vname'].htmlAttributes = {'maxlength': 30}
        fields['nname'].htmlAttributes = {'maxlength': 30}
        fields['phone'].htmlAttributes = {'maxlength': 15}
        fields['email'].htmlAttributes = {'maxlength': 79}
        fields['vorwahl'].htmlAttributes = {'maxlength': 6}
        fields['titel'].htmlAttributes = {'maxlength': 15}
        fields['funktion'].htmlAttributes = {'maxlength': 50}
        fields['password'].htmlAttributes = {'maxlength': 8}


def date_factory():
    return datetime.datetime.now().strftime('%Y-%m-%d')


@implementer(IModel, IIdentified, IVoucher)
class Voucher(Base, Location):

    #__tablename__ = 'z1ehrvch_t'
    __tablename__ = TABLENAMES['voucher']
    __schema__ = IVoucher
    __label__ = _(u"Vouchers")
    z1ext9aa = TABLENAMES['user']
    z1ehrrch = TABLENAMES['invoice']
    z1ehrbgl = TABLENAMES['generation']

    if schema:
        __table_args__ = {"schema": schema[:-1]}

    oid = Column('vch_oid', Integer, primary_key=True)
    creation_date = Column('erst_dat', DateTime)
    modification_date = Column(
        'mod_dat', DateTime, default=date_factory, onupdate=date_factory)
    status = Column('status', String)
    cat = Column('kat', String)
    user_id = Column('user_id', Integer) #, ForeignKey(schema + z1ext9aa + '.oid'))
    user_az = Column('user_az', String)
    user_login = Column('user_login', String())
    invoice_id = Column(
        'rech_oid', Integer, ForeignKey(schema + z1ehrrch + '.rech_oid'))
    generation_id = Column(
        'gen_oid', Integer, ForeignKey(schema + z1ehrbgl + '.bgl_oid'))

    # relations
    user = relationship('Account')
    __table_args__ = (ForeignKeyConstraint(
        [user_id, user_az, user_login],
        [schema + z1ext9aa + '.oid',
         schema + z1ext9aa + '.az',
         schema + z1ext9aa + '.login']), {})

    if schema:
        __table_args__ = (ForeignKeyConstraint([user_id, user_az, user_login],
                                           [schema + z1ext9aa + '.oid', schema + z1ext9aa + '.az', schema + z1ext9aa + '.login']),
                                           {"schema": schema[:-1]})

    def getInvoice(self):
        from cromlech.sqlalchemy import get_session
        session = get_session('ukhvoucher')
        if self.invoice_id:
            return session.query(Invoice).get(int(self.invoice_id))
        return None

    @property
    def title(self):
        return "Berechtigungsschein %s" % self.oid
    
    # search attributes
    search_attr = "oid"
    searchable_attrs = ("oid", "status", 'user_id')

    @property
    def displayData(self):
        import json
        rc = []
        data = json.loads(self.generation.data)
        if isinstance(data, dict):
            for k, v in json.loads(self.generation.data).items():
                if k == 'mitarbeiter':
                    k = u'Beschäftigte'
                if k == 'standorte':
                    k = u'Standorte'
                if k == 'schulstandorte':
                    k = u'Schulstandorte'
                if k == 'kitas':
                    k = u'Kitas'
                if k == 'merkmal':
                    k = u'Merkmal'
                if k == 'kolonne':
                    k = u'Kolonnen'
                if k == 'gruppen':
                    k = u'Gruppen'
                if k == 'lehrkraefte':
                    k = u'Lehrkräfte'
                if k == 'einsatzkraefte':
                    k = u'Einsatzkräfte'
                if k == 'betreuer':
                    k = u'Betreuer'
                if k == 'ma_verwaltung':
                    k = u'Mitarbeiter-Verwaltung'
                if k == 'st_verwaltung':
                    k = u'Standorte-Verwaltung'
                if k == 'ma_technik':
                    k = u'Mitarbeiter-Technik'
                if k == 'st_technik':
                    k = u'Standorte-Technik'
                if k == 'bestaetigung':
                    k = u'Bestätigung Richtigkeit'
                if v is True:
                    v = u'Ja'
                if v is False:
                    v = u'Nein'
                rc.append("%s: %s" % (k, v))
            return '; '.join(rc)
        return data

    @property
    def displayKat(self):
        dat = ''
        if self.cat.strip() == 'K1':
            dat = u'K1 - Verwaltung'
        elif self.cat.strip() == 'K2':
            dat = u'K2 - Sonstige Betriebe'
        elif self.cat.strip() == 'K3':
            dat = u'K3 - Kitas'
        elif self.cat.strip() == 'K4':
            dat = u'K4 - Bauhof'
        elif self.cat.strip() == 'K5':
            dat = u'K5 - Erhöhte Gefährdung'
        elif self.cat.strip() == 'K6':
            dat = u'K6 - Besonders hohe Gefährdung'
        elif self.cat.strip() == 'K7':
            dat = u'K7 - Lehrkräfte'
        elif self.cat.strip() == 'K8':
            dat = u'K8 - Schulpersonal'
        elif self.cat.strip() == 'K9':
            dat = u'K9 - Schulbetreuung'
        elif self.cat.strip() == 'K10':
            dat = u'K10 - Freiwillige Feuerwehren'
        elif self.cat.strip() == 'K11':
            dat = u'K11 - Gesundheitsdienste'
        return dat

    def zeitraum(self):
        from ukhvoucher.vocabularies import get_default_abrechnungszeitraum
        d = self.creation_date
        return get_default_abrechnungszeitraum(datetime.datetime(d.year, d.month, d.day))


@implementer(IModel, IIdentified, IInvoice)
class Invoice(Base, Location):

    #__tablename__ = 'z1ehrrch_t'
    __tablename__ = TABLENAMES['invoice']
    __schema__ = IInvoice
    __label__ = _(u"Zuordnung")

    if schema:
        __table_args__ = {"schema": schema[:-1]}
    oid = Column('rech_oid', Integer, primary_key=True)
    reason = Column('grund', StrippedString)
    description = Column('text', StrippedString)
    creation_date = Column('erst_dat', DateTime, default=date_factory)

    vouchers = relationship(
        Voucher, collection_class=set,
        backref=backref('invoice', uselist=False))

    @property
    def title(self):
        return "Zuordnung %s" % self.oid
    
    search_attr = "oid"
    #search_attr = "field.oid"
    searchable_attrs = ("oid", "reason")

    @staticmethod
    def widget_arrangements(fields):
        fields['oid'].readonly = True


class Generation(Base):
    #__tablename__ = 'z1ehrbgl_t'
    __tablename__ = TABLENAMES['generation']
    z1ext9aa = TABLENAMES['user']

    oid = Column('bgl_oid', Integer, primary_key=True)
    date = Column('vcb_dat', DateTime)
    type = Column('kat', String(20))
    data = Column('text', String(500))
    user = Column('user_id', Integer)
    user_az = Column('user_az', String)
    user_login = Column('user_login', String())
    uoid = Column('oid', Integer)
    voucher = relationship("Voucher", backref=backref('generation'))

    __table_args__ = (ForeignKeyConstraint(
        [user, user_az, user_login],
        [schema + z1ext9aa + '.oid', schema + z1ext9aa + '.az',
         schema + z1ext9aa + '.login']), {})

    if schema:
        __table_args__ = (ForeignKeyConstraint(
            [user, user_az, user_login],
            [schema + z1ext9aa + '.oid',
             schema + z1ext9aa + '.az',
             schema + z1ext9aa + '.login']), {"schema": schema[:-1]})


@implementer(IContent, IModelContainer)
class SQLContainer(BaseSQLContainer):

    @property
    def pkey(self):
        raise NotImplementedError('Implement your own.')


class Accounts(SQLContainer):
    __label__ = _(u"Accounts")

    pkey = 'oid'
    model = Account
    listing_attrs = uvclight.Fields(Account.__schema__).select(
        'oid', 'login', 'email', 'name')

    def query_filters1(self, query):
        query = query.filter(self.model.az == "eh")
        return query

    def key_converter(self, id):
        keys = unquote(id)
        try:
            oid, login, az = keys.split(' ')
            return oid, login, az
        except ValueError:
            return None

    def key_reverse(self, obj):
        return quote('%s %s %s' % (obj.oid, obj.login, obj.az))


class Addresses(SQLContainer):
    __label__ = _(u"Addresses")

    pkey = 'oid'
    model = Address
    listing_attrs = uvclight.Fields(Address.__schema__).select(
        'oid', 'user_id', 'name1', 'name2', 'zip_code', 'city')

    def key_reverse(self, obj):
        return str(obj.oid)

    def key_converter(self, id):
        return int(id)


class Vouchers(SQLContainer):
    __label__ = _(u"Vouchers")

    pkey = 'oid'
    model = Voucher
    listing_attrs = uvclight.Fields(Voucher.__schema__).select(
        'oid', 'cat', 'status', 'user_id', 'displayData', 'displayKat')

    search_fields = uvclight.Fields(IVoucherSearch).omit('user_id', 'status')

    def key_reverse(self, obj):
        return str(obj.oid)

    def key_converter(self, id):
        return int(id)

#    def query_filters(self, query):
#        return query.order_by(self.model.oid.desc()).limit(100)


class Invoices(SQLContainer):
    __label__ = u"Zuordnungen"

    pkey = 'oid'
    model = Invoice
    listing_attrs = uvclight.Fields(Invoice.__schema__).select(
        'oid', 'description', 'vouchers')

    search_fields = uvclight.Fields(IInvoiceSearch)

    def key_reverse(self, obj):
        return str(obj.oid)

    def key_converter(self, id):
        return int(id)

    def query_filters(self, query):
        return query.order_by(self.model.oid.desc()).limit(100)


class Categories(SQLContainer):
    __label__ = u"Kontingentkategorien"

    pkey = 'oid'
    model = Category
    listing_attrs = uvclight.Fields(Category.__schema__).select(
        'oid', 'kat1', 'kat2', 'kat3', 'kat4', 'kat5',
        'kat6', 'kat7', 'kat8', 'kat9', 'kat10', 'kat11')

    def key_reverse(self, obj):
        return str(obj.oid)

    def key_converter(self, id):
        return int(id)


class Journal(SQLContainer):
    __label__ = u"Journal"

    pkey = 'jid'
    model = JournalEntry
    listing_attrs = uvclight.Fields(JournalEntry.__schema__).select(
        'jid', 'date', 'userid')

    search_fields = uvclight.Fields(IJournalEntry)
    
    def key_reverse(self, obj):
        return str(obj.jid)

    def key_converter(self, id):
        return int(id)
