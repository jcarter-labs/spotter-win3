"""Pure math for the vertical band scope: frequency<->position mapping and
alpha-fade aging (spec item 5 — floor 0.15, never to zero), plus the policy
for when the scope actually needs repainting.
"""

from __future__ import annotations

AGE_ALPHA_FLOOR = 0.15
# Aging is the only thing that changes with no event: alpha moves at most
# (1 - floor) / window_seconds per second (~1.4 %/s at the shortest 1-minute
# window), so refreshing it every 2 s is visually indistinguishable.
FADE_REFRESH_SECONDS = 2.0


def y_for_freq(freq_khz: float, center_khz: float, bandwidth_khz: float) -> float:
    """0..1 fraction from bottom to top of the scope; higher frequency is
    higher on the spine."""
    half = bandwidth_khz / 2
    low, high = center_khz - half, center_khz + half
    if high == low:
        return 0.5
    return (freq_khz - low) / (high - low)


def in_window(freq_khz: float, center_khz: float, bandwidth_khz: float) -> bool:
    half = bandwidth_khz / 2
    return center_khz - half <= freq_khz <= center_khz + half


def age_alpha(age_seconds: float, window_seconds: float) -> float:
    """Linear fade from 1.0 (new) down to AGE_ALPHA_FLOOR at/after
    window_seconds — never reaches zero (spec item 5)."""
    if window_seconds <= 0:
        return AGE_ALPHA_FLOOR
    fraction_remaining = max(0.0, 1.0 - age_seconds / window_seconds)
    return AGE_ALPHA_FLOOR + (1.0 - AGE_ALPHA_FLOOR) * fraction_remaining


class RedrawGate:
    """Decides whether the scope needs repainting this tick: only when
    something changed (mark_dirty) or the fade interval has elapsed. Replaces
    an unconditional full rebuild + redraw on every 200 ms tick."""

    def __init__(self, fade_refresh_seconds: float = FADE_REFRESH_SECONDS) -> None:
        self._fade_refresh = fade_refresh_seconds
        self._dirty = True
        self._last_redraw: float | None = None

    def mark_dirty(self) -> None:
        self._dirty = True

    def should_redraw(self, now: float) -> bool:
        due = self._last_redraw is None or now - self._last_redraw >= self._fade_refresh
        if not (self._dirty or due):
            return False
        self._dirty = False
        self._last_redraw = now
        return True
