# -*- coding: utf-8 -*-
# Copyright (c) 2007-2013 NovaReto GmbH
# cklinger@novareto.de

import uvclight


from reportlab.lib.pagesizes import letter
from reportlab.graphics.barcode.common import I2of5
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from tempfile import NamedTemporaryFile
from ..interfaces import IUserLayer
from ..apps import UserRoot


styles = getSampleStyleSheet()


ADDRESS = """
<h2> %s </h2><br/>
<p> %s </p><br/>
<p> %s </p><br/>
<p> %s %s </p><br/>
<p> %s %s </p><br/>"""


def printAddress(principal):
    adr = principal.getAddress()
    return ADDRESS % (
        adr.name1,
        adr.name2,
        adr.name3,
        adr.street,
        adr.number,
        adr.zip_code,
        adr.city,
    )


VOUCHER = """
 <h2> Gutschein </h2><br/>
 <p> %s </p><br/>
 <p> %s </p><br/>
"""


def printVoucher(voucher):
    return VOUCHER % (
        voucher.oid,
        voucher.creation_date.strftime('%d.%m.%Y %H:%M')
    )


class PDF(uvclight.Page):
    uvclight.layer(IUserLayer)
    uvclight.context(UserRoot)
    uvclight.auth.require('users.access')

    def make_response(self, result):
        response = self.responseFactory(app_iter=result)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = "%s" % (
            'attachment; filename="gutschein.pdf"'
        )
        return response

    def render(self):
        doc = SimpleDocTemplate(NamedTemporaryFile(), pagesize=letter)
        parts = []
        principal = self.request.principal
        for voucher in principal.getVouchers():
            parts.append(Paragraph(u"Ihre Gutscheine", styles['Heading1']))
            parts.append(Paragraph(printAddress(principal), styles['Normal']))
            parts.append(Paragraph(printVoucher(voucher), styles['Normal']))
            parts.append(I2of5(voucher.oid, barWidth=inch * 0.02, checksum=0))
            parts.append(PageBreak())

        doc.build(parts)
        pdf = doc.filename
        pdf.seek(0)
        return pdf.read()
