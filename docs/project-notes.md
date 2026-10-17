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
- Radar colour scale: the NOAA mosaic uses a continuous colour path, calibrated (Oct 17) against IEM's numeric N0Q composite (grey-blue 0-10, blue ~15, cyan ~19, teal ~21-24, bright green ~28, dark greens ~31-38, yellow ~40-44 dBZ; yellow-green to yellow ~45-49, yellow to orange-yellow ~49-53 dBZ, calibrated Oct 17; red/magenta (55+) at standard positions until storms supply samples). Every verification run adds colour/dBZ pairs to data/radar_calib.json (scripts/radar_calib.py); the weekly review updates DBZ_PATH in radar.js from it. Radar alone never means thunder: 50+ dBZ plus NWS thunder 15%+ or an SPC thunder area.
- Continuity between loads (hourly, 2 h and beyond): PoP changes under 10 held, under 30 halfway; cloud under 15 held, under 40 halfway. The last radar result is reused at first view on a reload within 15 min, then replaced by fresh radar.
- First view after the forecast and station data; climate records, totals and air quality fill in afterwards.
- Radar (radar.js): 33x33 samples, three frames 15 min apart, consistent motion only, under 60 mph; echo along the trajectory (the location's own cell first, widening later); no extrapolation beyond 20 min without reliable motion. Rain that has passed (echoes just downstream, none upstream) caps the next 3 hours at 20% with no thunder from older guidance, and ends a stale station 'rain' report. Radar over the location (own sample) sets current precipitation when the station reports none.
- Precipitation falling now: the text gives when it ends (radar) and the chance of MORE afterwards ('Rain ending around 9:00 PM; ... Then a 20% chance of a passing shower.'), never a 100% for the whole period. When echoes can't be tracked, the 700 mb model wind steers them; nothing upstream after the current rain caps the next two hours at 30%.
- Forecast text states the forecast, not the analysis: no 'Radar:' or station commentary (e.g. 'Rain arriving around 9:00 PM.', 'Colder air arrives from the northwest by about 10 PM.').
- SPC: Day 1-3 risks, mesoscale discussions, thunder chances (thunder.js, spc.js).
- Nationwide corrections (learning.national): errors shared by 75%+ of at least 8 tracked cities (median, 70%, capped at half the city limits). Untracked US places get them in full; tracked cities blend from nationwide toward their own as their cases grow.
- Hourly learning cells: lead (0-6, 6-24, 24-48, 48+ h) x phase (day, evening = sunset to midnight, late night = midnight to sunrise, so pre-dawn lows are learned separately). No correction (city or nationwide) until a cell's cases span 3+ different days.
- Learning: daily (highs, lows, rain chance, rain amount by lead) and hourly (temperature, dewpoint, wind, gust, cloud, rain chance by lead and day / night), shrunk and capped corrections from the shared verification (and on-device daily learning).
- Day / night per hour from actual sunrise / sunset (sun shown if up at that hour).
- Hourly precipitation icon only at 40%+ chance (the icon follows the number shown); below that the sky icon.

## Layout decisions (owner's requests)
Order: location, alerts (chips; under the city on phones), hero (Current Conditions and Today So Far 2x2 blocks, peak gust, feels-like centered under temperature, text forecast Today / Tonight / Tomorrow / Tomorrow Night stacked), details, hourly, graphs (temperature and precipitation, collapsible), 12-day forecast, AFD with Severe / Winter discussions, Quick Glance at the Week Ahead (open), Observed Climate (precipitation totals on top, month pickers under totals, Warmest / Coldest / Avg high / Avg low / Mean / Precipitation tiles, daily table collapsed, record trophies as popups, nearby station picker), long-term trend (closed), Model Analysis (closed). All sections collapsible with one uniform style. Radar section directly below Detailed Current Observations, closed by default (radar_map.js): Leaflet on a darkened Esri dark-gray base (keyless; CARTO now needs a key), US Census county and state lines (us-atlas via jsdelivr) drawn over the radar, NOAA reflectivity exportImage recoloured per pixel through the calibrated rgbToDbz (below 15 dBZ and isolated specks removed, 15-20 dBZ muted), optional NWS warnings (storm polygons outlined, county-based alerts shaded via SAME codes), 1-hour loop, local time, opens on the selected city. No storm tracks or cells. Place shortcuts: Ashburn, DC, New York, Denver, Chicago, Seattle, Anchorage, Miami. Location line elevation in feet only (meters only in metric mode). Observed Climate also has a collapsed "Past 24 hours" table of hourly station reports (routine hourly METAR = raw report with the SLP remark, true specials = raw report without it (NWS raw text has no METAR/SPECI word); 5-minute readings never shown at stations with proper reports; at other stations only for significant changes: precipitation start/stop, thunder, gusts 25 mph+, visibility under 3 or 1 mi). A forecast card's chance and icon come from its own period segments, so they always agree.

Mammoth Lakes was removed from verification (Oct 16) at the owner's request: unreliable station data.

Los Angeles hourly checks and current conditions use Burbank (KBUR) since Oct 17: the Downtown/USC station (KCQT) stopped reporting through the NWS; daily checks stay on the official downtown record (KCQT).

## Current-conditions stations
Tracked cities show current conditions from the same station their forecasts are verified against (VERIFY_STATIONS in the app, matching `obs` in data/locations.json; within 12 km of the city). Order: that station from the NWS API, then the same station from IEM, then the next nearest station. Keep the two lists in sync when cities or stations change.

## Climate station choices
Nearest representative station within 40 km and 300 m elevation (observing station's own site to 60 km); per-location override in the picker. Burke uses Reagan (DCA) climate; Mammoth Lakes uses the Mammoth airport observations plus IEM daily data.
