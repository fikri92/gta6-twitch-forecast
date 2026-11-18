"""Forecast hours 2-24 of GTA VI's Twitch release day from its first hour.

The shape of a launch day is shared across big releases, so each comparable's
hours 2-24 are read as log ratios to that comparable's own hour 1. This case's
hour 1 then scales the pooled shape: every hour gets five weighted empirical
quantiles of those log ratios.

Weights favour the launches most like GTA VI: console releases (a console-only
midnight rollout makes hour 1 partial, exactly as here), recent releases, and
releases near GTA VI's size. Early-access-contaminated rows and rows without a
believable first hour are dropped. Fewer than five usable rows falls back to the
house baseline: flat on hour 1 with a random walk's spread in log space.
"""
import math

LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)
NORMAL_Z = (-1.645, -0.674, 0.0, 0.674, 1.645)
MIN_HOUR1 = 50_000.0
SIZE_CENTER = 1_200_000.0
SIZE_SPREAD = 1.25
MIN_ROWS = 5


def hourly_map(comp):
    """Map hour 1..24 of a comparable's own UTC release day to its viewers."""
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


def comparable_weight(comp, hours):
    """0 for rows that cannot help; otherwise a similarity weight."""
    hour1 = float(hours.get(1, 0))
    if hour1 < MIN_HOUR1:
        return 0.0
    platforms = str(comp.get("platforms", "")).lower()
    on_console = "ps" in platforms or "xbox" in platforms
    if not on_console:
        return 0.0
    has_pc = "pc" in platforms
    try:
        year = int(str(comp.get("day_start", ""))[:4])
    except (TypeError, ValueError):
        year = 2020
    w = 1.5 if not has_pc else 1.0
    w *= math.exp(-max(0, 2026 - year) / 5.0)
    w *= math.exp(-0.5 * (math.log(hour1 / SIZE_CENTER) / SIZE_SPREAD) ** 2)
    if "contaminated" in str(comp.get("tier", "")).lower():
        w *= 0.25
    return w


def weighted_quantile(pairs, level):
    """Empirical quantile of (value, weight) pairs at a level in (0, 1)."""
    ordered = sorted(pairs)
    total = sum(w for _, w in ordered)
    if total <= 0.0:
        return None
    running = 0.0
    for value, weight in ordered:
        running += weight
        if running >= level * total:
            return value
    return ordered[-1][0]


def hour1_print(case):
    known = case.get("known") or []
    if known:
        try:
            return max(1.0, float(known[0].get("viewers", 1)))
        except (TypeError, ValueError):
            pass
    return 1.0


def forecast(case):
    hour1 = hour1_print(case)
    pool = []
    for comp in case.get("comparables") or []:
        if not isinstance(comp, dict):
            continue
        hours = hourly_map(comp)
        if sum(1 for h in range(2, 25) if hours.get(h, 0) > 0) < 20:
            continue
        w = comparable_weight(comp, hours)
        if w > 0.0:
            pool.append((hours, w))
    rows = []
    for hour in range(2, 25):
        qs = None
        if len(pool) >= MIN_ROWS:
            pairs = [(math.log(hm[hour] / hm[1]), w) for hm, w in pool
                     if hm.get(1, 0) > 0 and hm.get(hour, 0) > 0]
            if len(pairs) >= MIN_ROWS:
                values = [weighted_quantile(pairs, level) for level in LEVELS]
                if all(v is not None for v in values):
                    qs = [hour1 * math.exp(v) for v in values]
        if qs is None:
            qs = [hour1 * math.exp(z * 0.15 * math.sqrt(hour - 1)) for z in NORMAL_Z]
        qs = sorted(min(1e9, max(0.01, q)) for q in qs)
        rows.append({"hour": hour, "q": qs})
    return {"hours": rows}
