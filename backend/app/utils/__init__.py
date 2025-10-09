"""Utilities package for HSO Marine backend.

This module exposes common utility subpackages:
- adapters: external adapters (email, cache, etc.)
- exception handlers and helpers

Keep this file intentionally small to make imports explicit from submodules.
"""

__all__ = ["adapters", "exception_handlers", "exceptions", "logging_config", "metrics"]
