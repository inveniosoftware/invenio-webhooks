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

"""Replace JSON columns with JSONB."""

from alembic import op
import sqlalchemy_utils
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import JSON
from sqlalchemy_utils.types import JSONType


# revision identifiers, used by Alembic.
revision = 'ab9601b524f2'
down_revision = 'a095bd179f5c'
branch_labels = ()
depends_on = None


def existing_json_column():
    """Return JSON column."""
    return sqlalchemy_utils.types.JSONType().with_variant(
        postgresql.JSON(none_as_null=True), 'postgresql',
    )


def _json_column():
    """Return JSON column."""
    return JSON().with_variant(
        postgresql.JSONB(none_as_null=True), 'postgresql'
    ).with_variant(JSONType(), 'sqlite')


def upgrade():
    """Upgrade database."""
    op.alter_column(table_name='webhooks_events', column_name='payload',
                    nullable=True, existing_nullable=True,
                    existing_server_default=None,
                    type_=_json_column(), postgresql_using='payload::jsonb',
                    existing_type=existing_json_column())
    op.alter_column(table_name='webhooks_events',
                    column_name='payload_headers',
                    nullable=True, existing_nullable=True,
                    existing_server_default=None,
                    type_=_json_column(),
                    postgresql_using='payload_headers::jsonb',
                    existing_type=existing_json_column())
    op.alter_column(table_name='webhooks_events', column_name='response',
                    nullable=True, existing_nullable=True,
                    type_=_json_column(), postgresql_using='response::jsonb',
                    existing_type=existing_json_column())
    op.alter_column(table_name='webhooks_events',
                    column_name='response_headers',
                    nullable=True, existing_nullable=True,
                    existing_server_default=None,
                    type_=_json_column(),
                    postgresql_using='response_headers::jsonb',
                    existing_type=existing_json_column())


def downgrade():
    """Downgrade database."""
    op.alter_column(table_name='webhooks_events', column_name='payload',
                    nullable=True, existing_nullable=True,
                    existing_server_default=None,
                    type_=existing_json_column(),
                    postgresql_using='payload::json',
                    existing_type=_json_column())
    op.alter_column(table_name='webhooks_events',
                    column_name='payload_headers',
                    nullable=True, existing_nullable=True,
                    existing_server_default=None,
                    type_=existing_json_column(),
                    postgresql_using='payload_headers::json',
                    existing_type=_json_column())
    op.alter_column(table_name='webhooks_events', column_name='response',
                    nullable=True, existing_nullable=True,
                    type_=existing_json_column(),
                    existing_type=_json_column(),
                    postgresql_using='response::json')
    op.alter_column(table_name='webhooks_events',
                    column_name='response_headers',
                    nullable=True, existing_nullable=True,
                    existing_server_default=None,
                    type_=existing_json_column(),
                    postgresql_using='response_headers::json',
                    existing_type=_json_column())
