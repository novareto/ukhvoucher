# -*- coding: utf-8 -*-

from fanstatic import Library, Resource
from js.jquery import jquery
from js.jquery_tablesorter import tablesorter

library = Library("ukhvoucher", "static")

ukhcss = Resource(library, "ukh.css")
masked_input = Resource(library, "jquery.mask.min.js", depends=[jquery])
jmi = Resource(library, "jasny-bootstrap.js", depends=[jquery])

select2css = Resource(library, "select2.min.css")
select2js = Resource(library, "select2.js", depends=[jquery, select2css])
select2_de = Resource(library, "select2_de.js", depends=[select2js])

ukhvouchers = Resource(
    library, "ukh.js", depends=[select2_de, tablesorter, masked_input, jmi]
)


ehcss = Resource(library, "eh.css")
