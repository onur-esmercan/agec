"""Typing helpers for optional adapters."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeAlias

CallableInput: TypeAlias = object | Callable[[object | None], object]
