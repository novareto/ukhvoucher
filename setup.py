from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(name='ukhvoucher',
      version=version,
      description="",
      long_description=""" """,
      classifiers=[],
      keywords='',
      author='',
      author_email='',
      url='',
      license='',
      packages=find_packages('src'),
      package_dir = {'': 'src'},
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          "GenericCache",
          "PyCrypto",
          "cromlech.sessions.jwt",
          "cromlech.sqlalchemy",
          "docxtpl",
          "dogpile.cache",
          "dolmen.batch",
          "dolmen.sqlcontainer",
          "infrae.testbrowser",
          "js.jquery_tablesorter",
          "natsort",
          "ordered_set",
          "plone.memoize",
          "profilehooks",
          "profilehooks",
          #"psycopg2-binary",
          "pycrypto",
          "python-gettext",
          "reportlab",
          "ukh.ibmdbsa",
          "ukhtheme.uvclight",
          "ul.auth",
          "ul.auth",
          "ul.sql",
          "uvc.validation",
          "uvclight",
          "webhelpers",
          "xlsxwriter",
          "zope.sendmail",
      ],
      entry_points={
         'fanstatic.libraries': [
            'ukhvoucher = ukhvoucher.resources:library',
         ],
         'paste.app_factory': [
             'app = ukhvoucher.wsgi:router',
         ],
        'pytest11': [
            'ukhvoucher_fixtures = ukhvoucher.tests.fixtures',
        ]
      }
      )
