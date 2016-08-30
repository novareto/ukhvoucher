# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de


import uvclight
import urllib

from ukhvoucher.models import Account
from base64 import decodestring
from ul.auth import require
from zope.component import getUtility
from ul.auth.browser import ICredentials
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
from Crypto import Random
from Crypto.Cipher import PKCS1_v1_5


with open('/etc/ukhprie.pem', 'r') as fp:
    pk = RSA.importKey(fp.read(), passphrase='Test123')


def v1_5(txt, pk):
    sentinel = Random.new().read(256)
    cipher = PKCS1_v1_5.new(pk)
    return cipher.decrypt(txt, sentinel)


class CheckAuth(uvclight.JSON):
    uvclight.context(uvclight.IRootObject)
    require('zope.Public')

    def render(self):
        if self.request.params.get('username') != 'admin':
            util = getUtility(ICredentials, 'users')
            account = util.log_in(
                self.request,
                self.request.params.get('username'),
                self.request.params.get('password')
            )
            if account:
                return {'auth': 1}
        return {'auth': 0}


class GetSchool(uvclight.JSON):
    uvclight.context(uvclight.IRootObject)
    require('zope.Public')

    def getIKNummer(self, mnr):
        from cromlech.sqlalchemy import get_session
        session = get_session('ukhvoucher')
        sql = """SELECT ENRRCD
                 FROM EDUCUSADAT.MIENR1AA
                 WHERE ENREA1 = '3'
                 AND ENRLFD = %s""" % mnr
        res = session.execute(sql).fetchone()
        print res
        if res:
            accounts = session.query(Account).filter(Account.oid == int(res[0])).all()
            print accounts
        if accounts:
            return accounts[0].login
        return "NOTHING FOuND"

    def render(self):
        snummer = self.request.params.get('snummer', 0)
        if snummer:
            sn = v1_5(urllib.unquote_plus(snummer.encode('utf-8')), pk)
            snummer = self.getIKNummer(sn)
        return {'snummer': snummer}
