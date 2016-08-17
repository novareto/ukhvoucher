from dolmen.forms.ztk.widgets.bool import CheckBoxWidget
from grokcore.component import adapts, name
import uvclight



class CheckBoxWidget(CheckBoxWidget):
    name("checkbox")
    template = uvclight.get_template('checkbox.cpt', __file__)
