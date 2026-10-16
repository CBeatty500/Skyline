# Skyline project notes

Everything a new session needs to continue the work. The owner is a meteorologist; measured data matters most.

## Where things live
- App: `index.html` (single file). Live at https://cbeatty500.github.io/Skyline (GitHub Pages, deploys on every push). Also weatherisawesome.netlify.app (Netlify link to GitHub broken; stale until relinked). The owner often emails the file to a work computer where Netlify is blocked.
- Build sources: `dev/` (see `dev/README.md`; `bash dev/restore.sh` then `python3 /home/claude/build_skyline.py`).
- Verification: `.github/workflows/learn.yml` (4x daily), `scripts/learn.mjs`, `data/locations.json` (cities, `obs` station for hourly checks, `daily` station for official daily records), results in `data/learning.json`, `data/snapshots.json`, `data/hourly_snaps.json`.
- Reviews: `docs/forecast-review.md` (weekly scheduled review, Mondays 9:51 AM Eastern).

## Standing rules
- Deliver every change: build, push to GitHub (index.html), and send the file to the owner.
- Commits: author `CBeatty500`, email `343234935+CBeatty500@users.noreply.github.com` (never any other email). Messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Measured / official data only, no API keys.
- Minimal text. No middle dots except in the "Lat · Lon · Elev" line. No subjective dewpoint descriptors.
- Forecast continuity between loads. Summary text must match the hourly icons. Never mention rain that already ended.
- Think before posting: nothing physically implausible (e.g. warming to the day's high after sunset, 77 mph radar motion).

## Data sources
Open-Meteo (forecast, individual models, elevation; multi-point for regional analysis); NWS API (points, forecast, gridData PoP / thunder / sky cover, alerts, observations, station lists); IEM (CLI climate reports, AFOS products SWOMCD/SWODY/QPFHSD, daily summaries, obhistory); ACIS (station metadata, daily records, normals); NOAA mapservices (SPC outlooks, base reflectivity mosaic sampled for the radar nowcast).

## Forecast method (summary)
- Multi-model blend weighted by region and by today's skill against the station; NWS point forecast blended 40% for highs / lows; NWS grid PoP and sky cover blended 50/50.
- Observation correction: the hourly curve starts from the latest report and the bias fades; measured warming trend extrapolated to the afternoon peak; today's high raised to the curve peak and measured value (raiseTodayHigh), curve mapped to the high only while the peak is still ahead.
- Regional observations (regional.js): nearby station errors versus the model, carried along the low-level flow, 0-9 h.
- Radar (radar.js): 33x33 samples, three frames 15 min apart, consistent motion only, under 60 mph; nowcast PoP / thunder for 0-3 h; radar over the location sets current precipitation when the station reports none.
- SPC: Day 1-3 risks, mesoscale discussions, thunder chances (thunder.js, spc.js).
- Learning: daily (highs, lows, rain chance, rain amount by lead) and hourly (temperature, dewpoint, wind, gust, cloud, rain chance by lead and day / night), shrunk and capped corrections from the shared verification (and on-device daily learning).
- Day / night per hour from actual sunrise / sunset (sun shown if up at that hour).

## Layout decisions (owner's requests)
Order: location, alerts (chips; under the city on phones), hero (Current Conditions and Today So Far 2x2 blocks, peak gust, feels-like centered under temperature, text forecast Today / Tonight / Tomorrow / Tomorrow Night stacked), details, hourly, graphs (temperature and precipitation, collapsible), 12-day forecast, AFD with Severe / Winter discussions, Quick Glance at the Week Ahead (open), Observed Climate (precipitation totals on top, month pickers under totals, Warmest / Coldest / Avg high / Avg low / Mean / Precipitation tiles, daily table collapsed, record trophies as popups, nearby station picker), long-term trend (closed), Model Analysis (closed). All sections collapsible with one uniform style. Place shortcuts: Ashburn, DC, New York, Denver, Chicago, Seattle, Anchorage, Miami.

## Climate station choices
Nearest representative station within 40 km and 300 m elevation (observing station's own site to 60 km); per-location override in the picker. Burke uses Reagan (DCA) climate; Mammoth Lakes uses the Mammoth airport observations plus IEM daily data.
