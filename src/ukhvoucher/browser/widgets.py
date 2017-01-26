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

    def upidate(self):
        self._disabled = self.component.valueField.vocabularyFactory(self.form.context).disabled_items
        MultiChoiceFieldWidget.update(self)

    def disabled(self, token):
        return token in self._disabled
