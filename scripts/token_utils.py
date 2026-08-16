#!/usr/bin/env python3
"""Dependency-free conservative token estimates for context-budget regression tests."""
from __future__ import annotations

import math
import re


def estimate_tokens(text: str) -> int:
    """Estimate multilingual tokens conservatively; use for budgets, not billing."""
    utf8_estimate = math.ceil(len(text.encode("utf-8")) / 3)
    lexical_estimate = len(re.findall(r"\w+|[^\w\s]", text, re.UNICODE))
    return max(utf8_estimate, lexical_estimate)
