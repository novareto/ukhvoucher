# -*- coding: utf-8 -*-

import os
import uvclight
import zope.sendmail
import zope.component


from zope.sendmail.mailer import SMTPMailer

from email import Encoders
from email.header import Header
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.MIMEMultipart import MIMEMultipart
from email.Utils import COMMASPACE, formatdate

from cromlech.browser import IPublicationRoot
from zope.interface import implements
from zope.location import Location
from zope.component import getGlobalSiteManager
from uvclight.utils import Site
from ul.browser.publication import Publication


class Root(Location):
    implements(IPublicationRoot)

    title = u"Example Site"
    description = u"An Example application."

    def __init__(self, name):
        self.name = name

    def getSiteManager(self):
        return getGlobalSiteManager()


class Application(Publication):
    def site_manager(self, environ):
        return Site(Root, self.name)



queue_path = "/tmp/mq"

mailer_object = SMTPMailer("10.64.33.17", 25, force_tls=False)


def mailer():
    return mailer_object


def delivery():
    from zope.sendmail.delivery import QueuedMailDelivery

    return QueuedMailDelivery(queue_path)


def start_processor_thread():
    from zope.sendmail.queue import QueueProcessorThread

    thread = QueueProcessorThread()
    thread.setMailer(mailer_object)
    thread.setQueuePath(queue_path)
    thread.start()


def send_mail(send_from, send_to, subject, text, files=[]):
    assert isinstance(send_to, (list, tuple, set))
    assert isinstance(files, (list, tuple, set))

    msg = MIMEMultipart()

    # headers
    msg["From"] = send_from
    msg["To"] = COMMASPACE.join(send_to)
    msg["Date"] = formatdate(localtime=True)
    msg["Subject"] = Header(subject, "utf-8")

    # body
    txt = MIMEText(text, "plain", "utf-8")
    msg.attach(txt)

    for f in files:
        part = MIMEBase("application", "octet-stream")
        with open(f, "rb") as fd:
            part.set_payload(fd.read())
        Encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition", 'attachment; filename="%s"' % os.path.basename(f)
        )
        msg.attach(part)

    mailer = zope.component.getUtility(
        zope.sendmail.interfaces.IMailDelivery, name=u"ukh.maildelivery"
    )
    mailer.send(send_from, send_to, msg.as_string())


uvclight.global_utility(
    mailer, provides=zope.sendmail.interfaces.IMailer, name="ukh.smtpmailer"
)
uvclight.global_utility(
    delivery, zope.sendmail.interfaces.IMailDelivery, name="ukh.maildelivery"
)
start_processor_thread()
