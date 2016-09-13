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
import uuid

import pytest

from invenio_webhooks.models import Event
from invenio_webhooks.receivers import CeleryChainTaskReceiver, \
    CeleryTaskReceiver, TaskReceiver


def send_request(app, payload, action, receiver_id):
    """Send given payload to receiver."""
    headers = [('Content-Type', 'application/json')]
    with app.test_request_context(headers=headers, data=payload):
        event = Event.create(receiver_id=receiver_id, action=action)
        event.process()
        return event.response_code, event.response


def send_new_task(app, task_id, kwargs, receiver_id):
    """Send a new_task action to task receiver."""
    payload = json.dumps(dict(
        task_id=task_id,
        kwargs=kwargs
    ))
    code, resp = send_request(app, payload, 'new_task', receiver_id)
    assert code == 200
    assert task_id in resp['message']


def send_get_status(app, task_id, receiver_id):
    """Send a get_status action to task receiver."""
    payload = json.dumps(dict(
        action='get_status',
        task_id=str(task_id),
    ))
    code, resp = send_request(app, payload, 'get_status', receiver_id)
    assert code == 200
    assert 'state' in resp
    return resp


def send_cancel_task(app, task_id, receiver_id):
    """Send a cancel_task action to task receiver."""
    payload = json.dumps(dict(
        action='cancel_task',
        task_id=str(task_id),
    ))
    code, resp = send_request(app, payload, 'cancel_task', receiver_id)
    assert code == 200
    assert resp['message'] == 'Revoked task'


def test_celery_task_receiver(app, task_receiver):
    """Test CeleryTaskReceiver."""
    task_id = str(uuid.uuid4())
    receiver_id = 'test-task-receiver'

    send_new_task(app, task_id, {'x': 10, 'y': 3}, receiver_id)
    assert task_receiver.result == 13
    send_get_status(app, task_id, receiver_id)
    send_cancel_task(app, task_id, receiver_id)


def test_celery_chain_task_receiver(app, chain_task_receiver):
    """Test CeleryChainTaskReceiver."""
    task_id = str(uuid.uuid4())
    receiver_id = 'test-chain-task-receiver'

    kwargs = {'initial_value': 10, 'multiplicand1': 2, 'multiplicand2': 10}
    send_new_task(app, task_id, kwargs, receiver_id)
    assert chain_task_receiver.result == 120
    send_get_status(app, task_id, receiver_id)
    send_cancel_task(app, task_id, receiver_id)
    pass


def test_improper_implementations():
    """Test improper implementations of TaskReceiver."""
    receiver_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    class InvalidReceiver(TaskReceiver):
        """Task receiver with incomplete implementation."""
        pass

    with pytest.raises(NotImplementedError):
        InvalidReceiver(receiver_id).new_task(task_id, {})
    with pytest.raises(NotImplementedError):
        InvalidReceiver(receiver_id).get_status(task_id)
    with pytest.raises(NotImplementedError):
        InvalidReceiver(receiver_id).cancel_task(task_id)

    class InvalidCeleryReceiver(CeleryTaskReceiver):
        """Celery receiver with incomplete implementation."""
        pass

    with pytest.raises(NotImplementedError):
        InvalidCeleryReceiver(receiver_id).celery_task()

    class InvalidChainReceiver(CeleryChainTaskReceiver):
        """Chain task receiver with incomplete implementation."""
        pass

    with pytest.raises(NotImplementedError):
        InvalidChainReceiver(receiver_id).celery_tasks()
