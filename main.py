"""GTA VI launch-day Twitch CCU forecaster (program/v1, stdlib only).

Model: the hour-by-hour shape of past big launches, as log ratios to their own
first-hour count, pooled over the comparables the case ships; each hour's five
quantiles are weighted empirical quantiles of those ratios, scaled by this
case's first-hour print. Console launches are weighted up, recent ones more,
and launches near GTA VI's size most of all; contaminated early-access rows and
rows without a plausible hour 1 are left out. With fewer than five usable
comparables it falls back to the house baseline (flat, random-walk spread).
"""
import json, math, os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
INPUT_DIR = Path(os.environ.get("MAKEFUN_INPUT_DIR", "/input"))
OUTPUT_DIR = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
LEVELS = [0.05, 0.25, 0.5, 0.75, 0.95]
Z = [-1.645, -0.674, 0.0, 0.674, 1.645]
MIN_V1 = 50000
SIZE_CENTER = 1_200_000.0
SIZE_SIGMA = 1.25


def hour_map(comp):
    """{hour 1..24: viewers} for the launch's own UTC release day."""
    day = str(comp.get("day_start", ""))[:10]
    out = {}
    for p in comp.get("hourly") or []:
        if not isinstance(p, dict):
            continue
        at = str(p.get("from", ""))
        if at[:10] != day:
            continue
        v = p.get("viewers")
        if v is None:
            continue
        try:
            h = int(at[11:13]) + 1
            out[h] = float(v)
        except (ValueError, TypeError):
            continue
    return out


def weight(comp, s):
    try:
        v1 = float(s.get(1, 0))
    except (TypeError, ValueError):
        return 0.0
    if v1 < MIN_V1:
        return 0.0
    platforms = str(comp.get("platforms", "")).lower()
    console = ("ps" in platforms) or ("xbox" in platforms)
    pc = "pc" in platforms
    if not console:
        return 0.0
    try:
        year = int(str(comp.get("day_start", ""))[:4])
    except (ValueError, TypeError):
        year = 2020
    w = 1.0
    w *= 1.5 if not pc else 1.0
    w *= math.exp(-max(0, 2026 - year) / 5.0)
    w *= math.exp(-0.5 * (math.log(v1 / SIZE_CENTER) / SIZE_SIGMA) ** 2)
    tier = str(comp.get("tier", "")).lower()
    if "contaminated" in tier:
        w *= 0.25
    return w


def wquant(pairs, tau):
    pairs = sorted(pairs)
    total = sum(w for _, w in pairs)
    if total <= 0:
        return None
    acc = 0.0
    for v, w in pairs:
        acc += w
        if acc >= tau * total:
            return v
    return pairs[-1][0]


def forecast(case):
    known = case.get("known") or []
    p1 = 1.0
    if known:
        try:
            p1 = max(1.0, float(known[0].get("viewers", 1)))
        except (TypeError, ValueError):
            p1 = 1.0
    pool = []
    for comp in case.get("comparables") or []:
        if not isinstance(comp, dict):
            continue
        s = hour_map(comp)
        if len([h for h in range(2, 25) if h in s and s[h] > 0]) < 20:
            continue
        w = weight(comp, s)
        if w <= 0:
            continue
        pool.append((s, w))
    rows = []
    for h in range(2, 25):
        qs = None
        if len(pool) >= 5:
            pairs = [(math.log(s[h] / s[1]), w) for s, w in pool
                     if h in s and s.get(1, 0) > 0 and s[h] > 0]
            if len(pairs) >= 5:
                vals = [wquant(pairs, tau) for tau in LEVELS]
                if all(v is not None for v in vals):
                    qs = [p1 * math.exp(v) for v in vals]
        if qs is None:
            qs = [p1 * math.exp(z * 0.15 * math.sqrt(h - 1)) for z in Z]
        qs = sorted(max(0.01, min(1e9, q)) for q in qs)
        rows.append({"hour": h, "q": qs})
    return {"hours": rows}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(INPUT_DIR.glob("*.in"))
    for path in files:
        with open(path, encoding="utf-8") as fh:
            case = json.load(fh)
        out = forecast(case)
        cid = str(case.get("id", path.stem))
        with open(OUTPUT_DIR / f"{cid}.out", "w", encoding="utf-8") as fh:
            json.dump(out, fh, separators=(",", ":"))


if __name__ == "__main__":
    main()
