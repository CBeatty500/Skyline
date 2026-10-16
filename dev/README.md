# Skyline build sources

`index.html` (repo root) is the built app. It is assembled from these sources:

- `src/the_weather.html`: the original base page.
- `src/build_skyline.py`: layout, hero, CSS, renderHero; reads the base page, then runs `skyline_extra.py` and `skyline_post.py`.
- `src/skyline_extra.py`: every later edit, as exact-match replacements (`_r(old, new)` asserts one match) and module inserts placed before `function restOfDayPhrase()`.
- `src/*.js`, `src/*.html`: modules inserted by the build (SPC, outlook, sections, thunder, radar, regional observations, learning, hourly learning, climate stations, daily climate, quick view, model analysis).
- `src/skyline_post.py`: compiles Tailwind (v3.4.17 standalone, `twbuild/`) into the page and replaces middle dots.
- `mock/`: offline test fixtures and Playwright test scripts.

Restore and build:

```
bash dev/restore.sh
python3 /home/claude/build_skyline.py
cp /mnt/user-data/outputs/skyline.html index.html
```

Check: extract the `<script>` blocks and run `node --check`; run a mock test from `/home/claude/mock`.

Small fixes can also be made directly in `index.html`, but then copy the change into these sources too, or the next build will undo it.
