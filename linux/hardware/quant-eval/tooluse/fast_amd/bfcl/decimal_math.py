"""Standard-library logarithm adapter for MathAPI's mpmath import."""

from decimal import Decimal, getcontext
from types import SimpleNamespace

mp = SimpleNamespace(dps=15)


def log(value):
    getcontext().prec = max(1, int(mp.dps))
    return Decimal(value).ln()
