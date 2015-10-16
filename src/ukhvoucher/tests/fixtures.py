# -*- coding: utf-8 -*-
# Copyright (c) 2007-2014 NovaReto GmbH
# cklinger@novareto.de

import pytest
import ukhvoucher
import ukhvoucher.utils

from paste.deploy import loadapp
from uvclight.tests.testing import configure


@pytest.fixture(scope="session")
def config(request):
    """loading the zca with configure.zcml of this package"""
    return configure(request, ukhvoucher, 'configure.zcml')


@pytest.fixture(scope="session")
def app(request):
    """ load the paste.deploy wsgi environment from deploy.ini"""
    deploy_ini = "config:/home/novareto/ukh/ukhvoucher_project/parts/etc/deploy.ini"
    return loadapp(deploy_ini.replace('=', ':'), name="main", global_conf={})


@pytest.fixture(scope="session")
def root(request):
    """ create an instance of the application"""
    return ukhvoucher.utils.Root('app')

