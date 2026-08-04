# SPDX-FileCopyrightText: 2015 CERN.
# SPDX-FileCopyrightText: 2025 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Module tests."""

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
    app = Flask("testapp")
    ext = InvenioWebhooks(app)
    assert "invenio-webhooks" in app.extensions

    app = Flask("testapp")
    ext = InvenioWebhooks()
    assert "invenio-webhooks" not in app.extensions
    ext.init_app(app)
    assert "invenio-webhooks" in app.extensions


@pytest.mark.skip("caused by missing key")
def test_alembic(app):
    """Test alembic recipes."""
    ext = app.extensions["invenio-db"]

    with app.app_context():
        if db.engine.name == "sqlite":
            raise pytest.skip("Upgrades are not supported on SQLite.")

        assert not ext.alembic.compare_metadata()
        db.drop_all()
        ext.alembic.upgrade()

        assert not ext.alembic.compare_metadata()
        ext.alembic.downgrade(target="96e796392533")
        ext.alembic.upgrade()

        assert not ext.alembic.compare_metadata()


def test_view(app, receiver):
    """Test view."""
    with app.test_request_context():
        view_url = url_for("invenio_webhooks.event_list", receiver_id="test_receiver")

    with app.test_client() as client:
        res = client.get(view_url)
        assert res.status_code == 405

        res = client.post(view_url)
        assert res.status_code == 401
