# -*- coding: utf-8 -*-

from fanstatic import Library, Resource
from js.jquery import jquery
from js.jquery_tablesorter import tablesorter

library = Library('ukhvoucher', 'static')

ukhcss = Resource(library, 'ukh.css')
chosencss = Resource(library, 'chosen.css')
chosenjs = Resource(library, 'chosen.jquery.js', depends=[jquery, chosencss])

#chosencss = Resource(library, 'select2.min.css')
#chosenjs = Resource(library, 'select2.min.js', depends=[jquery, chosencss])
chosenajax = Resource(library, 'chosen.ajaxaddition.jquery.js', depends=[chosenjs])


ukhvouchers = Resource(library, 'ukh.js', depends=[chosenjs, tablesorter])


ehcss = Resource(library, 'eh.css')
