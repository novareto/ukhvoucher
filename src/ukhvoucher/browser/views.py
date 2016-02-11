# -*- coding: utf-8 -*-

import uvclight
from webhelpers.html.builder import HTML
from ukhvoucher import models
from ..apps import AdminRoot, UserRoot
from ..interfaces import IAdminLayer, IUserLayer
from ..interfaces import IModelContainer
from ..models import JournalEntry
from ..resources import ukhcss
from ..resources import ukhvouchers
from .batch import get_dichotomy_batches
from cromlech.sqlalchemy import get_session
from dolmen.batch import Batcher
from sqlalchemy import inspect
from ul.auth import require
from zope.component import getMultiAdapter
from zope.component.hooks import getSite
from zope.i18n import translate
from zope.interface import Interface


class UserRootIndex(uvclight.Page):
    uvclight.name('index')
    uvclight.layer(IUserLayer)
    uvclight.context(UserRoot)
    require('users.access')

    template = uvclight.get_template('userroot.cpt', __file__)

    def update(self):
        self.categories = self._categories
        account = self.request.principal.getAccount()
        if account:
            if (account.phone.strip() == "" or
                account.nname.strip() == "" or
                account.email.strip() == "" or
                account.vname.strip() == ""):
                print "redirect"
                self.redirect(self.url(self.context, 'edit_account'))

    @property
    def _categories(self):
        for cat in sorted(self.request.principal.getCategory(),
                          key=lambda x: x.getName()):
            name = cat.getName()
            form = getMultiAdapter((self.context, self.request), Interface,
                                   name=name.lower() + 'form')
            form.update()
            form.updateForm()
            yield {
                'name': name,
                'doc': cat.getDoc(),
                'desc': self.getDesc(name),
                'url': '%s/%sform' % (self.application_url(), name.lower()),
                'vouchers': self.request.principal.getVouchers(),
                'form': form,
                }

    def getDesc(self, name):
        desc = ""
        if name == "IKG1":
            desc = u"""
                    <h1>H1: Verwaltung / Büro</h1>
                    <h4><u>Beschäftigte:</u></h4>
                    <p>Bitte tragen Sie <u>alle</u> bei der UKH versicherten Beschäftigten ein, die in Ihren Verwaltungsbereichen
                       arbeiten. Zählen Sie dazu die Personen, nicht die Vollzeitstellen. Beamte sind keine Beschäftigten
                       und werden daher nicht mitgezählt.</p>
                    <h4><u>Standorte:</u></h4>
                    <p>Tragen Sie bitte ein, an wie vielen räumlich abgeschlossenen Arbeitsorten mindestens zwei versicherte
                       Beschäftigte üblicherweise anwesend sind. Abgeschlossene Arbeitsorte sind zum Beispiel getrennte Gebäude,
                       jedoch nicht verschiedene Stockwerke oder Abteilungen innerhalb eines Gebäudes.</p>
                    """
        if name == "IKG2":
            desc = u"""
                    <h1>H2: Andere Betriebe und Hochschulen</h1>
                    <h4><u>Andere Betriebe:</u></h4>
                    <p>Alle Betriebe, die nicht in der Hauptsache Verwaltungs- oder Bürobetriebe sind beispielsweise:</p>
                    <p>-  Technische Betriebe</p>
                    <p>-  Landwirtschaftliche und gärtnerische Betriebe</p>
                    <p>-  Hauswirtschaftliche Betriebe</p>
                    <p>-  Betriebe für öffentliche Sicherheit und Ordnung mit Streifendienst</p>
                    <p>-  Zoos</p>
                    <p>-  Theater- und Musikbetriebe</p>
                    <p>-  Betreuungseinrichtungen</p>
                    <p>-  Entsorgungsbetriebe und Bauhöfe ohne Einteilung in Kolonnen.</p>
                    <br>
                    <p>Bitte beachten Sie hier die Besonderheiten für verschiedene Betriebsarten wie beispielsweise:</p>
                    <p>-  Kinderbetreuungseinrichtungen</p>
                    <p>-  Betriebe mit Beschäftigten in Kolonnen</p>
                    <p>-  Betriebe mit besonderer Gefährdung, sofern diese für Ihren Betrieb nachfolgend aufgeführt sind.</p>
                    <h4><u>Beschäftigte:</u></h4>
                    <p>Bitte tragen Sie <u>alle</u> bei der UKH versicherten beschäftigten Personen (ohne Beamte) ein, die in
                       anderen Bereichen als Verwaltung / Büros arbeiten abzüglich</p>
                    <p>a) Beschäftigte in Kindertageseinrichtungen</p>
                    <p>b) Beschäftigte in Kolonnen (Entsorgung, Bauhof)</p>
                    <p>c) Beschäftigte mit spezieller Gefährdung gemäß unten stehenden Sonderkontingenteni</p>
                    <p>d) Beschäftigte in Betrieben mit beruflich qualifizierten Ersthelfern
                          wie Gesundheits- und Pflegediensten, Schwimmbädern.</p>
                    <h4><u>Standorte:</u></h4>
                    <p>Tragen Sie bitte ein, an wie vielen räumlich abgeschlossenen Arbeitsorten mindestens zwei versicherte
                       Beschäftigte üblicherweise anwesend sind. Abgeschlossene Arbeitsorte sind zum Beispiel getrennte Gebäude,
                       jedoch nicht verschiedene Stockwerke oder Abteilungen innerhalb eines Gebäudes.</p>
                    """
        if name == "IKG3":
            desc = u"""
                    <h1>H3: Kindertageseinrichtungen</h1>
                    <h4><u>Kindergruppen:</u></h4>
                    <p>Bitte tragen Sie ein, wie viele Kindergruppen in Ihren Einrichtungen  maximal gleichzeitig betrieben werden.
                       Beispiel: 4 Vormittagsgruppen und 2 Nachmittagsgruppen sind maximal 4 Gruppen gleichzeitig.</p>
                    <p>Tragen Sie bitte ein, an wie vielen räumlich abgeschlossenen Arbeitsorten mindestens zwei versicherte Beschäftigte
                       üblicherweise anwesend sind. Abgeschlossene Arbeitsorte sind zum Beispiel getrennte Gebäude,
                       jedoch nicht verschiedene Stockwerke oder Abteilungen innerhalb eines Gebäudes.</p>
                    """
        if name == "IKG4":
            desc = u"""
                    <h1>H4: In Kolonnen tätige Beschäftigte</h1>
                    <h4><u>Kolonnen:</u></h4>
                    <p>Bitte tragen Sie die maximale Zahl der Kolonnen ein, in denen Beschäftigte in der Entsorgung oder im Bauhof
                       außerhalb gleichzeitig tätig sind.</p>
                    <p>Hinweis: Die übrigen Beschäftigten des Betriebs, die an festen Standorten tätig sind, sind mit der Personenzahl
                       unter „Andere Betriebe“ zu erfassen.</p>
                    """
        if name == "IKG5":
            desc = u"""
                    <h1>H5: Betriebe mit besonderer Gefährdung I</h1>
                    <h4><u>Beschäftigte:</u></h4>
                    <p>Bitte tragen Sie die bei der UKH versicherten Beschäftigten ein, die eine dieser Tätigkeiten ausüben.
                       Beachten Sie bitte auch, dass diese Personen unter „Andere Betriebe“ abzuziehen sind.</p>
                    <p>Geben Sie an, welches Merkmal für besondere Gefährdung zutrifft.</p>
                    """
        if name == "IKG6":
            desc = u"""
                    <h1>H6: Betriebe mit besonderer Gefährdung II</h1>
                    <h4><u>Beschäftigte:</u></h4>
                    <p>Bitte tragen Sie die bei der UKH versicherten Beschäftigten ein, die eine dieser Tätigkeiten ausüben.
                       Beachten Sie bitte auch, dass diese Personen unter „Andere Betriebe“ abzuziehen sind.</p>
                    <p>Geben Sie an, welches Merkmal für besondere Gefährdung zutrifft.</p>
                    """
        return desc


