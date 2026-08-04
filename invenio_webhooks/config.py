# SPDX-FileCopyrightText: 2014, 2015, 2016 CERN.
# SPDX-License-Identifier: MIT

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

WEBHOOKS_SECRET_KEY = "secret_key"
