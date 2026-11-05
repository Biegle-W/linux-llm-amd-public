"""Finite phase budgets without a per-token decode cutoff."""
from dataclasses import dataclass
import math
import time


def violation(now, heartbeat, progress, limits):
    if now - heartbeat['monotonic'] > limits['heartbeat_seconds']:
        return 'supervisor heartbeat missing'
    phase = progress['phase']
    age = now - progress['phase_started']
    if phase == 'loading' and age > limits['load_seconds']:
        return 'model loading deadline'
    first_limit = limits.get('first_token_seconds')
    # Legacy numeric decode-stall values are accepted as input but never enforced. New large-
    # model diagnostics pass None and retain their enclosing stage deadline.
    if phase == 'prefill' and first_limit is not None and age > first_limit:
        return 'first output deadline'
    # Large offloaded models can pause between output tokens while still working.
    # Legacy decode_stall_seconds settings are intentionally ignored: the owner
    # removed that cutoff on November 5. Bound generation by its complete phase.
    prefill_limit = limits.get('prefill_seconds')
    if phase == 'prefill' and prefill_limit is not None and age > prefill_limit:
        return 'prefill phase deadline'
    if first_limit is None:
        if phase == 'decode':
            start = progress.get('decode_started', progress['phase_started'])
            if now - start > limits['request_seconds']:
                return 'post-first-output request deadline'
    elif phase in ('prefill', 'decode'):
        if now - progress.get('request_started', now) > limits['request_seconds']:
            return 'request wall deadline'
    if phase == 'idle' and age > limits['idle_seconds']:
        return 'idle inter-request deadline'
    if phase == 'cleanup' and age > limits['cleanup_seconds']:
        return 'owned cleanup deadline'
    return None


class DiagnosticBudgetExpired(TimeoutError):
    """The experiment ended without establishing an inference verdict."""


@dataclass(frozen=True)
class StageBudget:
    started: float
    seconds: float
    cleanup_seconds: float

    def __post_init__(self):
        if not (math.isfinite(self.started) and math.isfinite(self.seconds)
                and math.isfinite(self.cleanup_seconds)
                and self.seconds > self.cleanup_seconds > 0):
            raise ValueError('A finite enclosing budget must reserve owned cleanup time')

    def timeout_seconds(self, now=None):
        now = time.monotonic() if now is None else now
        remaining = self.started + self.seconds - self.cleanup_seconds - now
        if remaining <= 0:
            raise DiagnosticBudgetExpired('Enclosing diagnostic budget exhausted; inference is inconclusive')
        return remaining

    def timeout_ms(self, now=None):
        return math.ceil(self.timeout_seconds(now) * 1000)

    def check(self):
        self.timeout_seconds()
