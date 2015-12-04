# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014 CERN.
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
from celery import shared_task
from flask import url_for

from invenio_webhooks.models import CeleryReceiver, Event, InvalidPayload, \
    InvalidSignature, Receiver, ReceiverDoesNotExist
from invenio_webhooks.signatures import get_hmac


def test_receiver_registration(app):
    calls = []

    def consumer(event):
        calls.append(event)

    @shared_task(ignore_result=True)
    def task_callable(event_state):
        e = Event()
        e.__setstate__(event_state)
        calls.append(e)

    r = Receiver(consumer)
    r_invalid = Receiver(consumer)

    with app.app_context():
        Receiver.register('test-receiver', r)
        Receiver.register('test-invalid', r_invalid)

        assert 'test-receiver' in Receiver.all()
        assert Receiver.get('test-receiver') == r

        # Double registration
        with pytest.raises(AssertionError):
            Receiver.register('test-receiver', r)

        Receiver.unregister('test-receiver')
        assert 'test-receiver' not in Receiver.all()

        Receiver.register('test-receiver', r)

    # JSON payload parsing
    payload = json.dumps(dict(somekey='somevalue'))
    headers = [('Content-Type', 'application/json')]
    with app.test_request_context(headers=headers, data=payload):
        r.consume_event(2)
        assert 1 == len(calls)
        assert json.loads(payload) == calls[0].payload
        assert 2 == calls[0].user_id

        # NOTE legacy test with no clear reason.
        # with pytest.raises(TypeError):
        #     r_invalid.consume_event(2)
        # assert 1 == len(calls)

    # Form encoded values payload parsing
    payload = dict(somekey='somevalue')
    with app.test_request_context(method='POST', data=payload):
        r.consume_event(2)
        assert 2 == len(calls)
        assert dict(somekey=['somevalue']) == calls[1].payload

    # Test invalid post data
    with app.test_request_context(method='POST', data="invaliddata"):
        with pytest.raises(InvalidPayload):
            r.consume_event(2)

    # Test Celery Receiver
    rcelery = CeleryReceiver(task_callable)
    with app.app_context():
        CeleryReceiver.register('celery-receiver', rcelery)

    # Form encoded values payload parsing
    payload = dict(somekey='somevalue')
    with app.test_request_context(method='POST', data=payload):
        rcelery.consume_event(1)
        assert 3 == len(calls)
        assert dict(somekey=['somevalue']) == calls[2].payload
        assert 1 == calls[2].user_id


def test_unknown_receiver(app):
    """Raise when receiver does not exist."""
    with app.app_context():
        with pytest.raises(ReceiverDoesNotExist):
            Receiver.get('unknown')


def test_hookurl(app, receiver):
    with app.test_request_context():
        assert Receiver.get_hook_url('test-receiver', 'token') == url_for(
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
            Receiver.get_hook_url('test-receiver', 'token')


def test_signature_checking(app):
    """Check signatures for payload."""
    calls = []

    def consumer(event):
        calls.append(event)

    r = Receiver(consumer, signature='X-Hub-Signature')
    with app.app_context():
        Receiver.register('test-receiver-sign', r)

    # check correct signature
    payload = json.dumps(dict(somekey='somevalue'))
    with app.app_context():
        headers = [('Content-Type', 'application/json'),
                   ('X-Hub-Signature', get_hmac(payload))]
    with app.test_request_context(headers=headers, data=payload):
        r.consume_event(2)
        assert json.loads(payload) == calls[0].payload

    # check signature with prefix
    with app.app_context():
        headers = [('Content-Type', 'application/json'),
                   ('X-Hub-Signature', 'sha1=' + get_hmac(payload))]
    with app.test_request_context(headers=headers, data=payload):
        r.consume_event(2)
        assert json.loads(payload) == calls[1].payload

    # check incorrect signature
    with app.app_context():
        headers = [('Content-Type', 'application/json'),
                   ('X-Hub-Signature', get_hmac("somevalue"))]
    with app.test_request_context(headers=headers, data=payload):
        with pytest.raises(InvalidSignature):
            r.consume_event(2)
