# SPDX-FileCopyrightText: 2015, 2016 CERN.
# SPDX-FileCopyrightText: 2025 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Invenio module for processing webhook events."""

from invenio_base.utils import entry_points

from . import config


class _WebhooksState:
    """Webhooks state storing registered receivers."""

    def __init__(self, app, entry_point_group=None):
        """Initialize state."""
        self.app = app
        self.receivers = {}

        if entry_point_group:
            self.load_entry_point_group(entry_point_group)

    def register(self, receiver_id, receiver):
        """Register a receiver."""
        assert receiver_id not in self.receivers
        self.receivers[receiver_id] = receiver(receiver_id)

    def unregister(self, receiver_id):
        """Unregister a receiver by its id."""
        del self.receivers[receiver_id]

    def load_entry_point_group(self, entry_point_group):
        """Load actions from an entry point group."""
        for ep in entry_points(group=entry_point_group):
            self.register(ep.name, ep.load())


class InvenioWebhooks:
    """Invenio-Webhooks extension."""

    def __init__(self, app=None, **kwargs):
        """Extension initialization."""
        if app:
            self.init_app(app, **kwargs)

    def init_app(self, app, entry_point_group="invenio_webhooks.receivers"):
        """Flask application initialization."""
        self.init_config(app)
        state = _WebhooksState(app, entry_point_group=entry_point_group)
        self._state = app.extensions["invenio-webhooks"] = state

    def init_config(self, app):
        """Initialize configuration."""
        app.config.setdefault(
            "WEBHOOKS_BASE_TEMPLATE",
            app.config.get("BASE_TEMPLATE", "invenio_webhooks/base.html"),
        )

        for k in dir(config):
            if k.startswith("WEBHOOKS_"):
                app.config.setdefault(k, getattr(config, k))
