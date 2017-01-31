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

"""Invenio module for processing webhook events."""

from __future__ import absolute_import, print_function

from functools import wraps

from flask import Blueprint, abort, jsonify, url_for
from flask.views import MethodView
from flask_babelex import lazy_gettext as _
from invenio_db import db
from invenio_oauth2server import require_api_auth, require_oauth_scopes
from invenio_oauth2server.models import Scope

from invenio_webhooks.decorators import need_receiver_permission, pass_event, \
    pass_user_id

from .errors import InvalidPayload, ReceiverDoesNotExist, WebhooksError
from .models import Event

blueprint = Blueprint('invenio_webhooks', __name__)

#
# Required scope
#
webhooks_event = Scope(
    'webhooks:event',
    group='Notifications',
    help_text=_('Allow notifications from external service.'),
    internal=True,
)


def add_link_header(response, links):
    """Add a Link HTTP header to a REST response.

    :param response: REST response instance.
    :param links: Dictionary of links.
    """
    if links is not None:
        response.headers.extend({
            'Link': ', '.join([
                '<{0}>; rel="{1}"'.format(l, r) for r, l in links.items()])
        })


def make_response(event):
    """Make a response from webhook event."""
    code, message = event.status
    response = jsonify(**event.response)
    response.headers['X-Hub-Event'] = event.receiver_id
    response.headers['X-Hub-Delivery'] = event.id
    if message:
        response.headers['X-Hub-Info'] = message
    add_link_header(response, {'self': url_for(
        '.event_item', receiver_id=event.receiver_id, event_id=event.id,
        _external=True
    )})
    return response, code


#
# Default decorators
#
def error_handler(f):
    """Decorator to handle exceptions."""
    @wraps(f)
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ReceiverDoesNotExist:
            return jsonify(
                status=404,
                description='Receiver does not exists.'
            ), 404
        except InvalidPayload as e:
            return jsonify(
                status=415,
                description='Receiver does not support the'
                            ' content-type "%s".' % e.args[0]
            ), 415
        except WebhooksError:
            return jsonify(
                status=500,
                description='Internal server error'
            ), 500
    return inner


#
# REST Resources
#
class ReceiverEventListResource(MethodView):
    """Receiver event hook."""

    @require_api_auth()
    @require_oauth_scopes('webhooks:event')
    @error_handler
    @pass_user_id
    @need_receiver_permission('create')
    def post(self, receiver_id, user_id):
        """Handle POST request."""
        event = Event.create(
            receiver_id=receiver_id,
            user_id=user_id
        )
        db.session.add(event)
        db.session.commit()

        # db.session.begin(subtransactions=True)
        event.process()
        db.session.commit()
        return make_response(event)

    def options(self, receiver_id):
        """Handle OPTIONS request."""
        abort(405)


class ReceiverEventResource(MethodView):
    """Event resource."""

    @require_api_auth()
    @require_oauth_scopes('webhooks:event')
    @error_handler
    @pass_user_id
    @pass_event
    @need_receiver_permission('read')
    def get(self, receiver_id, user_id, event):
        """Handle GET request."""
        return make_response(event)

    @require_api_auth()
    @require_oauth_scopes('webhooks:event')
    @error_handler
    @pass_user_id
    @pass_event
    @need_receiver_permission('update')
    def put(self, receiver_id, user_id, event):
        """Handle PUT request."""
        event.reprocess()
        db.session.commit()
        return make_response(event)

    @require_api_auth()
    @require_oauth_scopes('webhooks:event')
    @error_handler
    @pass_user_id
    @pass_event
    @need_receiver_permission('delete')
    def delete(self, receiver_id, user_id, event):
        """Handle DELETE request."""
        event.delete()
        db.session.commit()
        return make_response(event)


#
# Register API resources
#
event_list = ReceiverEventListResource.as_view('event_list')
event_item = ReceiverEventResource.as_view('event_item')

blueprint.add_url_rule(
    '/hooks/receivers/<string:receiver_id>/events/',
    view_func=event_list,
)
blueprint.add_url_rule(
    '/hooks/receivers/<string:receiver_id>/events/<string:event_id>',
    view_func=event_item,
)
