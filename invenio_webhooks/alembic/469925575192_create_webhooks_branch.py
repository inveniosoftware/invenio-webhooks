# SPDX-FileCopyrightText: 2016 CERN.
# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Create webhooks branch."""

# revision identifiers, used by Alembic.
revision = "469925575192"
down_revision = None
branch_labels = ("invenio_webhooks",)
depends_on = [
    # invenipo-db
    "dbdbc1b19cf2",
    # invenio_oauth2server/alembic/12a88921ada2_create_oauth2server_tables.py
    "12a88921ada2",
]


def upgrade():
    """Upgrade database."""


def downgrade():
    """Downgrade database."""
