# gta6-twitch-forecast

[![make.fun · gta6-twitch-ccu-forecast-01](https://make.fun/badge/gta6-twitch-ccu-forecast-01.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![rank](https://make.fun/badge/gta6-twitch-ccu-forecast-01/fikri92/gta6-twitch-forecast/rank.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)
[![reward](https://make.fun/badge/gta6-twitch-ccu-forecast-01/fikri92/gta6-twitch-forecast/reward.svg)](https://make.fun/bounty/gta6-twitch-ccu-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=gta6-twitch-ccu-forecast-01)

Entry for [make.fun's gta6-twitch-ccu-forecast-01](https://make.fun/bounty/gta6-twitch-ccu-forecast-01):
from hour 1 of Grand Theft Auto VI's release day (Twitch concurrent viewers in the
GTA VI category), forecast hours 2-24 as five quantiles (5/25/50/75/95%) for the
lowest pinball loss on the log scale.

## How it forecasts

Each comparable launch the case ships is read as log ratios of its hours 2-24 to
its own hour 1 -- the shape of a launch day, independent of size. The case's hour-1
print scales the pooled shape. Weights favour the launches most like GTA VI:
console releases, recent releases, and releases near GTA VI's size; early-access
contaminated rows and rows without a believable first hour are dropped. Each hour's
five quantiles are weighted empirical quantiles of those ratios. With fewer than
five usable comparables the program falls back to the house baseline (flat on hour
1, random-walk spread in log space).

## Run

    MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py

Python 3.13 standard library only; deterministic; no network.

## Files

- `main.py` -- entrypoint: reads each `*.in` case, writes `<id>.out`.
- `model.py` -- the comparable-shape forecaster.

## Referral

Made with make.fun; my referral code is on my [make.fun profile](https://make.fun).
