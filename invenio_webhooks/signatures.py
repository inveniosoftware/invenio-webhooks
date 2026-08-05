# SPDX-FileCopyrightText: 2014, 2015 CERN.
# SPDX-License-Identifier: MIT

"""Calculate signatures for payloads."""

import hmac
from hashlib import sha1

from flask import current_app


def get_hmac(message):
    """Calculate HMAC value of message using ``WEBHOOKS_SECRET_KEY``.

    :param message: String to calculate HMAC for.
    """
    key = current_app.config["WEBHOOKS_SECRET_KEY"]
    hmac_value = hmac.new(
        key.encode("utf-8") if hasattr(key, "encode") else key,
        message.encode("utf-8") if hasattr(message, "encode") else message,
        sha1,
    ).hexdigest()
    return hmac_value


def check_x_hub_signature(signature, message):
    """Check X-Hub-Signature used by GitHub to sign requests.

    :param signature: HMAC signature extracted from request.
    :param message: Request message.
    """
    hmac_value = get_hmac(message)
    return bool(
        hmac_value == signature
        or signature.find("=") > -1
        and hmac_value == signature[signature.find("=") + 1 :]
    )
