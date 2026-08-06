import os
import sys
from datetime import date, timedelta

# Make src/ importable without an install step.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


def make_obs(onset, lag_days, *, base=200.0, peak_add=150.0,
             before_days=200, after_days=200, step=7):
    """Weekly (date, value) series with a triangular stress peak at onset+lag_days.

    Baseline carries a small deterministic ±1 wobble so its sd > 0 (needed for
    z-scores). The maximum sits exactly at onset+lag_days when lag_days is a
    multiple of step.
    """
    obs = []
    # Anchor the weekly grid on onset so peaks at multiples of `step` land exactly.
    k_min = -(before_days // step)
    k_max = after_days // step
    for k in range(k_min, k_max + 1):
        d = onset + timedelta(days=k * step)
        delta = k * step
        if delta <= 0:
            v = base + (1.0 if k % 2 == 0 else -1.0)
        elif delta <= lag_days:
            v = base + peak_add * (delta / lag_days)
        else:
            v = base + peak_add * max(0.0, 1 - (delta - lag_days) / lag_days)
        obs.append((d, v))
    return obs
