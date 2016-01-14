# # -*- coding: utf-8 -*-

# import datetime
# from . import Base
# from .models import Voucher
# from .interfaces import IKG1, IKG2, IKG3
# from sqlalchemy import *
# from zope.interface import implementer
# from sqlalchemy.orm import relationship, backref


# @implementer(IKG1, IKG2, IKG3)
# class VoucherGeneration(Base):

#     __tablename__ = 'generations'

#     oid = Column('oid', Integer, primary_key=True, autoincrement=True)
#     date = Column('date', DateTime)
#     account = Column('account', String, ForeignKey('accounts.oid'))
#     type = Column('type', String)
#     mitarbeiter = Column('mitarbeiter', Integer)
#     standorte = Column('standorte', Integer)

#     # relationships
#     user = relationship('Account')
#     vouchers = relationship('Voucher')

#     @classmethod
#     def generate(cls, principal, iface):
#         now = datetime.datetime.now()
#         for i in range(amount):
#             voucher = Voucher(
#                 creation_date=now,
#                 status="created",
#                 cat=form._iface.getName(),
#                 user_id=principal.id)
#         generation = cls(date=now, account=principal.id)
