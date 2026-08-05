# SPDX-FileCopyrightText: 2014, 2015, 2016 CERN.
# SPDX-License-Identifier: MIT

"""Invenio module for processing webhook events."""

from functools import wraps

from flask import Blueprint, abort, jsonify, request, url_for
from flask.views import MethodView
from flask_login import current_user
from invenio_db import db
from invenio_i18n import _
from invenio_oauth2server import require_api_auth, require_oauth_scopes
from invenio_oauth2server.models import Scope

from .errors import InvalidPayload, ReceiverDoesNotExist, WebhooksError
from .models import Event

blueprint = Blueprint("invenio_webhooks", __name__)

#
# Required scope
#
webhooks_event = Scope(
    "webhooks:event",
    group="Notifications",
    help_text=_("Allow notifications from external service."),
    internal=True,
)


def add_link_header(response, links):
    """Add a Link HTTP header to a REST response.

    :param response: REST response instance.
    :param links: Dictionary of links.
    """
    if links is not None:
        response.headers.extend(
            {"Link": ", ".join([f'<{l}>; rel="{r}"' for r, l in links.items()])}
        )


def make_response(event):
    """Make a response from webhook event."""
    code, message = event.status
    response = jsonify(**event.response)
    response.headers["X-Hub-Event"] = event.receiver_id
    response.headers["X-Hub-Delivery"] = event.id
    if message:
        response.headers["X-Hub-Info"] = message
    add_link_header(
        response,
        {
            "self": url_for(
                ".event_item",
                receiver_id=event.receiver_id,
                event_id=event.id,
                _external=True,
            )
        },
    )
    return response, code


#
# Default decorators
#
def error_handler(f):
    """Return a json payload and appropriate status code on expection."""

    @wraps(f)
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ReceiverDoesNotExist:
            return jsonify(status=404, description="Receiver does not exists."), 404
        except InvalidPayload as e:
            return (
                jsonify(
                    status=415,
                    description="Receiver does not support the"
                    f' content-type "{e.args[0]}".',
                ),
                415,
            )
        except WebhooksError:
            return jsonify(status=500, description="Internal server error"), 500

    return inner


#
# REST Resources
#
class ReceiverEventListResource(MethodView):
    """Receiver event hook."""

    @require_api_auth()
    @require_oauth_scopes("webhooks:event")
    @error_handler
    def post(self, receiver_id=None):
        """Handle POST request."""
        try:
            user_id = request.oauth.access_token.user_id
        except AttributeError:
            user_id = current_user.get_id()

        event = Event.create(receiver_id=receiver_id, user_id=user_id)
        db.session.add(event)
        db.session.commit()

        try:
            event.process()
        except Exception:
            db.session.rollback()
            event.response_code = 500
            event.response = {"status": 500, "message": "Internal Server Error"}
            db.session.commit()
        return make_response(event)

    def options(self, receiver_id=None):
        """Handle OPTIONS request."""
        abort(405)


class ReceiverEventResource(MethodView):
    """Event resource."""

    @staticmethod
    def _get_event(receiver_id, event_id):
        """Find event and check access rights."""
        event = Event.query.filter_by(
            receiver_id=receiver_id, id=event_id
        ).first_or_404()

        try:
            user_id = request.oauth.access_token.user_id
        except AttributeError:
            user_id = current_user.get_id()

        if event.user_id != int(user_id):
            abort(401)

        return event

    @require_api_auth()
    @require_oauth_scopes("webhooks:event")
    @error_handler
    def get(self, receiver_id=None, event_id=None):
        """Handle GET request."""
        event = self._get_event(receiver_id, event_id)
        return make_response(event)

    @require_api_auth()
    @require_oauth_scopes("webhooks:event")
    @error_handler
    def delete(self, receiver_id=None, event_id=None):
        """Handle DELETE request."""
        event = self._get_event(receiver_id, event_id)
        event.delete()
        db.session.commit()
        return make_response(event)


#
# Register API resources
#
event_list = ReceiverEventListResource.as_view("event_list")
event_item = ReceiverEventResource.as_view("event_item")

blueprint.add_url_rule(
    "/hooks/receivers/<string:receiver_id>/events/",
    view_func=event_list,
)
blueprint.add_url_rule(
    "/hooks/receivers/<string:receiver_id>/events/<string:event_id>",
    view_func=event_item,
)
