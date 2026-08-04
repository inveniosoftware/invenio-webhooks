# SPDX-FileCopyrightText: 2015 CERN.
# SPDX-License-Identifier: MIT

"""Minimal Flask application example for development.

Run example development server:

.. code-block:: console

   $ cd examples
   $ python app.py
"""

from flask import Flask

from invenio_webhooks import InvenioWebhooks

# Create Flask application
app = Flask(__name__)
InvenioWebhooks(app)

if __name__ == "__main__":
    app.run()
