# -*- coding: utf-8 -*-

from fanstatic import Library, Resource
from js.jquery import jquery

library = Library('ukhvoucher', 'static')

chosencss = Resource(library, 'chosen.css')
chosenjs = Resource(library, 'chosen.jquery.js', depends=[jquery, chosencss])
ukhvouchers = Resource(library, 'ukh.js', depends=[chosenjs])
