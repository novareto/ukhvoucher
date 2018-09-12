# -*- coding: utf-8 -*-

import uvclight
from ukhvoucher import _
from uvc.design.canvas import IAboveContent
from cromlech.browser import getSession
from zope.schema import Choice
from zope.interface import Interface
from ukhvoucher.browser.views import AdminRootIndex
from ukhvoucher.vocabularies import VOCABULARIES
from ..interfaces import IAdminLayer, get_oid
from profilehooks import profile
from plone.memoize import forever
from plone.memoize import ram
from time import time
from uvc.entities.browser.menus import IPersonalMenu
from ukhtheme.uvclight.viewlets import Navigation
from dolmen.forms.base.datamanagers import DictDataManager


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
    uvclight.auth.require('display.vouchers')
    uvclight.order(20)
    template = uvclight.get_template('ajax_selectunternehmen.cpt', __file__)

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
        form = uvclight.ViewletForm.render(self)
        return form


class IDateRange(Interface):
    """ Date Range Select"""

    date_range = Choice(
        title=u"Abrechungszeitraun auswählen",
        source = VOCABULARIES['abrechnungszeitraum'](None) 
        )


class TimeRanngeSelect(uvclight.ViewletForm):
    uvclight.viewletmanager(Navigation)
    uvclight.layer(IAdminLayer)
    uvclight.auth.require('display.vouchers')
    uvclight.context(Interface)
    uvclight.order(59)
    template = uvclight.get_template('timerangeselect.cpt', __file__)
    fields = uvclight.Fields(IDateRange)
    ignoreContent = False
    dataManager = DictDataManager

    def __init__(self, *args):
        uvclight.ViewletForm.__init__(self, *args)
        session = getSession()
        self.setContentData(session)

    @property
    def action_url(self):
        return self.view.application_url()

    @uvclight.action(u'Abrechnungszeitraum wählen', identifier="cdr")
    def handle_date_range(self):
        data, errors = self.extractData()
        if errors:
            return
        session = getSession()
        session['date_range'] = data['date_range']
        self.view.flash(u'Der Abrechungszeitraum wurde gesetzt!')
        self.view.redirect(self.request.path)

    def render(self):
        form = uvclight.ViewletForm.render(self)
        return form
