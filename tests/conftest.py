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


"""Pytest configuration."""

from __future__ import absolute_import, print_function

import os

import pytest
from celery import shared_task
from flask import Flask
from flask_babelex import Babel
from flask_breadcrumbs import Breadcrumbs
from flask_celeryext import FlaskCeleryExt
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
from invenio_webhooks.receivers import CeleryChainTaskReceiver, \
    CeleryTaskReceiver
from invenio_webhooks.views import blueprint


@pytest.fixture
def app(request):
    """Flask application fixture."""
    app = Flask('testapp')
    app.config.update(
        TESTING=True,
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND='memory',
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND='cache',
        BROKER_TRANSPORT='redis',
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
        SECURITY_DEPRECATED_PASSWORD_SCHEMES=[],
    )
    celeryext = FlaskCeleryExt(app)
    celeryext.celery.flask_app = app  # Make sure both apps are the same!
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
    app.register_blueprint(blueprint)

    with app.app_context():
        db.create_all()

    def teardown():
        with app.app_context():
            db.drop_all()

    request.addfinalizer(teardown)
    return app


@pytest.fixture
def tester_id(app):
    """Fixture that contains the test data for models tests."""
    with app.app_context():
        datastore = app.extensions['security'].datastore
        tester = datastore.create_user(
            email='info@inveniosoftware.org', password='tester',
        )
        db.session.commit()
        tester_id = tester.id
    return tester_id


@pytest.fixture
def access_token(app, tester_id):
    """Fixture that create an access token."""
    with app.app_context():
        token = Token.create_personal(
            'test-personal-{0}'.format(tester_id),
            tester_id,
            scopes=['webhooks:event'],
            is_internal=True,
        ).access_token
        db.session.commit()
        return token


@pytest.fixture
def access_token_no_scope(app, tester_id):
    """Fixture that create an access token without scope."""
    with app.app_context():
        token = Token.create_personal(
            'test-personal-{0}'.format(tester_id),
            tester_id,
            scopes=[''],
            is_internal=True,
        ).access_token
        db.session.commit()
        return token


@pytest.fixture
def receiver(app):
    """Register test receiver."""
    class TestReceiver(Receiver):

        def __init__(self, *args, **kwargs):
            super(TestReceiver, self).__init__(*args, **kwargs)
            self.calls = []

        def run(self, event):
            self.calls.append(event)

    app.extensions['invenio-webhooks'].register('test-receiver', TestReceiver)
    return TestReceiver


@pytest.fixture
def task_receiver(app):
    """Register test celery task receiver."""

    @shared_task
    def add(x, y):
        TestCeleryTaskReceiver.result = x + y
        return x + y

    class TestCeleryTaskReceiver(CeleryTaskReceiver):
        """Test receiver that executes an addition as a Celery """
        celery_task = add
        result = None

    app.extensions['invenio-webhooks'].register('test-task-receiver',
                                                TestCeleryTaskReceiver)
    return TestCeleryTaskReceiver


@pytest.fixture
def chain_task_receiver(app):
    """Register test celery chain task receiver."""

    @shared_task
    def init(initial_value, parent_id):
        return initial_value

    @shared_task
    def mul1(value, multiplicand1, parent_id):
        return value * multiplicand1

    @shared_task
    def mul2(value, multiplicand2, parent_id):
        return value * multiplicand2

    @shared_task
    def final(values, parent_id):
        TestCeleryChainTaskReceiver.result = values[0] + values[1]
        return values[0] + values[1]

    class TestCeleryChainTaskReceiver(CeleryChainTaskReceiver):
        """Test receiver that executes a celery chain."""
        result = None
        celery_tasks = [
            (init, {'initial_value'}),
            [
                (mul1, {'multiplicand1'}),
                (mul2, {'multiplicand2'})
            ],
            (final, {})
        ]

    app.extensions['invenio-webhooks'].register(
        'test-chain-task-receiver', TestCeleryChainTaskReceiver
    )
    return TestCeleryChainTaskReceiver
