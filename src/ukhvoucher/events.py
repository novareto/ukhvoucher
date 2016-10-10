from zope.lifecycleevent.interfaces import IObjectModifiedEvent
import grokcore.component as grok
import uvclight

from .interfaces import IAccount, ICategory


@grok.subscribe(IAccount, IObjectModifiedEvent)
def handle_cacheclear(account, event):
    principal = uvclight.utils.current_principal()
    principal.getAccount(invalidate=True)

@grok.subscribe(ICategory, IObjectModifiedEvent)
def handle_cacheclear(account, event):
    principal = uvclight.utils.current_principal()
    principal.getCategory(invalidate=True)
