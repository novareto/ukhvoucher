# -*- coding: utf-8 -*-

import uvclight
from webhelpers.html.builder import HTML
from ukhvoucher import models
from ..apps import AdminRoot, UserRoot
from ..interfaces import IAdminLayer, IUserLayer
from ..interfaces import IModelContainer, get_oid
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
from profilehooks import profile
from natsort import natsorted

class SearchUnternehmen(uvclight.JSON):
    uvclight.name('search_unternehmen')
    uvclight.layer(IAdminLayer)
    uvclight.context(Interface)
    require('manage.vouchers')

    #@profile
    def update(self):
        self.term = self.request.form['data[q]']
        self.vocabulary = get_oid(self.context)

    #@profile
    def render(self):
        terms = []
        matcher = self.term.lower()
        for item in self.vocabulary:
            if matcher in item.title.lower():
                terms.append({'id': item.token, 'text': item.title})
        return {'q': self.term, 'results': terms}



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
        for cat in natsorted(self.request.principal.getCategory(),
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
        if name == "K1":
            desc = u"""
                    <h2>K1: Verwaltung / Büro</h2>
                    <h4><u>Beschäftigte:</u></h4>
                    <p>Bitte tragen Sie <u>alle</u> bei der UKH versicherten Beschäftigten ein, die in Ihren Verwaltungsbereichen
                       arbeiten. Zählen Sie dazu die Personen, nicht die Vollzeitstellen. Beamte sind keine Beschäftigten
                       und werden daher nicht mitgezählt.</p>
                    <h4><u>Standorte:</u></h4>
                    <p>Tragen Sie bitte ein, an wie vielen räumlich abgeschlossenen Arbeitsorten mindestens zwei versicherte
                       Beschäftigte üblicherweise anwesend sind. Abgeschlossene Arbeitsorte sind zum Beispiel getrennte Gebäude,
                       jedoch nicht verschiedene Stockwerke oder Abteilungen innerhalb eines Gebäudes.</p>
                    """
        if name == "K2":
            desc = u"""
                    <h2>K2: Sonstige Betriebe und Hochschulen</h2>
                    <h4><u>Sonstige Betriebe:</u></h4>
                    <p>Alle Betriebe, die nicht in der Hauptsache Verwaltungs- oder Bürobetriebe sind beispielsweise:</p>
                    <p>-  Technische Betriebe</p>
                    <p>-  Landwirtschaftliche und gärtnerische Betriebe</p>
                    <p>-  Hauswirtschaftliche Betriebe</p>
                    <p>-  Betriebe für öffentliche Sicherheit und Ordnung mit Streifendienst</p>
                    <p>-  Zoos (ohne Beschäftigte in der Tierpflege)</p>
                    <p>-  Theater- und Musikbetriebe</p>
                    <p>-  Betreuungseinrichtungen (ohne Kindertagesstätten, -krippen, Schulbetreuung)</p>
                    <p>-  Entsorgungsbetriebe und Bauhöfe ohne Einteilung in Kolonnen</p>
                    <p>-  Schulpersonal der Schulträger</p>
                    <p>-  Betriebe mit beruflich qualifizierten Ersthelfern wie Gesundheits- und Pflegediensten, Schwimmbädern (K11)</p>
                    <br>
                    <p>Bitte beachten Sie hier die Besonderheiten für verschiedene Betriebsarten wie beispielsweise:</p>
                    <p>-  Kinderbetreuungseinrichtungen (K3) und Schulbetreuung (K9)</p>
                    <p>-  Betriebe mit Beschäftigten in Kolonnen (K4)</p>
                    <p>-  Betriebe mit besonderer Gefährdung (K5, K6)</p>
                    <h4><u>Beschäftigte:</u></h4>
                    <p>Bitte tragen Sie <u>alle</u> bei der UKH versicherten beschäftigten Personen (ohne Beamte) ein, die in
                       anderen Bereichen als Verwaltung / Büros arbeiten abzüglich</p>
                    <p>a) Beschäftigte in Kindertageseinrichtungen</p>
                    <p>b) Beschäftigte in Kolonnen (Bauhof, Entsorgung)</p>
                    <p>c) Beschäftigte mit spezieller Gefährdung gemäß aufgeführtem Sonderkontingent</p>
                    <h4><u>Standorte:</u></h4>
                    <p>Tragen Sie bitte ein, an wie vielen räumlich abgeschlossenen Arbeitsorten mindestens zwei versicherte
                       Beschäftigte üblicherweise anwesend sind. Abgeschlossene Arbeitsorte sind zum Beispiel getrennte Gebäude,
                       jedoch nicht verschiedene Stockwerke oder Abteilungen innerhalb eines Gebäudes.</p>
                    """
        if name == "K3":
            desc = u"""
                    <h2>K3: Kindertageseinrichtungen</h2>
                    <h4><u>Kindergruppen:</u></h4>
                    <p>Bitte tragen Sie ein, wie viele Kindergruppen in Ihren Einrichtungen  maximal gleichzeitig betrieben werden.
                       Beispiel: 4 Vormittagsgruppen und 2 Nachmittagsgruppen sind maximal 4 Gruppen gleichzeitig.</p>
                    <p>Tragen Sie bitte ein, an wie vielen räumlich abgeschlossenen Arbeitsorten mindestens zwei versicherte Beschäftigte
                       üblicherweise anwesend sind. Abgeschlossene Arbeitsorte sind zum Beispiel getrennte Gebäude,
                       jedoch nicht verschiedene Stockwerke oder Abteilungen innerhalb eines Gebäudes.</p>
                    """
        if name == "K4":
            desc = u"""
                    <h2>K4: In Kolonnen tätige Beschäftigte</h2>
                    <h4><u>Kolonnen:</u></h4>
                    <p>Bitte tragen Sie die maximale Zahl der Kolonnen ein, in denen Beschäftigte in der Entsorgung oder im Bauhof
                       außerhalb gleichzeitig tätig sind.</p>
                    <p>Hinweis: Die übrigen Beschäftigten des Betriebs, die an festen Standorten tätig sind, sind mit der Personenzahl
                       unter der Kontingent Kategorie 2 „Sonstige Betriebe“ zu erfassen.</p>
                    """
        if name == "K5":
            desc = u"""
                    <h2>K5: Beschäftigte und Einrichtungen mit eröhter Gefährdung</h2>
                    <h4><u>Beschäftigte:</u></h4>
                    <p>Bitte tragen Sie die bei der UKH versicherten Beschäftigten ein, die eine dieser Tätigkeiten ausüben.
                       Beachten Sie bitte auch, dass diese Personen unter der Kontingent Kategorie 2 „Sonstige Betriebe“ abzuziehen sind.</p>
                    <p>Geben Sie an, welches Merkmal für erhöhte Gefährdung zutrifft.</p>
                    """
        if name == "K6":
            desc = u"""
                    <h2>K6: Betriebe mit besonders hoher Gefährdung</h2>
                    <h4><u>Beschäftigte:</u></h4>
                    <p>Bitte tragen Sie die bei der UKH versicherten Beschäftigten ein, die eine dieser Tätigkeiten ausüben.
                       Beachten Sie bitte auch, dass diese Personen unter „Andere Betriebe“ abzuziehen sind.</p>
                    <p>Geben Sie an, welches Merkmal für die besonders hohe Gefährdung zutrifft.</p>
                    """
        if name == "K7":
            desc = u"""
                    <h2>K7: Schulen (nur Lehrkräfte)</h2>
                    <h4><u>Lehrkräfte:</u></h4>
                    <p>Bitte tragen Sie die Zahl der Lehrkräfte ein, die an der Schule und ggf. an den Außenstellen der Schule tätig sind.
                       Wir übernehmen Lehrgangsgebühren für die Teilnahme an Erste Hilfe-Fortbildungen im Sinne des DGUV Grundsatzes 304-001
                       oder für Erste Hilfe-Fortbildungen Schule für 15 % des gesamten Kollegiums in einem Zeitraum von 2 Jahren.</p>
                    <p>Hinweis: Bitte zählen Sie Personal in anderen Bereichen, bspw. in der Schulbetreuung, Reinigung,
                       Sekretariat oder Hausmeister nicht mit. Für dieses Personal beantragt der Arbeitgeber die Kostenübernahme
                       der Lehrgangsgebühren bei der zuständigen Fach-Berufsgenossenschaft oder bei uns als Mitgliedsunternehmen.</p>
                    """
        if name == "K8":
            desc = u"""
                    <h2>K9: Schulstandorte </h2>
                    <h4><u>Standorte:</u></h4>
                    <p>Bitte tragen Sie ein, an wie vielen Schulstandorten Personal in den Bereichen Reinigung,
                       Sekretariat oder Hausmeister beschäftigt wird.</p>
                    <p>Als Schulstandort gilt eine Schule, wobei Außenstellen von Schulen als eigener Standort gezählt werden.</p>
                    """
        if name == "K9":
            desc = u"""
                    <h2>K9: Schulbetreuung</h2>
                    <h4><u>Gruppen:</u></h4>
                    <p>Bitte tragen Sie ein, wie viele Schulbetreuungsgruppen höchstens gleichzeitig betrieben werden.
                       Beispiel: 3 Gruppen dienstags und 2 Gruppen donnerstags sind 3 Gruppen gleichzeitig.</p>
                    """
        if name == "K10":
            desc = u"""
                    <h2>K10: Freiwillige Feuerwehren</h2>
                    <h4><u>Aktive Einsatzkräfte:</u></h4>
                    <p>Bitte tragen Sie die Summe der aktiven Einsatzkräfte aus allen Orts- oder Stadtteilfeuerwehren ein.
                       Die UKH übernimmt die Kosten für Erste Hilfe Lehrgänge über 9 Unterrichtseinheiten für 10% der
                       aktiven Einsatzkräfte im Zeitraum von 2 Jahren.</p>
                    <h4><u>Jugendbetreuer/innen:</u></h4>
                    <p>Bitte tragen Sie auch hier alle Jugendbetreuer/innen der Orts oder Stadtteilfeuerwehren ein.
                       Die UKH übernimmt für alle einmal in 2 Jahren die Kosten der Erste Hilfe Lehrgänge.</p>
                    """
        if name == "K11":
            desc = u"""
                    <h2>K11: Gesundheitsdienste</h2>
                    <p>Gesundheitsdienste brauchen neben dem medizinischen Personal nur dann betriebliche Ersthelfer,
                       wenn Bereiche so aus dem medizinischen Betrieb ausgelagert sind, dass die Ersthelfer nicht erreichbar sind.</p>
                    <h4><u>Beschäftigte in der Verwaltung</u></h4>
                    <p>Bitte tragen Sie hier nur die Zahl derjenigen Beschäftigten in der Verwaltung ein,
                       die an einem anderen Standort als das medizinische Personal tätig sind.</p>
                    <h4><u>Beschäftigte im technischen Bereich</u></h4>
                    <p>Bitte tragen Sie hier nur die Zahl derjenigen Beschäftigten ein, die an einem anderen Standort als das medizinische Personal tätig sind.
                       Zum technischen Bereich zählen Labore, Werkstätten, Wäschereien und Küchen.</p>
                    <h4><u>Standorte</u></h4>
                    <p>Bitte tragen Sie nur Standorte für die jeweiligen Bereiche ein, die vom Medizinbetrieb getrennt sind.
                       Als eigene Standorte gelten räumlich abgeschlossene Arbeitsorte, an denen mindestens zwei versicherte
                       Beschäftigte üblicherweise anwesend sind.
                       Verschiedene Stockwerke oder Abteilungen innerhalb eines Gebäudes zählen nicht als abgeschlossene Arbeitsorte.</p>
                    """
        return desc

class AdminRootIndex(uvclight.Page):
    uvclight.name('index')
    uvclight.layer(IAdminLayer)
    uvclight.context(AdminRoot)
    require('manage.vouchers')

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
                        c="Neue Kategorien anlegen",)
                    )
        return rc

    def getVoucherActions(self):
        rc = []
        oid = self.request.principal.oid
        rc.append(
                HTML.tag(
                    'a',
                    href="%s/account/%s/ask.vouchers" % (self.application_url(), oid),
                    c=u"Zusätzliche Berechtigungsscheine erzeugen",)
                )
        rc.append(
                HTML.tag(
                    'a',
                    href="%s/account/%s/disable.vouchers" % (self.application_url(), oid),
                    c=u"Berechtigungsscheine sperren",)
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
        self.batcher = Batcher(self.context, self.request, size=50)
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
        ukhvouchers.need()
        session = get_session('ukhvoucher')
        self.entries = session.query(JournalEntry)

from profilehooks import profile
class TT(uvclight.View):
    uvclight.layer(IAdminLayer)
    uvclight.context(Interface)
    require('manage.vouchers')

    def render(self):
        session = get_session('ukhvoucher')
        tt = session.query(models.AddressEinrichtung.name1).all()
        return ""

