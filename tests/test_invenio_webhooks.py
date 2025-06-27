# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015 CERN.
# Copyright (C) 2025 Graz University of Technology.
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
