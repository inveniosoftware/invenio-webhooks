# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Module tests."""

from __future__ import absolute_import, print_function

import pytest
from flask import Flask, url_for
from invenio_db import db

from invenio_webhooks import InvenioWebhooks


def test_version():
    """Test version import."""
    from invenio_webhooks import __version__
    assert __version__


def test_init():
    """Test extension initialization."""
    app = Flask('testapp')
    ext = InvenioWebhooks(app)
    assert 'invenio-webhooks' in app.extensions

    app = Flask('testapp')
    ext = InvenioWebhooks()
    assert 'invenio-webhooks' not in app.extensions
    ext.init_app(app)
    assert 'invenio-webhooks' in app.extensions


def test_alembic(app):
    """Test alembic recipes."""
    ext = app.extensions['invenio-db']

    with app.app_context():
        if db.engine.name == 'sqlite':
            raise pytest.skip('Upgrades are not supported on SQLite.')

        assert not ext.alembic.compare_metadata()
        db.drop_all()
        ext.alembic.upgrade()

        assert not ext.alembic.compare_metadata()
        ext.alembic.downgrade(target='96e796392533')
        ext.alembic.upgrade()

        assert not ext.alembic.compare_metadata()


def test_view(app):
    """Test view."""
    with app.test_request_context():
        view_url = url_for('invenio_webhooks.event_list',
                           receiver_id='test_receiver')

    with app.test_client() as client:
        res = client.get(view_url)
        assert res.status_code == 405

        res = client.post(view_url)
        assert res.status_code == 401
