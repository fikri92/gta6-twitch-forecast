"""Forecast hours 2-24 of GTA VI's Twitch release day from its first hour.

A launch day is a peak and a shape. Each comparable launch contributes two
things measured on its own UTC release day: how much bigger its peak hour was
than its first hour, and the fraction of its peak that each later hour held.
This case's first-hour print times a pooled peak ratio and a pooled shape gives
the forecast, with weighted empirical quantiles over the comparables carrying
the uncertainty in both factors.

Comparables are filtered to console releases: a PC unlock happens at one global
moment, while GTA VI's console rollout is rolling midnight local time, so the
first hour means something different there. Early-access-contaminated rows and
rows without a believable first hour are dropped. If fewer than five console
rows remain the filter is relaxed to any console release; with too few usable
rows overall the house baseline is used (flat on hour 1, random-walk spread).
"""
import math

LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)
NORMAL_Z = (-1.645, -0.674, 0.0, 0.674, 1.645)
MIN_HOUR1 = 20_000.0
LOOSE_HOUR1 = 50_000.0
MIN_ROWS = 5


def hourly_map(comp):
    """Map hours 1..24 of a comparable's own UTC release day to viewers."""
    day = str(comp.get("day_start", ""))[:10]
    hours = {}
    for point in comp.get("hourly") or []:
        if not isinstance(point, dict):
            continue
        at = str(point.get("from", ""))
        if at[:10] != day:
            continue
        viewers = point.get("viewers")
        if viewers is None:
            continue
        try:
            hours[int(at[11:13]) + 1] = float(viewers)
        except (TypeError, ValueError):
            continue
    return hours


def launch_shape(hours):
    """Peak-to-first-hour ratio and each hour's fraction of that peak."""
    later = [h for h in range(2, 25) if hours.get(h, 0) > 0]
    if len(later) < 20 or hours.get(1, 0) <= 0:
        return None
    peak = max(hours[h] for h in later)
    if peak <= 0:
        return None
    ratio = peak / hours[1]
    shape = {h: hours[h] / peak for h in later}
    return ratio, shape


def comparable_weight(comp, hours, strict, min1):
    hour1 = float(hours.get(1, 0))
    if hour1 < min1:
        return 0.0
    platforms = str(comp.get("platforms", "")).lower()
    on_console = "ps" in platforms or "xbox" in platforms
    if not on_console:
        return 0.0
    has_pc = "pc" in platforms
    if strict and has_pc:
        return 0.0
    try:
        year = int(str(comp.get("day_start", ""))[:4])
    except (TypeError, ValueError):
        year = 2020
    w = 1.0
    w *= math.exp(-max(0, 2026 - year) / 6.0)
    if "contaminated" in str(comp.get("tier", "")).lower():
        w *= 0.25
    return w


def weighted_quantile(pairs, level):
    """Weighted empirical quantile, interpolated between neighbouring rows."""
    ordered = sorted(pairs)
    total = sum(w for _, w in ordered)
    if total <= 0.0:
        return None
    target = level * total
    running = 0.0
    previous = None
    for value, weight in ordered:
        if running + weight >= target:
            if previous is None or weight <= 0.0:
                return value
            fraction = (target - running) / weight
            return previous + (value - previous) * fraction
        running += weight
        previous = value
    return ordered[-1][0]


def hour1_print(case):
    known = case.get("known") or []
    if known:
        try:
            return max(1.0, float(known[0].get("viewers", 1)))
        except (TypeError, ValueError):
            pass
    return 1.0


def build_pool(case, strict, min1):
    """Usable comparables: (weight, peak ratio, shape) under one strictness."""
    pool = []
    for comp in case.get("comparables") or []:
        if not isinstance(comp, dict):
            continue
        hours = hourly_map(comp)
        shaped = launch_shape(hours)
        if shaped is None:
            continue
        w = comparable_weight(comp, hours, strict, min1)
        if w > 0.0:
            ratio, shape = shaped
            pool.append((w, ratio, shape))
    return pool


def forecast(case):
    hour1 = hour1_print(case)
    pool = build_pool(case, True, MIN_HOUR1)
    if len(pool) < MIN_ROWS:
        pool = build_pool(case, False, LOOSE_HOUR1)
    rows = []
    for hour in range(2, 25):
        qs = None
        if len(pool) >= MIN_ROWS:
            ratios = [(ratio, w) for w, ratio, shape in pool if hour in shape]
            shapes = [(shape[hour], w) for w, ratio, shape in pool if hour in shape]
            if len(ratios) >= MIN_ROWS and len(shapes) >= MIN_ROWS:
                values = []
                for level in LEVELS:
                    pr = weighted_quantile(ratios, level)
                    sh = weighted_quantile(shapes, level)
                    if pr is None or sh is None:
                        values = []
                        break
                    values.append(hour1 * pr * sh)
                if values:
                    qs = values
        if qs is None:
            qs = [hour1 * math.exp(z * 0.15 * math.sqrt(hour - 1)) for z in NORMAL_Z]
        qs = sorted(min(1e9, max(0.01, q)) for q in qs)
        rows.append({"hour": hour, "q": qs})
    return {"hours": rows}
