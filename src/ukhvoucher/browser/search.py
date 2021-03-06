# -*- coding: utf-8 -*-

import uvclight

from dolmen.forms.base.markers import NO_VALUE
from sqlalchemy import String, inspect
from sqlalchemy.orm.attributes import InstrumentedAttribute
from ul.auth import require
from uvc.design.canvas import menus, managers
from zope.component import getMultiAdapter
from zope.interface import Interface
from zope.lifecycleevent import created
from zope.location import LocationProxy

from .views import ContainerIndex
from .. import _
from ..apps import AdminRoot, UserRoot
from ..interfaces import IModel, IModelContainer
from ..interfaces import IAdminLayer, IUserLayer
from ..models import (
    Invoices, Accounts, Account, Addresses, Address, Vouchers, Voucher)
from ..resources import ukhvouchers



MULTISELECTS = set(('vouchers',))


class SearchAction(uvclight.Action):

    @staticmethod
    def search(session, model, **data):
        details = inspect(model)
        relationships = details.relationships.keys()

        query = session.query(model)
        for attr in model.searchable_attrs:

            if attr in data:
                value = data[attr]
                if value is NO_VALUE:
                    continue

                if attr in details.relationships.keys():
                    relation = details.relationships.get(attr)
                    modelcls = relation.mapper.class_
                    if relation.collection_class is None:
                        query = query.join(relation.mapper).filter(
                            modelcls.id == value.id)
                    elif value:
                        query = query.join(getattr(model, attr)).filter(
                            modelcls.id.in_([elm.id for elm in value]))
                elif value:
                    column = getattr(model, attr)
                    datatype = column.property.columns[0].type
                    if isinstance(datatype, String):
                        query = query.filter(column.like("%%%s%%" % value))
                    else:
                        query = query.filter(column == value)
        return query

    def __call__(self, view):
        data, errors = view.extractData()
        if errors:
            view.submissionError = errors
            view.flash(_(u"Es ist ein Fehler aufgetreten!"))
            return uvclight.FAILURE

        model = view.context.model
        session = view.context.session
        view.results = [
            LocationProxy(res, view.context, str(res.oid))
            for res in self.search(session, model, **data)]

        if len(view.results) == 1:
            url = view.url(view.results[0])
            return uvclight.SuccessMarker('One result found', True, url=url)
        return uvclight.SUCCESS


class Search(uvclight.Form, ContainerIndex):
    uvclight.name("search")
    uvclight.context(IModelContainer)
    require('manage.vouchers')

    results = None
    ignoreRequest = False
    ignoreContent = True
    postOnly = False
    prefix = ''

    actions = uvclight.Actions(
        SearchAction(_(u'Suche'), 'search'),
    )

    def updateForm(self):
        ukhvouchers.need()
        uvclight.Form.updateForm(self)
        ContainerIndex.update(self)

    def batch_elements(self):
       return getattr(self, 'results', [])

    @property
    def label(self):
        return _(u"Suche : ${item_type}",
                 mapping=dict(item_type=self.context.model.__label__))

    @property
    def fields(self):
        fields = getattr(self.context, 'search_fields', None)
        if fields is None:
            fields = uvclight.Fields(self.context.model.__schema__).select(
                *self.context.model.searchable_attrs)
            for field in fields:
                field.prefix = ''
                field.description = ''
                field.required = False
                field.defaultValue = ''
                field.defaultFactory = None
                if field.identifier in MULTISELECTS:
                    field.mode = 'multiselect'

        return fields


class ModelSearch(uvclight.Viewlet):
    uvclight.order(1)
    uvclight.context(IModelContainer)
    uvclight.viewletmanager(managers.IAboveContent)
    require('manage.vouchers')
    uvclight.baseclass()

    template = uvclight.get_template('search.pt', __file__)

    @property
    def available(self):
        return not isinstance(self.view, Search)

    def update(self):
        platzhalter = ''
        self.target = self.view.url(self.context) + '/search'
        self.attribute = self.context.model.search_attr
        if self.context.__label__ == 'Vouchers':
            platzhalter = u'Berechtigungsschein Nummer'
        if self.context.__label__ == 'Zuordnungen':
            platzhalter = u'Zuordnung'
        #self.placeholder = "%s (%s)" % (self.context.__label__, self.attribute)
        self.placeholder = platzhalter


class InvoicesSearch(ModelSearch):
    uvclight.context(Invoices)


class VouchersSearch(ModelSearch):
    uvclight.context(Vouchers)


class SearchResults(uvclight.Viewlet):
    uvclight.order(1)
    uvclight.view(Search)
    uvclight.context(IModelContainer)
    uvclight.viewletmanager(managers.IBelowContent)
    require('manage.vouchers')

    template = uvclight.get_template('results.pt', __file__)

