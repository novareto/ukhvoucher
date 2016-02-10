# -*- coding: utf-8 -*-

import uvclight
from ukhvoucher import _
from uvc.design.canvas import IAboveContent
from cromlech.browser import getSession
from zope.schema import Choice
from zope.interface import Interface
from ..interfaces import get_oid


class IAccounts(Interface):

    oid = Choice(
        title=_(u"Member to inspect"),
        required=True,
        source=get_oid,
    )


class UserMasquarade(uvclight.ViewletForm):
    uvclight.viewletmanager(IAboveContent)
    uvclight.context(Interface)
    uvclight.auth.require('manage.vouchers')
    uvclight.order(20)

    fields = uvclight.Fields(IAccounts)
    ignoreContent = False

    @property
    def action_url(self):
        return self.view.application_url()

    @uvclight.action(u'Select user', identifier="masq")
    def handle_masquarade(self):
        data, errors = self.extractData()
        if errors:
            return

        session = getSession()
        session['masquarade'] = data['oid']
        self.view.redirect(self.request.path)

    def render(self):
        oid = self.request.principal.masquarade
        form = uvclight.ViewletForm.render(self)
        if oid is not None:
            masquarade = u"<p>Currently inspecting user %r</p>" % oid
            return masquarade + form
        return form
        
