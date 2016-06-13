# -*- coding: utf-8 -*-

import uvclight
import json
from ..models import Voucher
from ..interfaces import IAccount, IAdminLayer
from .forms import ModelIndex, CreateModel
from dolmen.menu import menu
from ukhtheme.uvclight.viewlets import BelowContent
from uvc.entities.browser.menus import IPersonalMenu, INavigationMenu
from zope.interface import Interface
from cromlech.browser import getSession


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

class Categories(uvclight.Viewlet):
    uvclight.context(IAccount)
    uvclight.view(ModelIndex)
    uvclight.viewletmanager(BelowContent)

    def render(self):
        values = []
        categories = self.context.categories
        for category in categories:
            values += [(kid, getattr(category, kid))
                       for kid in ('kat1', 'kat2', 'kat3', 'kat4', 'kat5')]
        if not values:
            return u"Keine Kategorien"
        return "Categories: %s" % ', '.join(
            (kat[0] for kat in values if kat[1]))


class VoucherGeneration(uvclight.Viewlet):
    uvclight.context(Voucher)
    uvclight.view(ModelIndex)
    uvclight.viewletmanager(BelowContent)

    template = uvclight.get_template('generation.cpt', __file__)

    def update(self):
        if self.context.generation is not None:
            #self.data = json.loads(self.context.generation.data)
            rc = ""
            data = json.loads(self.context.generation.data)

            if isinstance(data, dict):
                z = 0
                for k, v in json.loads(self.context.generation.data).items():
                    #print "###",k,"###"
                    if k == 'mitarbeiter':
                        k = u'Beschäftigte'
                    if k == 'standorte':
                        k = u'Standorte'
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
        except:
            return "HHH"

    def render(self):
        import pdb; pdb.set_trace()


class BaseNavMenu(uvclight.MenuItem):
    uvclight.context(Interface)
    uvclight.menu(INavigationMenu)
    uvclight.layer(IAdminLayer)
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


#class MenuAccounts(BaseNavMenu):
#    uvclight.order(3)
#    attribute = "accounts"
#    title = "Benutzer"


#class MenuAddresses(BaseNavMenu):
#    uvclight.order(3)
#    attribute = "addresses"
#    title = "Adressen"


#class MenuKategorien(BaseNavMenu):
#    uvclight.order(4)
#    attribute = "categories"
#    title = "Kategorien"


class MenuStat(BaseNavMenu):
    uvclight.order(5)
    attribute = "statistik"
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
        response.delete_cookie('auth_pubtkt', path='/', domain='kuvb.de')
        return response

    def update(self):
        session = getSession()
        if session:
            if 'username' in session:
                del session['username']
            if 'masquarde' in session:
                del session['masquarade']

    def render(self):
        return self.redirect(self.application_url())


from ul.browser.components import DisplayMenuItem


class DisplayMenuItem(DisplayMenuItem):
    available = False
