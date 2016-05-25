# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015, 2016 CERN.
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

"""Models for webhook receivers."""

from __future__ import absolute_import

import re
import uuid

from celery import shared_task
from flask import current_app, request, url_for
from invenio_accounts.models import User
from invenio_db import db
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import validates
from sqlalchemy_utils.models import Timestamp
from sqlalchemy_utils.types import JSONType, UUIDType

from . import signatures
from .proxies import current_webhooks


#
# Errors
#
class WebhookError(Exception):
    """General webhook error."""


class ReceiverDoesNotExist(WebhookError):
    """Raised when receiver does not exist."""


class InvalidPayload(WebhookError):
    """Raised when the payload is invalid."""


class InvalidSignature(WebhookError):
    """Raised when the signature does not match."""


#
# Models
#
class Receiver(object):
    """Base class for a webhook receiver.

    A receiver is responsible for receiving and extracting a payload from a
    request. You must implement ``run`` method that accepts the event
    instance.
    """

    signature = ''
    """Default signature."""

    def __init__(self, receiver_id):
        """Initialize a receiver identifier."""
        self.receiver_id = receiver_id

    def __call__(self, event):
        """Proxy to ``self.run`` method."""
        return self.run(event)

    def run(self, event):
        """Implement method accepting the ``Event`` instance."""
        raise NotImplemented()

    def get_hook_url(self, access_token):
        """Get URL for webhook.

        In debug and testing mode the hook URL can be overwritten using
        ``WEBHOOKS_DEBUG_RECEIVER_URLS`` configuration variable to allow
        testing webhooks via services such as e.g. Ultrahook.

        .. code-block:: python

            WEBHOOKS_DEBUG_RECEIVER_URLS = dict(
                github='http://github.userid.ultrahook.com',
            )
        """
        # Allow overwriting hook URL in debug mode.
        if (current_app.debug or current_app.testing) and \
           current_app.config.get('WEBHOOKS_DEBUG_RECEIVER_URLS', None):
            url_pattern = current_app.config[
                'WEBHOOKS_DEBUG_RECEIVER_URLS'].get(self.receiver_id, None)
            if url_pattern:
                return url_pattern % dict(token=access_token)
        return url_for(
            'invenio_webhooks.event_list',
            receiver_id=self.receiver_id,
            access_token=access_token,
            _external=True
        )

    #
    # Instance methods (override if needed)
    #
    def check_signature(self):
        """Check signature of signed request."""
        if not self.signature:
            return True
        signature_value = request.headers.get(self.signature, None)
        if signature_value:
            validator = 'check_' + re.sub(r'[-]', '_', self.signature).lower()
            check_signature = getattr(signatures, validator)
            if check_signature(signature_value, request.data):
                return True
        return False

    def extract_payload(self):
        """Extract payload from request."""
        if not self.check_signature():
            raise InvalidSignature('Invalid Signature')
        if request.content_type == 'application/json':
            return request.get_json()
        elif request.content_type == 'application/x-www-form-urlencoded':
            return dict(request.form)
        raise InvalidPayload(request.content_type)


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


def _json_column(**kwargs):
    """Return JSON column."""
    return db.Column(
        JSONType().with_variant(
            postgresql.JSON(none_as_null=True),
            'postgresql',
        ),
        nullable=True,
        **kwargs
    )


class Event(db.Model, Timestamp):
    """Incoming webhook event data.

    Represents webhook event data which consists of a payload and a user id.
    """

    __tablename__ = 'webhooks_events'

    id = db.Column(
        UUIDType,
        primary_key=True,
        default=uuid.uuid4,
    )
    """Event identifier."""

    receiver_id = db.Column(db.String(255), index=True, nullable=False)
    """Receiver identifier."""

    user_id = db.Column(
        db.Integer,
        db.ForeignKey(User.id),
        nullable=True,
    )
    """User identifier."""

    payload = _json_column()
    """Store payload in JSON format."""

    payload_headers = _json_column()
    """Store payload headers in JSON format."""

    response = _json_column(
        default=lambda: {'status': 202, 'message': 'Accepted.'}
    )
    """Store response in JSON format."""

    response_headers = _json_column()
    """Store response headers in JSON format."""

    response_code = db.Column(db.Integer, default=202)

    @validates('receiver_id')
    def validate_receiver(self, key, value):
        """Validate receiver identifier."""
        if value not in current_webhooks.receivers:
            raise ReceiverDoesNotExist(self.receiver_id)
        return value

    @classmethod
    def create(cls, receiver_id, user_id=None):
        """Create an event instance."""
        event = cls(id=uuid.uuid4(), receiver_id=receiver_id, user_id=user_id)
        event.payload = event.receiver.extract_payload()
        return event

    @property
    def receiver(self):
        """Return registered receiver."""
        try:
            return current_webhooks.receivers[self.receiver_id]
        except KeyError:
            raise ReceiverDoesNotExist(self.receiver_id)

    @receiver.setter
    def receiver(self, value):
        """Set receiver instance."""
        assert isinstance(value, Receiver)
        self.receiver_id = value.receiver_id

    def process(self):
        """Process current event."""
        try:
            self.receiver(self)
        # TODO RESTException
        except Exception as e:
            current_app.logger.exception('Could not process event.')
            self.response_code = 500
            self.response = dict(status=500, message=str(e))
        return self
