from cromlech.sqlalchemy import get_session
from zope.schema.interfaces import IContextSourceBinder
from zope.schema.vocabulary import SimpleVocabulary, SimpleTerm
from zope.interface import provider


class MyVoc(SimpleVocabulary):
    def __init__(self):
        print "INIT"

    def __contains__(self, value):
        session = get_session('ukhvoucher')
        from ukhvoucher.models import Voucher
        return session.query(Voucher).get(value.oid)

    def getTerm(self, term):
        session = get_session('ukhvoucher')
        from ukhvoucher.models import Voucher
        item = session.query(Voucher).get(term)
        return SimpleTerm(item, token=item.oid, title="%s - %s %s" %(item.title, item.status.strip(), item.cat))

    def getTermByToken(self, token):
        session = get_session('ukhvoucher')
        from ukhvoucher.models import Voucher
        item = session.query(Voucher).get(token)
        return SimpleTerm(item, token=item.oid, title="%s - %s %s" %(item.title, item.status.strip(), item.cat))


@provider(IContextSourceBinder)
def mysource(context):
    return MyVoc()
