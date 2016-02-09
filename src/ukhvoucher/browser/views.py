# -*- coding: utf-8 -*-

import uvclight
from ..apps import AdminRoot, UserRoot
from ..interfaces import IAdminLayer, IUserLayer
from ..interfaces import IModel, IModelContainer
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
                    __________________________________________________________________________________________
                    Beschäftigte: Bitte tragen Sie alle bei der UKH versicherten Beschäftigten ein, die in Ihren
                    Verwaltungsbereichen arbeiten. Zählen Sie dazu die Personen, nicht die Vollzeitstellen.
                    Beamte sind keine Beschäftigten und werden daher nicht mitgezählt.
                    __________________________________________________________________________________________
                    Standorte: Tragen Sie bitte ein, an wie vielen räumlich abgeschlossenen Arbeitsorten mindestens
                    zwei versicherte Beschäftigte üblicherweise anwesend sind. Abgeschlossene Arbeitsorte sind zum
                    Beispiel getrennte Gebäude, jedoch nicht verschiedene Stockwerke oder Abteilungen innerhalb eines Gebäudes.
                    """
        if name == "IKG2":
            desc = u"""
                    __________________________________________________________________________________________
                    Andere Betriebe: Alle Betriebe, die nicht in der Hauptsache Verwaltungs- oder Bürobetriebe sind, beispielsweise
                    technische Betriebe, landwirtschaftliche und gärtnerische Betriebe,  hauswirtschaftliche Betriebe, Betriebe
                    für öffentliche Sicherheit und Ordnung mit Streifendienst, Zoos, Theater- und Musikbetriebe, Betreuungseinrichtungen,
                    Entsorgungsbetriebe und Bauhöfe ohne Einteilung in Kolonnen.
                    __________________________________________________________________________________________

                    Bitte beachten Sie hier die Besonderheiten für verschiedene Betriebsarten wie Kinderbetreuungseinrichtungen
                    Betriebe mit Beschäftigten in Kolonnen, Betriebe mit besonderer Gefährdung, sofern diese für Ihren Betrieb
                    nachfolgend aufgeführt sind.
                    __________________________________________________________________________________________
                    Beschäftigte: Bitte tragen Sie alle bei der UKH versicherten beschäftigten Personen (ohne Beamte) ein,
                    die in anderen Bereichen als Verwaltung / Büros arbeiten abzüglich a) Beschäftigte in Kindertageseinrichtungen,
                    b) Beschäftigte in Kolonnen (Entsorgung, Bauhof), c) Beschäftigte mit spezieller Gefährdung gemäß unten
                    stehenden Sonderkontingenten, d) Beschäftigte in Betrieben mit beruflich qualifizierten Ersthelfern
                    wie Gesundheits- und Pflegediensten, Schwimmbädern.
                    __________________________________________________________________________________________
                    Standorte: Tragen Sie bitte ein, an wie vielen räumlich abgeschlossenen Arbeitsorten mindestens
                    zwei versicherte Beschäftigte üblicherweise anwesend sind. Abgeschlossene Arbeitsorte sind zum
                    Beispiel getrennte Gebäude, jedoch nicht verschiedene Stockwerke oder Abteilungen innerhalb eines Gebäudes.

                    """
        if name == "IKG3":
            desc = u"""
                    __________________________________________________________________________________________
                    Kindergruppen: Bitte tragen Sie ein, wie viele Kindergruppen in Ihren Einrichtungen  maximal
                    gleichzeitig betrieben werden. Beispiel: 4 Vormittagsgruppen und 2 Nachmittagsgruppen sind
                    maximal 4 Gruppen gleichzeitig.
                    __________________________________________________________________________________________
                    Tragen Sie bitte ein, an wie vielen räumlich abgeschlossenen Arbeitsorten mindestens zwei
                    versicherte Beschäftigte üblicherweise anwesend sind. Abgeschlossene Arbeitsorte sind zum
                    Beispiel getrennte Gebäude, jedoch nicht verschiedene Stockwerke oder Abteilungen innerhalb eines Gebäudes.
                    """
        if name == "IKG4":
            desc = u"""
                    __________________________________________________________________________________________
                    Kolonnen: Bitte tragen Sie die maximale Zahl der Kolonnen ein, in denen Beschäftigte in der
                    Entsorgung oder im Bauhof außerhalb gleichzeitig tätig sind.
                    __________________________________________________________________________________________
                    Hinweis: Die übrigen Beschäftigten des Betriebs, die an festen Standorten tätig sind,
                    sind mit der Personenzahl unter „Andere Betriebe“ zu erfassen.
                    """
        if name == "IKG5":
            desc = u"""
                    __________________________________________________________________________________________
                    Beschäftigte: Bitte tragen Sie die bei der UKH versicherten Beschäftigten ein, die eine dieser
                    Tätigkeiten ausüben. Beachten Sie bitte auch, dass diese Personen unter „Andere Betriebe“ abzuziehen sind.
                    __________________________________________________________________________________________
                    Geben Sie an, welches Merkmal für besondere Gefährdung zutrifft.
                    """
        if name == "IKG6":
            desc = u"""
                    __________________________________________________________________________________________
                    Beschäftigte: Bitte tragen Sie die bei der UKH versicherten Beschäftigten ein, die eine dieser
                    Tätigkeiten ausüben. Beachten Sie bitte auch, dass diese Personen unter „Andere Betriebe“ abzuziehen sind.
                    __________________________________________________________________________________________
                    Geben Sie an, welches Merkmal für besondere Gefährdung zutrifft.
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

    def update(self):
        ukhcss.need()
        self.columns = [field.title for field in self.context.listing_attrs]
        elements = list(self.context)
        self.batcher = Batcher(self.context, self.request, size=10)
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


class TT(uvclight.View):
    uvclight.layer(IAdminLayer)
    uvclight.context(Interface)
    require('manage.vouchers')

    def render(self):
        from ukhvoucher.models import TestTable
        session = get_session('ukhvoucher')
        import pdb; pdb.set_trace()
        return ""

