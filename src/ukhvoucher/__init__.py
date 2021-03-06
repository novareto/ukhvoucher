# -*- coding: utf-8 -*-

from sqlalchemy.ext.declarative import declarative_base
from zope.i18nmessageid import MessageFactory
from zope.component.hooks import setSite
import logging


class Site(object):

    def __init__(self, root):
        self.root = root

    def __enter__(self):
        setSite(self.root)
        return self.root

    def __exit__(self, exc_type, exc_value, traceback):
        setSite()


_ = MessageFactory('ukhvoucher')

Base = declarative_base()
VOCABULARIES = {}


DISABLED = u'ungültig'
CREATED = u"erstellt"
MANUALLY_CREATED = u"manuell_erstellt"
BOOKED = u"gebucht"
NOT_BOOKED = u"ausgebucht"


logger = logging.getLogger('ukhvoucher')

def log(message, summary='', severity=logging.INFO, extra_data=None):
    logger.log(severity, '%s %s', summary, message, extra=extra_data)

