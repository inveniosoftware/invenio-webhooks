# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio module for processing webhook events."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'Flask-CeleryExt>=0.2.2',
    'SQLAlchemy-Continuum>=1.2.1',
    'check-manifest>=0.35',
    'coverage>=4.4.1',
    'isort>=4.3',
    'pydocstyle>=2.0.0',
    'pytest-cov>=2.5.1',
    'pytest-pep8>=1.0.6',
    'pytest>=3.3.1',
]

extras_require = {
    'celery': [
        'celery>=3.1,<4.0',
    ],
    'docs': [
        'Sphinx>=1.5.2',
    ],
    'mysql': [
        'invenio-db[mysql]>=1.0.0b8',
    ],
    'postgresql': [
        'invenio-db[postgresql]>=1.0.0b8',
    ],
    'sqlite': [
        'invenio-db>=1.0.0b8',
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
    'Flask-BabelEx>=0.9.3',
    'Flask>=0.11.1',
    'invenio-accounts>=1.0.0b9',
    'invenio-oauth2server>=1.0.0b4',
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
    license='MIT',
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
        'License :: OSI Approved :: MIT License',
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
