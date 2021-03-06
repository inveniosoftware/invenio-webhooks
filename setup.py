# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015, 2016 CERN.
#
# Invenio is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston,
# MA 02111-1307, USA.
#
# In applying this license, CERN does not
# waive the privileges and immunities granted to it by virtue of its status
# as an Intergovernmental Organization or submit itself to any jurisdiction.

"""Invenio module for processing webhook events."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'Flask-CeleryExt>=0.3.4',
    'SQLAlchemy-Continuum>=1.2.1',
    'pytest-cache>=1.0',
    'pytest-invenio>=1.4.0',
    'iniconfig>=1.1.1',
]

extras_require = {
    'celery': [
        'celery>=5.0',
    ],
    'docs': [
        'Sphinx>=3',
    ],
    'mysql': [
        'invenio-db[mysql]>=1.0.8',
    ],
    'postgresql': [
        'invenio-db[postgresql]>=1.0.8',
    ],
    'sqlite': [
        'invenio-db>=1.0.8',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    if name in ('mysql', 'postgresql', 'sqlite'):
        continue
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=2.4.0',
    'pytest-runner>=3.0.0,<5',
]

install_requires = [
    'Flask-BabelEx>=0.9.4',
    'Flask>=1.0.4',
    'invenio-accounts>=1.4.1',
    'invenio-oauth2server>=1.2.0',
]

packages = find_packages()


# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_webhooks', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-webhooks',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio webhooks',
    license='GPLv2',
    author='CERN',
    author_email='info@inveniosoftware.org',
    url='https://github.com/inveniosoftware/invenio-webhooks',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'invenio_base.api_apps': [
            'invenio_webhooks = invenio_webhooks:InvenioWebhooks',
        ],
        'invenio_base.api_blueprints': [
            'invenio_webhooks = invenio_webhooks.views:blueprint',
        ],
        'invenio_base.models': [
            'invenio_webhooks = invenio_webhooks.models',
        ],
        'invenio_db.alembic': [
            'invenio_webhooks = invenio_webhooks:alembic',
        ],
        'invenio_db.models': [
            'invenio_webhooks = invenio_webhooks.models',
        ],
        'invenio_i18n.translations': [
            'messages = invenio_webhooks',
        ],
        'invenio_oauth2server.scopes': [
            'webhooks_event = invenio_webhooks.views:webhooks_event',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Development Status :: 1 - Planning',
    ],
)
