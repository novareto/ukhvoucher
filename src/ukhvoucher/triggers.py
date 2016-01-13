# -*- coding: utf-8 -*-

from .models import Voucher, Invoice
from sqlalchemy import event


def rel_modified(target, value, initiator):
    value.status = u'booked'
    return value


def rel_deleted(target, value, initiator):
    value.stauts = u"not booked"
    return value


event.listen(Invoice.vouchers, 'append', rel_modified, retval=True)
event.listen(Invoice.vouchers, 'remove', rel_deleted, retval=True)
