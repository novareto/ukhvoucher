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
          "cromlech.sqlalchemy",
          "dolmen.batch",
          "infrae.testbrowser",
          "plone.memoize",
          "reportlab",
          "pycrypto",
          "ukh.ibmdbsa",
          "ukhtheme.uvclight",
          "profilehooks",
          "webhelpers",
          "ul.auth",
          "ordered_set",
          "natsort",
          "js.jquery_tablesorter",
          "xlsxwriter",
          "PyCrypto",
          "python-gettext",
          "zope.sendmail",
          "GenericCache",
          "profilehooks",
          "dogpile.cache",
          "uvc.validation",
          "docxtpl",
          "psycopg2",
          "cromlech.sessions.jwt"
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
