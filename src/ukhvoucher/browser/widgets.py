# -*- coding: utf-8 -*-

import uvclight
from grokcore import component as grok
from dolmen.forms.ztk.interfaces import ICollectionField
from zope.interface import Interface
from dolmen.forms.base.interfaces import IWidget
from dolmen.forms.base.widgets import WidgetExtractor
from dolmen.forms.base.markers import NO_VALUE
from dolmen.forms.ztk.widgets.choice import ChoiceField
from dolmen.forms.ztk.widgets.textline import TextLineField
from cromlech.sqlalchemy import get_session
from dolmen.forms.ztk.widgets.collection import (
    _, WidgetExtractor, MultiGenericFieldWidget, MultiGenericWidgetExtractor,
    SetField, newCollectionWidgetFactory)
from ..models import Voucher


grok.global_adapter(
    newCollectionWidgetFactory(mode='multidisabled'),
    adapts=(ICollectionField, Interface, Interface),
    provides=IWidget,
    name='multidisabled')


class MultiSelectFieldWidget(MultiGenericFieldWidget):
    grok.name('multidisabled')
    template = uvclight.get_template('disabled.cpt', __file__)

    def disabled(self, token):
        return token in self._disabled


class CustomMultiWidgetExtractor(WidgetExtractor):
    grok.adapts(SetField, TextLineField, uvclight.Form, Interface)

    def __init__(self, field, value_field, form, request):
        super(CustomMultiWidgetExtractor, self).__init__(field, form, request)
        self.value_field = value_field

    def extract(self):
        value, errors = super(CustomMultiWidgetExtractor, self).extract()
        if self.component.mode == 'multidisabled':
            if errors is None:
                if value is NO_VALUE:
                    # Nothing selected
                    return (self.component.collectionType(), None)
                try:
                    if not isinstance(value, list):
                        value = [value]

                    session = get_session('ukhvoucher')
                    vouchers = session.query(Voucher).filter(Voucher.oid.in_(value)).all()
                    if len(vouchers) != len(value):
                        return (None, _(u'Invalid ID.'))
                    return (self.component.collectionType(vouchers), errors)

                except LookupError:
                    return (None, _(u'The selected value is not available.'))
        return (value, errors)

