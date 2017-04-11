# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2016 CERN.
#
# Invenio is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Invenio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Invenio; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

from __future__ import absolute_import

import pytest
from flask import json, url_for
from invenio_accounts.testutils import login_user_via_session


def login(app, client, user_id):
    """Login user via session."""
    ds = app.extensions['security'].datastore
    user = ds.get_user(user_id)
    login_user_via_session(client, user)


def create_event(client, status_code=202, **payload):
    """Create event and return event URL."""
    response = client.post(
        url_for('invenio_webhooks.event_list',
                receiver_id='restricted-receiver',),
        headers=[('Content-Type', 'application/json')],
        data=json.dumps(payload),
    )
    assert response.status_code == status_code
    return response.headers['Link'][1:-13]


@pytest.mark.parametrize('calls, method, status_code, payload', [
    (1, None, None, {}),
    (1, 'get', 202, {'read': True}),
    (1, 'get', 403, {}),
    (2, 'put', 202, {'update': True}),
    (1, 'delete', 410, {'delete': True}),
])
def test_permissions(app, tester_id, restricted_receiver, calls, method,
                     status_code, payload):
    """Test permissions for webhook receivers."""
    with app.test_request_context():
        with app.test_client() as client:
            login(app, client, tester_id)
            event_url = create_event(client, **payload)
            if method:
                client_func = getattr(client, method)
                assert client_func(event_url).status_code == status_code
            assert len(restricted_receiver.calls) == calls
