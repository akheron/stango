#!/usr/bin/python

from distutils.core import setup

setup(
    name='stango',
    version='0.1',
    author='Petri Lehtinen',
    author_email='petri@digip.org',
    url='http://www.digip.org/stango/',
    description='Static web site generator for Python programmers',
    long_description='''Stango is a Pythonic static web site generator
that feels like a web framework. User defined view functions generate
the content to pages (e.g. using Jinja2 templates or any other means).
During development, the pages are served locally using a built-in web
server with all URLs working. When they site is ready, it is rendered
to flat files and can be pushed to a production server.''',
    license='MIT',
    package_dir={'': 'lib'},
    packages=['stango', 'stango.manage'],
)
