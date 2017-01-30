# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2017 CERN.
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

"""Useful decorators for checking permission."""

from __future__ import absolute_import, print_function

from functools import wraps

from flask import request
from flask_login import current_user
from werkzeug.exceptions import abort

from invenio_webhooks import current_webhooks
from invenio_webhooks.errors import ReceiverDoesNotExist
from invenio_webhooks.models import Event


def pass_user_id(f):
    """Decorator to retrieve user ID."""
    @wraps(f)
    def inner(self, receiver_id=None, *args, **kwargs):
        try:
            user_id = request.oauth.access_token.user_id
        except AttributeError:
            user_id = current_user.get_id()

        kwargs.update(receiver_id=receiver_id, user_id=user_id)
        return f(self, *args, **kwargs)
    return inner


def pass_event(f):
    """Decorator to retrieve event."""
    @wraps(f)
    def inner(self, receiver_id=None, event_id=None, *args, **kwargs):
        event = Event.query.filter_by(
            receiver_id=receiver_id, id=event_id
        ).first_or_404()

        kwargs.update(receiver_id=receiver_id, event=event)
        return f(self, *args, **kwargs)
    return inner


def need_receiver_permission(action_name):
    """Decorator for actions on receivers.

    :param action_name: name of the action to perform.
    """
    def need_receiver_permission_builder(f):
        @wraps(f)
        def need_receiver_permission_decorator(self, receiver_id=None,
                                               user_id=None, *args, **kwargs):
            # Get receiver for given receiver ID
            try:
                receiver = current_webhooks.receivers[receiver_id]
            except KeyError:
                raise ReceiverDoesNotExist(receiver_id)

            # Get event (if it exists)
            event = kwargs.get('event')

            # Get receiver's permission method for given action
            can_method = getattr(receiver, 'can_{0}'.format(action_name))

            # Check if user can perform requested action
            if not can_method(user_id, event=event):
                abort(403)

            # Update keyword arguments
            kwargs.update(receiver_id=receiver_id, user_id=user_id)
            if event is not None:
                kwargs.update(event=event)

            return f(self, *args, **kwargs)
        return need_receiver_permission_decorator
    return need_receiver_permission_builder
