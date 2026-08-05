# SPDX-FileCopyrightText: 2015 CERN.
# SPDX-FileCopyrightText: 2025-2026 Graz University of Technology.
# SPDX-FileCopyrightText: 2026 TU Wien.
# SPDX-License-Identifier: MIT

"""Invenio module for processing webhook events."""

from .ext import InvenioWebhooks
from .models import Receiver
from .proxies import current_webhooks

__version__ = "4.0.2"

__all__ = (
    "InvenioWebhooks",
    "Receiver",
    "__version__",
    "current_webhooks",
)