class AdminRootIndex(uvclight.Page):
    uvclight.name('index')
    uvclight.layer(IAdminLayer)
    uvclight.context(AdminRoot)
    require('manage.vouchers')

    @property
    def panels(self):
        for id in uvclight.traversable.bind().get(self.context):
            panel = getattr(self.context, id)
            yield {'title': translate(panel.__label__, context=self.request),
                   'url': self.url(panel)}
    template = uvclight.get_template('adminroot.cpt', __file__)

    def update(self):
        ukhvouchers.need()

    def getAdrActions(self, adr):
        rc = []
        oid = self.request.principal.oid
        if not adr or isinstance(adr, (models.AddressTraeger, models.AddressEinrichtung)):
            rc.append(
                    HTML.tag(
                        'a',
                        href="%s/addresses/add?form.field.oid=%s&form.field.mnr=%s" % (self.application_url(), oid, adr.mnr),
                        c="Neue Adresse anlegen",)
                    )
        elif isinstance(adr, models.Address):
            rc.append(
                    HTML.tag(
                        'a',
                        href="%s/addresses/%s/edit" % (self.application_url(), oid),
                        c="Adresse bearbeiten",)
                    )
        return rc

    def getAccountActions(self, account):
        rc = []
        oid = self.request.principal.oid
        rc.append(
                HTML.tag(
                    'a',
                    href="%s/accounts/add?form.field.oid=%s" % (self.application_url(), oid),
                    c="Neuen Account anlegen",)
                )
        if not account:
            rc.append(
                    HTML.tag(
                        'a',
                        href="%s/accounts/add" % self.application_url(),
                        c="Neuen Account anlegen",)
                    )
        else:
            rc.append(
                    HTML.tag(
                        'a',
                        href="%s/accounts/%s/edit" % (self.application_url(), oid),
                        c="Account bearbeiten",)
                    )
        return rc

    def getCatActions(self):
        rc = []
        oid = self.request.principal.oid
        session = get_session('ukhvoucher')
        category = session.query(models.Category).get(oid)
        if category:
            rc.append(
                    HTML.tag(
                        'a',
                        href="%s/categories/%s/edit" % (self.application_url(), oid),
                        c="Kategorien bearbeiten",)
                    )
        else:
            rc.append(
                    HTML.tag(
                        'a',
                        href="%s/categories/add?form.field.oid=%s" % (self.application_url(), oid),
                        c="Neuen Kategorien anlegen",)
                    )
        return rc

    def getVoucherActions(self):
        rc = []
        oid = self.request.principal.oid
        rc.append(
                HTML.tag(
                    'a',
                    href="%s/accounts/%s/ask.vouchers" % (self.application_url(), oid),
                    c=u"Zusätzliche Gutscheine erzeugen",)
                )
        rc.append(
                HTML.tag(
                    'a',
                    href="%s/accounts/%s/disable.vouchers" % (self.application_url(), oid),
                    c=u"Gutscheine löschen",)
                )
        return rc


