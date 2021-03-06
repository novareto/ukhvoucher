# -*- coding: utf-8 -*-

import uvclight
import json
from ..models import Voucher, Vouchers, Invoice, Address
from .. import models
from ..interfaces import IAccount, IAdminLayer, IUserLayer
from .forms import ModelIndex, CreateModel
from dolmen.menu import menu
from ukhtheme.uvclight.viewlets import BelowContent, FlashMessages
from uvc.entities.browser.menus import IPersonalMenu, INavigationMenu
from zope.interface import Interface
from cromlech.browser import getSession
from cromlech.sqlalchemy import get_session


class Sound(uvclight.Viewlet):
    uvclight.context(Interface)
    uvclight.view(CreateModel)
    uvclight.viewletmanager(BelowContent)

    def render(self):
	return """
	  <audio id="success" preload='auto' src='/fanstatic/ukhvoucher/success.wav'>
	    <b>Your browser does not support the audio tag.</b>
	  </audio>
          <audio id="failure" preload='auto' src='/fanstatic/ukhvoucher/failure.wav'>
            <b>Your browser does not support the audio tag.</b>
          </audio>
	"""

class EditSound(uvclight.Viewlet):
    uvclight.context(Interface)
    uvclight.viewletmanager(BelowContent)

    def render(self):
	return """
	  <audio id="success" preload='auto' src='/fanstatic/ukhvoucher/success.wav'>
	    <b>Your browser does not support the audio tag.</b>
	  </audio>
          <audio id="failure" preload='auto' src='/fanstatic/ukhvoucher/failure.wav'>
            <b>Your browser does not support the audio tag.</b>
          </audio>
	"""

class EditSoundV(uvclight.Viewlet):
    uvclight.context(Invoice)
    uvclight.viewletmanager(BelowContent)

    def render(self):
	return """
	  <audio id="success" preload='auto' src='/fanstatic/ukhvoucher/success.wav'>
	    <b>Your browser does not support the audio tag.</b>
	  </audio>
          <audio id="failure" preload='auto' src='/fanstatic/ukhvoucher/failure.wav'>
            <b>Your browser does not support the audio tag.</b>
          </audio>
	"""


class Categories(uvclight.Viewlet):
    uvclight.context(IAccount)
    uvclight.view(ModelIndex)
    uvclight.viewletmanager(BelowContent)

    def render(self):
        values = []
        categories = self.context.categories
        for category in categories:
            values += [(kid, getattr(category, kid))
                       for kid in ('kat1', 'kat2', 'kat3', 'kat4', 'kat5', 'kat6', 'kat7', 'kat8', 'kat9', 'kat10', 'kat11', 'kat13')]
        if not values:
            return u"Keine Kontingente"
        return "Zugeordnete Kontingente: %s" % ', '.join(
            (kat[0] for kat in values if kat[1]))

from ukhvoucher.components import _render_details_cachekey
from plone.memoize import ram

class VoucherGeneration(uvclight.Viewlet):
    uvclight.context(Voucher)
    uvclight.view(ModelIndex)
    uvclight.viewletmanager(BelowContent)

    template = uvclight.get_template('generation.cpt', __file__)

    def getAddress(self):
        session = get_session('ukhvoucher')
        oid = str(self.context.user.oid)
        address = session.query(models.Address).get(oid)
        if address:
            return address
        @ram.cache(_render_details_cachekey)
        def getSlowAdr(oid):
            address = session.query(models.AddressTraeger).get(oid)
            if address:
                return address
            address = session.query(models.AddressEinrichtung).get(oid)
            if address:
                return address
        return getSlowAdr(oid)

    def update(self):
        if self.context.generation is not None:
            #self.data = json.loads(self.context.generation.data)
            rc = ""
            data = json.loads(self.context.generation.data)

            if isinstance(data, dict):
                z = 0
                for k, v in json.loads(self.context.generation.data).items():
                    if k == 'mitarbeiter':
                        k = u'Beschäftigte'
                    if k == 'standorte':
                        k = u'Standorte'
                    if k == 'schulstandorte':
                        k = u'Schulstandorte'
                    if k == 'kitas':
                        k = u'Kitas'
                    if k == 'merkmal':
                        k = u'Merkmal'
                    if k == 'kolonne':
                        k = u'Kolonnen'
                    if k == 'gruppen':
                        k = u'Gruppen'
                    if k == 'lehrkraefte':
                        k = u'Lehrkräfte'
                    if k == 'einsatzkraefte':
                        k = u'Einsatzkräfte'
                    if k == 'betreuer':
                        k = u'Betreuer'
                    if k == 'bestaetigung':
                        k = u'Bestätigung Richtigkeit'
                    if v is True:
                        v = u'Ja'
                    if v is False:
                        v = u'Nein'
                    if z is 0:
                        rc = rc + ("%s: %s" % (k, v))
                    if z > 0:
                        rc = rc + " und " + ("%s: %s" % (k, v))
                    z = z + 1
                data = rc
            self.data = data
        else:
            self.data = None


class Username(uvclight.MenuItem):
    uvclight.context(Interface)
    uvclight.menu(IPersonalMenu)
    id = "username"
    action = ""
    submenu = None

    @property
    def title(self):
        try:
            if self.request.principal.title == "Unauthenticated principal":
                return u"Bitte anmelden"
            return u"Sie sind angemeldet als: %s" % self.request.principal.title
            #return u"Herzlich willkommen im Mitgliederportal der Unfallkasse Hessen. Sie sind angemeldet als: %s" % self.request.principal.title
        except:
            return "HHH"


