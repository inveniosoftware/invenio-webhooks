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

import json

from flask import url_for
from flask_login import current_user
from flask_security import url_for_security

from invenio_webhooks.models import Receiver
from invenio_webhooks.proxies import current_webhooks


def make_request(
    access_token,
    client_func,
    endpoint,
    urlargs=None,
    data=None,
    is_json=True,
    code=None,
    headers=None,
    follow_redirects=False,
):
    """Make a request to the API endpoint.

    Ensures request looks like they arrive on CFG_SITE_SECURE_URL.
    That header "Contet-Type: application/json" is added if the parameter
    is_json is True
    :param endpoint: Endpoint passed to url_for.
    :param urlargs: Keyword args passed to url_for
    :param data: Request body, either as a dictionary if ``is_json`` is
        True, or as a string if ``is_json`` is False
    :param headers: List of headers for the request
    :param code: Assert response status code
    :param follow_redirects: Whether to follow redirects.
    """
    urlargs = urlargs or {}
    urlargs["access_token"] = access_token

    if headers is None:
        headers = [("content-type", "application/json")] if is_json else []

    if data is not None:
        request_args = dict(
            data=json.dumps(data) if is_json else data,
            headers=headers,
        )
    else:
        request_args = {}

    url = url_for(endpoint, **urlargs)
    response = client_func(url, follow_redirects=follow_redirects, **request_args)

    if code is not None:
        assert code == response.status_code
    return response


def test_405_methods(app, tester_id, access_token):
    with app.test_request_context():
        with app.test_client() as client:
            methods = [
                client.get,
                client.put,
                client.delete,
                client.head,
                client.options,
                client.patch,
            ]

            for client_func in methods:
                make_request(
                    access_token,
                    client_func,
                    "invenio_webhooks.event_list",
                    urlargs=dict(receiver_id="test-receiver"),
                    code=405,
                )


def test_webhook_post_unregistered(app, tester_id, access_token):
    with app.test_request_context():
        with app.test_client() as client:
            make_request(
                access_token,
                client.post,
                "invenio_webhooks.event_list",
                urlargs=dict(receiver_id="test-receiver"),
                code=404,
            )


def test_webhook_post(app, tester_id, access_token, receiver):
    with app.test_request_context():
        receiver = current_webhooks.receivers["test-receiver"]
        with app.test_client() as client:
            payload = dict(somekey="somevalue")
            make_request(
                access_token,
                client.post,
                "invenio_webhooks.event_list",
                urlargs=dict(receiver_id="test-receiver"),
                data=payload,
                code=202,
            )

            assert 1 == len(receiver.calls)
            assert tester_id == receiver.calls[0].user_id
            assert payload == receiver.calls[0].payload

            # Test invalid payload
            import pickle

            payload = dict(somekey="somevalue")
            make_request(
                access_token,
                client.post,
                "invenio_webhooks.event_list",
                urlargs=dict(receiver_id="test-receiver"),
                data=pickle.dumps(payload),
                is_json=False,
                headers=[("Content-Type", "application/python-pickle")],
                code=415,
            )

            # Test invalid payload, with wrong content-type
            make_request(
                access_token,
                client.post,
                "invenio_webhooks.event_list",
                urlargs=dict(receiver_id="test-receiver"),
                data=pickle.dumps(payload),
                is_json=False,
                headers=[("Content-Type", "application/json")],
                code=400,
            )


def test_webhook_post_no_token(app, tester_id, receiver):
    ds = app.extensions["security"].datastore

    with app.test_request_context():
        user = ds.get_user(tester_id)
        with app.test_client() as client:
            # Manual login via view
            response = client.post(
                url_for_security("login"),
                data={"email": user.email, "password": user.password},
                environ_base={"REMOTE_ADDR": "127.0.0.1"},
            )

            assert response.status_code == 302
            assert user.get_id() == current_user.get_id()

            payload = dict(somekey="somevalue")
            response = make_request(
                None,
                client.post,
                "invenio_webhooks.event_list",
                urlargs=dict(receiver_id="test-receiver"),
                data=payload,
                code=202,
            )

            make_request(
                None,
                client.get,
                "invenio_webhooks.event_item",
                urlargs=dict(
                    receiver_id=response.headers["X-Hub-Event"],
                    event_id=response.headers["X-Hub-Delivery"],
                ),
                data=payload,
                code=202,
            )


def test_405_methods_no_scope(app, tester_id, access_token_no_scope):
    with app.test_request_context():
        with app.test_client() as client:
            methods = [
                client.get,
                client.put,
                client.delete,
                client.head,
                client.options,
                client.patch,
            ]

            for client_func in methods:
                make_request(
                    access_token_no_scope,
                    client_func,
                    "invenio_webhooks.event_list",
                    urlargs=dict(receiver_id="test-receiver"),
                    code=405,
                )


def test_webhook_post_no_scope(app, tester_id, access_token_no_scope):
    class TestReceiverNoScope(Receiver):
        def __call__(self, event):
            return event

    with app.test_request_context():
        current_webhooks.register("test-receiver-no-scope", TestReceiverNoScope)

        with app.test_client() as client:
            payload = dict(somekey="somevalue")
            make_request(
                access_token_no_scope,
                client.post,
                "invenio_webhooks.event_list",
                urlargs=dict(receiver_id="test-receiver-no-scope"),
                data=payload,
                code=403,
            )


def test_event_api(app, tester_id, access_token, receiver):
    with app.test_request_context():
        receiver = current_webhooks.receivers["test-receiver"]
        with app.test_client() as client:
            payload = dict(somekey="somevalue")
            response = make_request(
                access_token,
                client.post,
                "invenio_webhooks.event_list",
                urlargs=dict(receiver_id="test-receiver"),
                data=payload,
                code=202,
            )

            # Check if the event exists.
            make_request(
                access_token,
                client.head,
                "invenio_webhooks.event_item",
                urlargs=dict(
                    receiver_id=response.headers["X-Hub-Event"],
                    event_id=response.headers["X-Hub-Delivery"],
                ),
                data=payload,
                code=202,
            )
            make_request(
                access_token,
                client.get,
                "invenio_webhooks.event_item",
                urlargs=dict(
                    receiver_id=response.headers["X-Hub-Event"],
                    event_id=response.headers["X-Hub-Delivery"],
                ),
                data=payload,
                code=202,
            )

            # Delete event.
            make_request(
                access_token,
                client.delete,
                "invenio_webhooks.event_item",
                urlargs=dict(
                    receiver_id=response.headers["X-Hub-Event"],
                    event_id=response.headers["X-Hub-Delivery"],
                ),
                data=payload,
            )

            # Check that event was deleted.
            make_request(
                access_token,
                client.get,
                "invenio_webhooks.event_item",
                urlargs=dict(
                    receiver_id=response.headers["X-Hub-Event"],
                    event_id=response.headers["X-Hub-Delivery"],
                ),
                data=payload,
                code=410,
            )
