# -*- coding: utf-8 -*-

from sqlalchemy import event
from .models import Voucher, Invoice
from ukhvoucher import BOOKED, NOT_BOOKED


def rel_modified(target, value, initiator):
    value.status = BOOKED
    return value


def rel_deleted(target, value, initiator):
    value.stauts = NOT_BOOKED
    return value


event.listen(Invoice.vouchers, 'append', rel_modified, retval=True)
event.listen(Invoice.vouchers, 'remove', rel_deleted, retval=True)
