# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2014, 2015 CERN.
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

"""Calculate signatures for payloads."""

import hmac
from hashlib import sha1

from flask import current_app


def get_hmac(message):
    """Calculate HMAC value of message using ``WEBHOOKS_SECRET_KEY``.

    :param message: String to calculate HMAC for.
    """
    key = current_app.config['WEBHOOKS_SECRET_KEY']
    hmac_value = hmac.new(
        key.encode('utf-8') if hasattr(key, 'encode') else key,
        message.encode('utf-8') if hasattr(message, 'encode') else message,
        sha1
    ).hexdigest()
    return hmac_value


def check_x_hub_signature(signature, message):
    """Check X-Hub-Signature used by GitHub to sign requests.

    :param signature: HMAC signature extracted from request.
    :param message: Request message.
    """
    hmac_value = get_hmac(message)
    if hmac_value == signature or \
       (signature.find('=') > -1 and
            hmac_value == signature[signature.find('=') + 1:]):
        return True
    return False
