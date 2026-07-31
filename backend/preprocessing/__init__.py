"""Canonical PDF preprocessing package for JanMitra.

Keep package import side-effect free.  In particular, importing
``preprocessing.sarvam_system`` for an offline test must not initialize the
Sarvam SDK or load provider credentials.  Callers should import public classes
from their owning modules, for example ``preprocessing.router.DocumentRouter``.
"""
