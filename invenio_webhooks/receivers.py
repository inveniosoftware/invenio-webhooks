# -*- coding: utf-8 -*-
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

"""Useful webhook receivers."""

from __future__ import absolute_import


from celery import chain, group, shared_task
from celery.result import AsyncResult
from invenio_db import db

from invenio_webhooks.models import Event, Receiver


@shared_task(ignore_results=True)
def process_event(event_id):
    """Process event in Celery."""
    with db.session.begin_nested():
        event = Event.query.get(event_id)
        event.receiver.run(event)  # call run directly to avoild circular calls
        db.session.add(event)
    db.session.commit()


class CeleryReceiver(Receiver):
    """Asynchronous receiver.

    Receiver which will fire a celery task to handle payload instead of running
    it synchronously during the request.
    """

    def __call__(self, event):
        """Fire a celery task."""
        process_event.apply_async(args=[event.id])


class TaskReceiver(Receiver):
    """Base class for task-based webhook receivers.

    This receiver runs a long-running task and keep track of its status.

    Payloads sent to this receivers must conform to the following form:

    {
        "action": "new_task" | "get_status" | "cancel_task"
        "task_id": <user-defined ID>
        "kwargs": {
            "arg1": value1
            "arg2": value2
                  .
                  .
                  .
            "argN": valueN
        }
    }

    """

    def run(self, event):
        """Run the requested action."""
        action = event.action
        task_id = event.payload['task_id']
        response = dict(message='Invalid action')

        if action == 'new_task':
            kwargs = event.payload['kwargs']
            tid = self.new_task(task_id, kwargs=kwargs)
            # assert tid == task_id
            response['message'] = 'Started task [{}]'.format(task_id)

        elif action == 'get_status':
            (state, meta) = self.get_status(task_id)
            response = dict(state=state, **meta)

        elif action == 'cancel_task':
            message = self.cancel_task(task_id)
            response['message'] = message

        event.response_code = 200
        event.response = response

    def new_task(self, task_id, kwargs):
        """Start executing task."""
        raise NotImplementedError

    def get_status(self, task_id):
        """Retrieve current status of task."""
        raise NotImplementedError

    def cancel_task(self, task_id):
        """Cancel execution of task."""
        raise NotImplementedError


class CeleryTaskReceiver(TaskReceiver):
    """Base class for Celery-based TaskReceivers.

    Implementing this class requires the definition of a single Celery task.

    .. note::

        Arguments of the task must match the ones of the task provided exactly.
    """

    @property
    def celery_task(self):
        """Celery task to be executed by this receiver."""
        raise NotImplementedError

    def new_task(self, task_id, kwargs):
        """Start asynchronous execution of Celery task."""
        return self.celery_task.apply_async(task_id=task_id, kwargs=kwargs).id

    def get_status(self, task_id):
        """Retrieve status of current task from the Celery backend."""
        result = AsyncResult(task_id)
        return result.state, result.info if result.state == 'PROGRESS' else {}

    def cancel_task(self, task_id):
        """Cancel execution of the Celery task."""
        AsyncResult(task_id).revoke(terminate=True)
        return 'Revoked task'


class CeleryChainTaskReceiver(TaskReceiver):
    """Base class for Celery-based chained TaskReceivers.

    Expressive power
    ================
    The canvas representing the workflow is limited to chains (i.e. in-order
    sequential execution) of tasks or groups of tasks (i.e. concurrent tasks).

    Implementation
    ==============
    Implementing this class requires the definition of the task workflow.
    The chain is represented as a list, whose elements' order is the order of
    execution.

    Each element of the chain can either be a Celery task or a list of tasks,
    representing a group to be executed concurrently.

    Argument handling
    =================
    Each task (even the ones inside groups) must be paired with the keyword
    arguments they must accept from the payload message.

    Moreover, each task should accept a `parent_id` argument, in order to be
    able to update the status of the parent task (i.e. the task that manages
    the whole workflow).
    """

    # List of tuples of the form (celery_task, argument identifiers)
    @property
    def celery_tasks(self):
        """The workflow definition."""
        raise NotImplementedError

    def new_task(self, task_id, kwargs):
        """Chain sequential tasks and group concurrent ones."""
        task_list = []
        parent_kw = {'parent_id': task_id}
        for task_definition in self.celery_tasks:
            if isinstance(task_definition, tuple):
                task, task_kw = task_definition
                kw = {k: kwargs[k] for k in kwargs if k in task_kw}
                kw.update(parent_kw)
                task_list.append(task.subtask(kwargs=kw))
            elif isinstance(task_definition, list):
                subtasks = []
                for task, task_kw in task_definition:
                    kw = {k: kwargs[k] for k in kwargs if k in task_kw}
                    kw.update(parent_kw)
                    subtasks.append(task.subtask(kwargs=kw))
                task_list.append(group(*subtasks))
        return chain(*task_list, task_id=task_id)().id

    def get_status(self, task_id):
        """Retrieve statuses of all currently-executing Celery task."""
        result = AsyncResult(task_id)
        return result.state, result.info if result.state == 'PROGRESS' else {}

    def cancel_task(self, task_id):
        """Cancel execution of the workflow."""
        AsyncResult(task_id).revoke(terminate=True)
        return 'Revoked task'
