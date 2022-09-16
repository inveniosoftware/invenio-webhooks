#
# This file is part of Invenio.
# Copyright (C) 2016 CERN.
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

"""Create webhooks tables."""

import sqlalchemy as sa
import sqlalchemy_utils
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "a095bd179f5c"
down_revision = "469925575192"
branch_labels = ()
depends_on = "9848d0149abd"


def upgrade():
    """Upgrade database."""

    def json_column(name, **kwargs):
        """Return JSON column."""
        return sa.Column(
            name,
            sqlalchemy_utils.types.JSONType().with_variant(
                postgresql.JSON(none_as_null=True),
                "postgresql",
            ),
            **kwargs
        )

    op.create_table(
        "webhooks_events",
        sa.Column("created", sa.DateTime(), nullable=False),
        sa.Column("updated", sa.DateTime(), nullable=False),
        sa.Column("id", sqlalchemy_utils.types.uuid.UUIDType(), nullable=False),
        sa.Column("receiver_id", sa.String(length=255), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        json_column("payload", nullable=True),
        json_column("payload_headers", nullable=True),
        json_column("response", nullable=True),
        json_column("response_headers", nullable=True),
        sa.Column("response_code", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["accounts_user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_webhooks_events_receiver_id"),
        "webhooks_events",
        ["receiver_id"],
        unique=False,
    )


def downgrade():
    """Downgrade database."""
    op.drop_index(op.f("ix_webhooks_events_receiver_id"), table_name="webhooks_events")
    op.drop_table("webhooks_events")
