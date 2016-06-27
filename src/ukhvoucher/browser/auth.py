# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de


import uvclight
import urllib

from base64 import decodestring
from ul.auth import require
from zope.component import getUtility
from ul.auth.browser import ICredentials
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP


fp = open('/etc/ukh_private.pem', 'r')
private_key = RSA.importKey(fp.read(), passphrase='ukhukh')
private_key_ = PKCS1_OAEP.new(private_key)


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

    def render(self):
        snummer = self.request.params.get('snummer', 0)
        if snummer:
            return private_key_.decrypt(urllib.unquote_plus(snummer))
        return {'snummer': snummer}
