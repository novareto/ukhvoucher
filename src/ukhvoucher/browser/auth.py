# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de


import uvclight

from ul.auth import require
from zope.component import getUtility
from ul.auth.browser import ICredentials


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
