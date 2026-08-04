# SPDX-FileCopyrightText: 2015-2020 CERN.
# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Alembic upgrade tests."""

import pytest
from invenio_db import db


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

        #
        # Can not perform downgrade test because alembic has a curious behaviour/bug:
        # if the revision id looks like a number, it is treated as a number of steps
        # to perform and not as a revision id. So this downgrade would like to downgrade
        # by a billion of steps which would fail.
        #
        # ext.alembic.downgrade(target="469925575192")
        # ext.alembic.upgrade()

        # assert not ext.alembic.compare_metadata()
