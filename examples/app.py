# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2019 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.


"""Minimal Flask application example for development.

Run example development server:

.. code-block:: console

   $ cd examples
   $ python app.py
"""

from __future__ import absolute_import, print_function

from flask import Flask
from flask_babelex import Babel

from invenio_webhooks import InvenioWebhooks

# Create Flask application
app = Flask(__name__)
Babel(app)
InvenioWebhooks(app)

if __name__ == "__main__":
    app.run()
