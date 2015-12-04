# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
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


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os

import pytest
from flask import Flask
from flask_babelex import Babel
from flask_breadcrumbs import Breadcrumbs
from flask_celeryext import FlaskCeleryExt
from flask_cli import FlaskCLI
from flask_mail import Mail
from flask_menu import Menu
from invenio_accounts import InvenioAccounts
from invenio_accounts.views import blueprint as accounts_blueprint
from invenio_db import InvenioDB, db
from invenio_oauth2server import InvenioOAuth2Server
from invenio_oauth2server.models import Token
from invenio_oauth2server.views import server_blueprint, settings_blueprint

from invenio_webhooks import InvenioWebhooks
from invenio_webhooks.models import Receiver


@pytest.fixture()
def app(request):
    """Flask application fixture."""
    app = Flask('testapp')
    app.config.update(
        TESTING=True,
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND="memory",
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND="cache",
        LOGIN_DISABLED=False,
        SECRET_KEY='test_key',
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                          'sqlite:///test.db'),
        WTF_CSRF_ENABLED=False,
        OAUTHLIB_INSECURE_TRANSPORT=True,
        OAUTH2_CACHE_TYPE='simple',
        SECURITY_PASSWORD_HASH='plaintext',
        SECURITY_PASSWORD_SCHEMES=['plaintext'],
    )
    FlaskCLI(app)
    FlaskCeleryExt(app)
    Babel(app)
    Mail(app)
    Menu(app)
    Breadcrumbs(app)
    InvenioDB(app)
    InvenioAccounts(app)
    app.register_blueprint(accounts_blueprint)
    InvenioOAuth2Server(app)
    app.register_blueprint(server_blueprint)
    app.register_blueprint(settings_blueprint)
    InvenioWebhooks(app)

    with app.app_context():
        db.create_all()

    def teardown():
        with app.app_context():
            db.drop_all()

    request.addfinalizer(teardown)
    return app


@pytest.fixture
def tester(app):
    """Fixture that contains the test data for models tests."""
    with app.app_context():
        datastore = app.extensions['security'].datastore
        with db.session.begin_nested():
            tester = datastore.create_user(
                email='info@invenio-software.org', password='tester',
            )
    return tester


@pytest.fixture
def access_token(app, tester):
    with app.app_context():
        return Token.create_personal(
            'test-personal-{0}'.format(tester.id),
            tester.id,
            scopes=['webhooks:event'],
            is_internal=True,
        ).access_token


@pytest.fixture
def access_token_no_scope(app, tester):
    with app.app_context():
        return Token.create_personal(
            'test-personal-{0}'.format(tester.id),
            tester.id,
            scopes=[''],
            is_internal=True,
        ).access_token


@pytest.fixture()
def receiver(app):
    """Register test receiver."""
    calls = []

    def consumer(event):
        calls.append(event)

    test_receiver = Receiver(consumer)
    test_receiver.calls = calls

    with app.app_context():
        Receiver.register('test-receiver', test_receiver)

    return test_receiver
