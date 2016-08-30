# -*- coding: utf-8 -*-

from grokcore.security import name, Permission


class ManageVouchers(Permission):
    name('manage.vouchers')


class DisplayVouchers(Permission):
    name('display.vouchers')


class UserAccess(Permission):
    name('users.access')
