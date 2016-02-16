# -*- coding: utf-8 -*-

import uvclight
from ukhvoucher import _
from uvc.design.canvas import IAboveContent
from cromlech.browser import getSession
from zope.schema import Choice
from zope.interface import Interface
from ukhvoucher.browser.views import AdminRootIndex
from ..interfaces import IAdminLayer, get_oid
from profilehooks import profile
from plone.memoize import forever
from plone.memoize import ram
from time import time


class IAccounts(Interface):

    oid = Choice(
        title=_(u"Member to inspect"),
        required=True,
        source=get_oid,
    )


class UserMasquarade(uvclight.ViewletForm):
    uvclight.viewletmanager(IAboveContent)
    uvclight.context(Interface)
    uvclight.view(AdminRootIndex)
    uvclight.layer(IAdminLayer)
    uvclight.auth.require('manage.vouchers')
    uvclight.order(20)
    template = uvclight.get_template('selectunternehmen.cpt', __file__)

    fields = uvclight.Fields(IAccounts)
    ignoreContent = False

    def __init__(self, *args):
        uvclight.ViewletForm.__init__(self, *args)
        self.setContentData(self.request.principal)

    @property
    def action_url(self):
        return self.view.application_url()

    @uvclight.action(u'Mitglied auswählen', identifier="masq")
    def handle_masquarade(self):
        data, errors = self.extractData()
        if errors:
            return

        session = getSession()
        session['masquarade'] = data['oid']
        self.view.redirect(self.request.path)

    #@ram.cache(lambda *args: time() // (60 * 60))
    def render(self):
        print "I AM CALLED"
        form = uvclight.ViewletForm.render(self)
        return form

