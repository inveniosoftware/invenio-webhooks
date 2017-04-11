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
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

from invenio_webhooks import InvenioWebhooks
from invenio_webhooks.models import Receiver
from invenio_webhooks.views import blueprint


@pytest.fixture
def app(request):
    """Flask application fixture."""
    app = Flask('testapp')
    app.config.update(
        BROKER_TRANSPORT='redis',
        CELERY_ALWAYS_EAGER=True,
        CELERY_CACHE_BACKEND='memory',
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        CELERY_RESULT_BACKEND='cache',
        CELERY_TRACK_STARTED=True,
        LOGIN_DISABLED=False,
        OAUTH2_CACHE_TYPE='simple',
        OAUTHLIB_INSECURE_TRANSPORT=True,
        SECRET_KEY='test_key',
        SECURITY_DEPRECATED_PASSWORD_SCHEMES=[],
        SECURITY_PASSWORD_HASH='plaintext',
        SECURITY_PASSWORD_SCHEMES=['plaintext'],
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        SQLALCHEMY_DATABASE_URI=os.getenv('SQLALCHEMY_DATABASE_URI',
                                          'sqlite:///test.db'),
        TESTING=True,
        WTF_CSRF_ENABLED=False,
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
        if not database_exists(str(db.engine.url)):
            create_database(str(db.engine.url))
        db.create_all()

    def teardown():
        with app.app_context():
            drop_database(str(db.engine.url))

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
def restricted_receiver(app):
    """Register test receiver with permissions."""
    class RestrictedReceiver(Receiver):
        """Permits operations based on boolean flags on event's payload."""

        def __init__(self, *args, **kwargs):
            super(RestrictedReceiver, self).__init__(*args, **kwargs)
            self.calls = []

        def run(self, event):
            event.response = {'status': 202, 'message': 'Accepted.'}
            event.response_code = 202
            self.calls.append(event)

        @staticmethod
        def can_create(user_id, **kwargs):
            return Receiver.can_create(user_id)

        @staticmethod
        def can_read(user_id, event, **kwargs):
            return event.payload.get('read')

        @staticmethod
        def can_update(user_id, event, **kwargs):
            return event.payload.get('update')

        @staticmethod
        def can_delete(user_id, event, **kwargs):
            return event.payload.get('delete')

    app.extensions['invenio-webhooks'].register('restricted-receiver',
                                                RestrictedReceiver)
    return app.extensions['invenio-webhooks'].receivers['restricted-receiver']
