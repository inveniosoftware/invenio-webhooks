# SPDX-FileCopyrightText: 2025 Graz University of Technology.
# SPDX-License-Identifier: MIT

"""Compatibility module for Flask."""

from importlib.metadata import version

from packaging.version import Version as V

_FLASK_CURRENT_VERSION = V(version("flask"))
_FLASK_VERSION_WITH_BUG = V("0.12")


def delete_cached_json_for(request):
    """Delete `_cached_json` attribute for the given request.

    Bug workaround to delete `_cached_json` attribute when using Flask < 0.12.
    More details: https://github.com/pallets/flask/issues/2087

    Note that starting from Flask 1.0, the private `_cached_json` attribute
    has been changed in Flask package, and this code will fail.
    """
    if _FLASK_CURRENT_VERSION < _FLASK_VERSION_WITH_BUG:
        if hasattr(request, "_cached_json"):
            delattr(request, "_cached_json")
