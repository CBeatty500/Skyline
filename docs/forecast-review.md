# Skyline forecast reviews

Running log of verification reviews: what the data showed, what changed and why, what to watch.

## 2026-10-16: first review

**Verification data.** The system went live today: 18 cities, checked 4 times a day. Daily scoring starts with the first measured day (Oct 17); hourly scoring started this evening (1 hour per city so far). There are not yet enough cases for any statistical correction, so no learned correction is active. Corrections stay at zero until the minimums are met (3 daily cases for highs and lows, 10 for rain chance, 6 effective hourly cases for hourly variables, 24 for hourly rain chance).

**Problems found today (from use, Ashburn, rain arriving after sunset) and fixed:**
- Evening temperatures lifted to the day's high (82°F "before sunrise"): today's curve was rescaled to the forecast high even after the peak had passed. Now only while the afternoon peak is still ahead and the sun is up. A "rise overnight" statement requires the warmest hour to come after the coolest.
- Radar motion of 77 mph: a two-frame match on a coarse grid hit the edge of its search. Now three frames 15 minutes apart, ~10 km grid, edge matches rejected, the two 15-minute steps must agree with the 30-minute step, nothing above 60 mph. Synthetic tests: 25/40/10/55 mph recovered within 1 mph; random echoes give no motion.
- "Clear" while raining: the station report can lag or miss light rain. Reflectivity over the location (last 20 min) now sets current precipitation when the station reports none.
- Hourly day/night icons now follow the actual sunrise and sunset for each hour.

**New: regional observation analysis (0-9 h).** Up to 28 nearby NWS stations (within 160 km) are compared with the model at their own sites and elevations. The error field is carried along the low-level flow (mean station wind x1.25); the change in error expected here (minus a 1°C noise floor, 70%, fading) is added to the next 9 hours of temperature and dewpoint. A forecast line appears when the change reaches about 3°F. Skipped when the flow is under 8 km/h or fewer than 4 stations report.

**Verification stations.** Most representative, robust station per city: Burke uses Davison AAF (KDAA), Chicago Midway, Dallas Love Field, Los Angeles Downtown/USC, New York Central Park for daily and LaGuardia for hourly. Others use the main airport.

**Watching next week:**
- Displayed versus raw temperature error at 0-6 h ("ts" versus "t" in hourly cells): is the observation, regional and trend adjustment actually reducing error? If not, damp the regional factor.
- Regional diagnostics per city (learning.json "diag"): station counts, flow, size of adjustments; any implausible messages.
- Night versus day temperature bias, especially Mammoth Lakes (KMMH lower and east of town), Denver (KDEN on the plains), Phoenix (urban heat island at night).
- Gust ratio: models are usually too gusty in light flow; expect gust ratios below 1.
- Rain-chance reliability in the dry West (Phoenix, Los Angeles): over-forecast likely.
- Run time with 3 cities at a time, and whether any city is skipped.
