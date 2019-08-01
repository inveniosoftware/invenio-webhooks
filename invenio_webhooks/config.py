# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Webhooks module."""

WEBHOOKS_DEBUG_RECEIVER_URLS = {}
"""Mapping of receiver id to URL pattern.

This allows generating URLs to an intermediate webhook proxy service like
Ultrahook for testing on development machines:

.. code-block:: python

    WEBHOOKS_DEBUG_RECEIVER_URLS = {
        'github': 'https://hook.user.ultrahook.com/?access_token=%%(token)s'
    }
"""

WEBHOOKS_SECRET_KEY = 'secret_key'
