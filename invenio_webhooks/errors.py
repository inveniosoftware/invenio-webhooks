# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2016-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Webhook errors."""

from __future__ import absolute_import


class WebhooksError(Exception):
    """General webhook error."""


class ReceiverDoesNotExist(WebhooksError):
    """Raised when receiver does not exist."""


class InvalidPayload(WebhooksError):
    """Raised when the payload is invalid."""


class InvalidSignature(WebhooksError):
    """Raised when the signature does not match."""