class BaseNavMenu(uvclight.MenuItem):
    uvclight.context(Interface)
    uvclight.menu(INavigationMenu)
    uvclight.layer(IAdminLayer)
    uvclight.auth.require('manage.vouchers')
    uvclight.baseclass()

    attribute = ""
    title = "Startseite"

    @property
    def url(self):
        return "%s/%s" % (self.view.application_url(), self.attribute)

    @property
    def action(self):
        return self.url

    @property
    def selected(self):
        return self.request.url.startswith(self.url)


class Startseite(BaseNavMenu):
    uvclight.order(1)
    attribute = "/"
    title = "Startseite"


class MenuInvoice(BaseNavMenu):
    uvclight.order(2)
    attribute = "invoices"
    title = u"Übersicht Zuordnungen"


class MenuVoucher(BaseNavMenu):
    uvclight.order(3)
    attribute = "vouchers"
    title = u"Übersicht Berechtigungsscheine"


#class MenuAccounts(BaseNavMenu):
#    uvclight.order(3)
#    attribute = "accounts"
#    title = "Benutzer"


#class MenuAddresses(BaseNavMenu):
#    uvclight.order(3)
#    attribute = "addresses"
#    title = "Adressen"


#class MenuStat(BaseNavMenu):
#    uvclight.order(5)
#    attribute = "statistik"
#    title = "Statistik"


class MenuStatNew(BaseNavMenu):
    uvclight.order(5)
    attribute = "statistiksuperneu"
    title = "Statistik"


class Journal(BaseNavMenu):
    uvclight.order(6)
    attribute = "journal"
    title = u"Historie"


class LogoutMenu(uvclight.MenuItem):
    uvclight.context(Interface)
    menu(IPersonalMenu)
    uvclight.title(u'Logout')
    id = "lmi"
    submenu = None

    @property
    def action(self):
        return self.view.application_url() + '/logout1'


class Stammdaten(uvclight.MenuItem):
    uvclight.context(Interface)
    menu(IPersonalMenu)
    uvclight.title(u'Stammdaten')
    uvclight.layer(IUserLayer)
    id = "smi"
    submenu = None

    @property
    def action(self):
        return self.view.application_url() + '/edit_account'


class PW(uvclight.MenuItem):
    uvclight.context(Interface)
    menu(IPersonalMenu)
    uvclight.layer(IUserLayer)
    uvclight.title(u'Passwort ändern')
    #uvclight.auth.require('zope.View')
    id = "smi"
    submenu = None

    @property
    def available(self):
        principal = self.request.principal
        from ukhvoucher.apps import USERS
        if principal.id not in USERS.keys():
            mnr = principal.getAddress().mnr
            if mnr.startswith('3.2.') or mnr.startswith('3.3.'):
                return False
        return True

    @property
    def action(self):
        return self.view.application_url() + '/change_pw'


class Kontakt(uvclight.MenuItem):
    uvclight.context(Interface)
    menu(IPersonalMenu)
    uvclight.layer(IUserLayer)
    uvclight.title(u'Kontakt')
    uvclight.order(30)
    id = "kmi"
    submenu = None

    @property
    def action(self):
        return self.view.application_url() + '/kontakt'

class Home(uvclight.MenuItem):
    uvclight.context(Interface)
    menu(IPersonalMenu)
    uvclight.layer(IUserLayer)
    uvclight.title(u'Startseite')
    uvclight.order(40)
    id = "home"
    submenu = None

    @property
    def action(self):
        return self.view.application_url()


class Logout(uvclight.View):
    uvclight.context(uvclight.IRootObject)
    uvclight.name('logout1')
    uvclight.auth.require('zope.Public')

    def make_response(self, result, *args, **kwargs):
        response = super(Logout, self).make_response(result, *args, **kwargs)
        url = self.application_url()
        response.url = url
        response.location = url
        response.status_int = 302
        response.delete_cookie('auth_pubtkt', path='/', domain='ukh.de')
        response.delete_cookie('ukh.eh', path='/', domain='ukh.de')
        response.delete_cookie('dolmen.authcookie', path='/', domain='ukh.de')
        return response

    def update(self):
        session = getSession()
        if session:
            if 'username' in session:
                del session['username']
            if 'masquarde' in session:
                del session['masquarade']

    def render(self):
        return u"LOGOUT"
        return self.redirect(self.application_url())


from ul.browser.components import DisplayMenuItem


class DisplayMenuItem(DisplayMenuItem):
    available = False

from uvc.entities.browser import IContextualActionsMenu, IDocumentActions
from ukhvoucher.interfaces import IInvoice, IAccount


class InvoiceEditEntry(uvclight.MenuItem):
    uvclight.context(IInvoice)
    uvclight.menu(IDocumentActions)
    uvclight.title(u'Bearbeiten')
    uvclight.name('edit')

    action="edit"


from ukhvoucher.browser.forms import ModelIndex

class AccountEditEntry(uvclight.MenuItem):
    uvclight.context(IAccount)
    uvclight.view(ModelIndex)
    uvclight.menu(IDocumentActions)
    uvclight.title(u'Bearbeiten')
    uvclight.name('edit')

    action="edit"


class FlashMessages(FlashMessages):
    template = uvclight.get_template('flash.cpt', __file__)