class ContainerIndex(uvclight.Page):
    uvclight.name('index')
    uvclight.layer(IAdminLayer)
    uvclight.context(IModelContainer)
    require('manage.vouchers')

    template = uvclight.get_template('container.cpt', __file__)
    batching = uvclight.get_template('batch.pt', __file__)

    def listing(self, item):
        details = inspect(item)
        relations = details.mapper.relationships.keys()
        itemurl = self.url(item)

        for col in self.context.listing_attrs:
            value = getattr(item, col.identifier, col.defaultValue)

            if col.identifier in relations:
                relation = self.relation(col.identifier, value)
                yield col.identifier, [{
                    'value': rel.title,
                    'link': link} for rel, link in relation]
            else:
                yield col.identifier, [{
                    'value': value,
                    'link': col.identifier == 'oid' and itemurl or ''}]

    def batch_elements(self):
        return list(self.context)
                
    def set_batch(self):
        self.batcher = Batcher(self.context, self.request, size=10)
        elements = self.batch_elements()
        if elements:
            self.batcher.update(elements)
            self.dichotomy = get_dichotomy_batches(
                self.batcher.batch.batches,
                self.batcher.batch.total,
                self.batcher.batch.number)
            self.batch = self.batching.render(
                self, **self.namespace())
        else:
            self.batch = u''
                
    def update(self):
        ukhcss.need()
        self.columns = [field.title for field in self.context.listing_attrs]
        self.set_batch()

    def relation(self, id, value):
        site = getSite()
        if id == 'vouchers':
            baseurl = self.url(site) + '/vouchers/'
            for voucher in value:
                yield voucher, baseurl + str(voucher.oid)


class JournalIndex(uvclight.Page):
    uvclight.name('journal')
    uvclight.layer(IAdminLayer)
    uvclight.context(Interface)
    require('manage.vouchers')

    template = uvclight.get_template('journal.cpt', __file__)

    def update(self):
        session = get_session('ukhvoucher')
        self.entries = session.query(JournalEntry)

from profilehooks import profile
class TT(uvclight.View):
    uvclight.layer(IAdminLayer)
    uvclight.context(Interface)
    require('manage.vouchers')

    def render(self):
        from ukhvoucher.models import TestTable
        session = get_session('ukhvoucher')
        tt = session.query(models.AddressEinrichtung.name1).all()
        return ""

