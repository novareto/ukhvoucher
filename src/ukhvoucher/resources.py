# -*- coding: utf-8 -*-

from fanstatic import Library, Resource
from js.jquery import jquery
from js.jquery_tablesorter import tablesorter

library = Library("ukhvoucher", "static")

ukhcss = Resource(library, "ukh.css")
masked_input = Resource(library, "jquery.mask.min.js", depends=[jquery])
jmi = Resource(library, "jasny-bootstrap.js", depends=[jquery])

chosencss = Resource(library, "select2.min.css")
select2_de = Resource(library, "select2_de.js")
chosenjs = Resource(library, "select2.min.js", depends=[jquery, select2_de, chosencss])
ukhvouchers = Resource(
    library, "ukh.js", depends=[chosenjs, tablesorter, masked_input, jmi]
)


ehcss = Resource(library, "eh.css")
