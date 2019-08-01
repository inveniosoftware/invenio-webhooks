# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Create webhooks branch."""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '469925575192'
down_revision = '12a88921ada2'
branch_labels = (u'invenio_webhooks',)
depends_on = 'dbdbc1b19cf2'


def upgrade():
    """Upgrade database."""
    pass


def downgrade():
    """Downgrade database."""
    pass
