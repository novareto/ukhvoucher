import uvclight
from grokcore import component as grok
from dolmen.forms.ztk.interfaces import ICollectionField
from zope.interface import Interface
from dolmen.forms.base.interfaces import IWidget
from dolmen.forms.ztk.widgets.collection import (
    MultiChoiceFieldWidget, newCollectionWidgetFactory)


grok.global_adapter(
    newCollectionWidgetFactory(mode='multidisabled'),
    adapts=(ICollectionField, Interface, Interface),
    provides=IWidget,
    name='multidisabled')


class MultiSelectFieldWidget(MultiChoiceFieldWidget):
    grok.name('multidisabled')
    template = uvclight.get_template('disabled.cpt', __file__)

    def disabled(self, token):
        voc = self.component.valueField.vocabularyFactory(None)
        return token in voc.disabled_items
