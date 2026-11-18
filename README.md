# gta6-twitch-forecast

Forecaster for make.fun's **gta6-twitch-ccu-forecast-01**: from hour 1 of GTA VI's
release day (Twitch concurrent viewers in the GTA VI category), predict hours 2-24 as
five quantiles (5/25/50/75/95%) for the lowest pinball loss on the log scale.

The model pools the case's own comparables -- past big launches' hourly counts -- as
log ratios to each launch's own first hour, weights console releases, recent releases
and releases near GTA VI's size up, drops early-access-contaminated rows, and takes
weighted empirical quantiles per hour, scaled by this case's hour-1 print. With too
few comparables it falls back to the house baseline (flat, random-walk spread).

Run locally:

    MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py

Standard library only; deterministic; no network.
