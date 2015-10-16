# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de

from cromlech.browser.testing import TestRequest
from grokcore.component import Context
from zope.component import getMultiAdapter


class TestClass:
    request = TestRequest()
    context = Context()

    def test_example(self):
        assert 1==1

#    def test_view(self, config, root):
#        view = getMultiAdapter((root, self.request), name='index')
#        view.update()
#        assert "HALLO WELT" == view.render()

#    # Achtung infrae.testbrowser muss zunächst installiert werden
#    def test_browser(self, config, app):
#        from infrae.testbrowser import Browser
#        browser = Browser(app)
#        browser.open('http://localhost')
#        assert browser.status == "200 OK"

