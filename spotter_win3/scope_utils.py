"""Pure math for the vertical band scope: frequency<->position mapping and
alpha-fade aging (spec item 5 — floor 0.15, never to zero).
"""

from __future__ import annotations

AGE_ALPHA_FLOOR = 0.15


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
