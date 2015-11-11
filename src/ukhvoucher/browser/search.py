# -*- coding: utf-8 -*-

import uvclight
from ul.auth import require
from .. import _
from ..apps import AdminRoot, UserRoot
from ..interfaces import IModel, IModelContainer
from ..interfaces import IAdminLayer, IUserLayer
from ..models import Accounts, Account, Addresses, Address, Vouchers, Voucher
from zope.component import getMultiAdapter
from zope.interface import Interface

from sqlalchemy import String, inspect
from sqlalchemy.orm.attributes import InstrumentedAttribute
from zope.lifecycleevent import created
from zope.location import LocationProxy
from dolmen.forms.base.markers import NO_VALUE
from uvc.design.canvas import menus, managers


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
                        print [elm.id for elm in value]
                        query = query.join(getattr(model, attr)).filter(
                            modelcls.id.in_([elm.id for elm in value]))
                elif value:
                    column = getattr(model, attr)
                    datatype = column.property.columns[0].type
                    if isinstance(datatype, String):
                        query = query.filter(column.like("%%%s%%" % value))
                    else:
                        query = query.filter(column == value)

        return query.all()

    def __call__(self, view):
        data, errors = view.extractData()
        if errors:
            view.submissionError = errors
            view.flash(_(u"An error occured."))
            return uvclight.FAILURE

        model = view.context.model
        session = view.context.session
        view.results = self.search(session, model, **data)
        return uvclight.SUCCESS


class Search(uvclight.Form):
    uvclight.name("search")
    uvclight.context(IModelContainer)
    require('manage.vouchers')

    ignoreRequest = False
    ignoreContent = True
    postOnly = False
    prefix = ''

    actions = uvclight.Actions(
        SearchAction(_(u'Search'), 'search'),
    )

    def update(self):
        self.columns = [field.title for field in self.context.listing_attrs]
        uvclight.Form.update(self)

    def listing(self, item):
        for col in self.context.listing_attrs:
            yield col.identifier, getattr(
                item, col.identifier, col.defaultValue)

    @property
    def label(self):
        return _(u"Search : ${item_type}",
                 mapping=dict(item_type=self.context.model.__label__))

    @property
    def fields(self):
        fields = uvclight.Fields(self.context.model.__schema__)
        fields = fields.select(*self.context.model.searchable_attrs)
        for field in fields:
            field.prefix = ''
            field.description = ''
            field.required = False
            if field.identifier in MULTISELECTS:
                field.mode = 'multiselect'

        return fields


class ModelSearch(uvclight.Viewlet):
    uvclight.order(1)
    uvclight.context(IModelContainer)
    uvclight.viewletmanager(managers.IAboveContent)
    require('manage.vouchers')

    template = uvclight.get_template('search.pt', __file__)

    @property
    def available(self):
        return not isinstance(self.view, Search)

    def update(self):
        self.target = self.view.url(self.context) + '/search'
        self.attribute = self.context.model.search_attr


class SearchResults(uvclight.Viewlet):
    uvclight.order(1)
    uvclight.view(Search)
    uvclight.context(IModelContainer)
    uvclight.viewletmanager(managers.IBelowContent)
    require('manage.vouchers')

    template = uvclight.get_template('results.pt', __file__)

    def update(self):
        self.results = [
            LocationProxy(res, self.context, str(res.oid))
            for res in getattr(self.view, 'results', [])]

    def url(self, item):
        return self.view.url(item)
