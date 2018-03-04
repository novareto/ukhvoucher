# -*- coding: utf-8 -*-

import uvclight
from ukhvoucher.apps import UserRoot
from ukhvoucher.components import ExternalPrincipal
from .views import UserRootIndexBase


class ExternalAPI(UserRootIndexBase, uvclight.View):
    uvclight.context(UserRoot)
    uvclight.name('external')
    uvclight.auth.require('zope.Public')

    def get_principal(self):
        return self.request.principal
        #return ExternalPrincipal('32279')

