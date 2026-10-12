"""Deterministic random generators. From halcyon_common.rng: one generator per
builder/table so adding rows to one table never reshuffles another."""
from __future__ import annotations

import zlib

import numpy as np


def rng(seed: int, tag: str) -> np.random.Generator:
    return np.random.default_rng([int(seed), zlib.crc32(tag.encode())])
