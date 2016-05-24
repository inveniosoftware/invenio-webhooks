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

import json

import pytest
from flask import url_for
from invenio_db import db

from invenio_webhooks.models import CeleryReceiver, Event, InvalidPayload, \
    InvalidSignature, ReceiverDoesNotExist
from invenio_webhooks.proxies import current_webhooks
from invenio_webhooks.signatures import get_hmac


def test_receiver_registration(app, receiver):
    with app.app_context():
        current_webhooks.register('test-invalid', receiver)

        assert 'test-receiver' in current_webhooks.receivers
        assert 'test-receiver' == current_webhooks.receivers[
            'test-receiver'].receiver_id

        # Double registration
        with pytest.raises(AssertionError):
            current_webhooks.register('test-receiver', receiver)

        current_webhooks.unregister('test-receiver')
        assert 'test-receiver' not in current_webhooks.receivers

        current_webhooks.register('test-receiver', receiver)

    # JSON payload parsing
    payload = json.dumps(dict(somekey='somevalue'))
    headers = [('Content-Type', 'application/json')]
    with app.test_request_context(headers=headers, data=payload):
        event = Event.create(receiver_id='test-receiver')
        event.process()
        assert 1 == len(event.receiver.calls)
        assert json.loads(payload) == event.receiver.calls[0].payload
        assert event.receiver.calls[0].user_id is None

    # Form encoded values payload parsing
    payload = dict(somekey='somevalue')
    with app.test_request_context(method='POST', data=payload):
        event = Event.create(receiver_id='test-receiver')
        event.process()
        assert 2 == len(event.receiver.calls)
        assert dict(somekey=['somevalue']) == event.receiver.calls[1].payload

    # Test invalid post data
    with app.test_request_context(method='POST', data="invaliddata"):
        with pytest.raises(InvalidPayload):
            event = Event.create(receiver_id='test-receiver')

    calls = []

    # Test Celery Receiver
    class TestCeleryReceiver(CeleryReceiver):

        def run(self, event):
            calls.append(event.payload)

    app.extensions['invenio-webhooks'].register('celery-receiver',
                                                TestCeleryReceiver)

    # Form encoded values payload parsing
    payload = dict(somekey='somevalue')
    with app.test_request_context(method='POST', data=payload):
        event = Event.create(receiver_id='celery-receiver')
        db.session.add(event)
        db.session.commit()
        event.process()
        assert 1 == len(calls)
        assert dict(somekey=['somevalue']) == calls[0]


def test_unknown_receiver(app):
    """Raise when receiver does not exist."""
    with app.app_context():
        with pytest.raises(ReceiverDoesNotExist):
            Event.create(receiver_id='unknown')


def test_hookurl(app, receiver):
    with app.test_request_context():
        assert current_webhooks.receivers['test-receiver'].get_hook_url(
            'token'
        ) == url_for(
            'invenio_webhooks.event_list',
            receiver_id='test-receiver',
            access_token='token',
            _external=True
        )

    app.config['WEBHOOKS_DEBUG_RECEIVER_URLS'] = {
        'test-receiver': 'http://test.local/?access_token=%(token)s'
    }

    with app.test_request_context():
        assert 'http://test.local/?access_token=token' == \
            current_webhooks.receivers['test-receiver'].get_hook_url(
                'token'
            )


def test_signature_checking(app, receiver):
    """Check signatures for payload."""
    class TestReceiverSign(receiver):
        signature = 'X-Hub-Signature'

    with app.app_context():
        current_webhooks.register('test-receiver-sign', TestReceiverSign)

    # check correct signature
    payload = json.dumps(dict(somekey='somevalue'))
    with app.app_context():
        headers = [('Content-Type', 'application/json'),
                   ('X-Hub-Signature', get_hmac(payload))]
    with app.test_request_context(headers=headers, data=payload):
        event = Event.create(receiver_id='test-receiver-sign')
        event.process()
        assert json.loads(payload) == event.receiver.calls[0].payload

    # check signature with prefix
    with app.app_context():
        headers = [('Content-Type', 'application/json'),
                   ('X-Hub-Signature', 'sha1=' + get_hmac(payload))]
    with app.test_request_context(headers=headers, data=payload):
        event = Event.create(receiver_id='test-receiver-sign')
        event.process()
        assert json.loads(payload) == event.receiver.calls[1].payload

    # check incorrect signature
    with app.app_context():
        headers = [('Content-Type', 'application/json'),
                   ('X-Hub-Signature', get_hmac("somevalue"))]
    with app.test_request_context(headers=headers, data=payload):
        with pytest.raises(InvalidSignature):
            Event.create(receiver_id='test-receiver-sign')
