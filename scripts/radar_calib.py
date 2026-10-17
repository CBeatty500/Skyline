# Radar colour calibration: pairs the NOAA mosaic colour with IEM's numeric N0Q reflectivity at the same place and time.
# Scans the lower 48 for echoes, samples densely around the strongest, and adds the pairs to data/radar_calib.json.
import json, urllib.request, urllib.parse, collections, io, datetime as dt, os
from PIL import Image
IS = 'https://mapservices.weather.noaa.gov/eventdriven/rest/services/radar/radar_base_reflectivity_time/ImageServer'
def samples(pts, ms):
    out = []
    for k in range(0, len(pts), 400):
        ch = pts[k:k + 400]
        body = urllib.parse.urlencode({'geometry': json.dumps({'points': ch, 'spatialReference': {'wkid': 4326}}), 'geometryType': 'esriGeometryMultipoint',
                                       'returnFirstValueOnly': 'true', 'interpolation': 'RSP_NearestNeighbor', 'time': str(ms), 'f': 'json'}).encode()
        try:
            j = json.load(urllib.request.urlopen(urllib.request.Request(IS + '/getSamples', data=body), timeout=90))
            out += [(ch[s['locationId']], s['value']) for s in j.get('samples', [])]
        except Exception: pass
    return out
info = json.load(urllib.request.urlopen(IS + '?f=json', timeout=60))
T = dt.datetime.utcfromtimestamp(info['timeInfo']['timeExtent'][1] / 1000) - dt.timedelta(minutes=10)
T = T.replace(minute=T.minute - T.minute % 5, second=0, microsecond=0)
ms = int(T.replace(tzinfo=dt.timezone.utc).timestamp() * 1000)
im = Image.open(io.BytesIO(urllib.request.urlopen(f"https://mesonet.agron.iastate.edu/archive/data/{T:%Y/%m/%d}/GIS/uscomp/n0q_{T:%Y%m%d%H%M}.png", timeout=120).read()))
W, H = im.size; px = im.load()
def dbz(lo, la):
    x, y = int(round((lo + 126) / 0.005)), int(round((50 - la) / 0.005))
    if not (0 <= x < W and 0 <= y < H): return None
    v = px[x, y]; return None if v == 0 else v * 0.5 - 32.5
# 1) coarse scan of the lower 48 using IEM's numbers to find the strongest echoes
hot = []
for la10 in range(250, 495, 5):
    for lo10 in range(-1245, -670, 5):
        z = dbz(lo10 / 10, la10 / 10)
        if z is not None and z >= 35: hot.append((z, lo10 / 10, la10 / 10))
hot.sort(reverse=True); centers = hot[:40]
# 2) dense samples around them (0.01 deg grid, 21 x 21), plus a sparse national set
pts = []
for _, lo, la in centers: pts += [[round(lo + (i - 10) * 0.01, 3), round(la + (j - 10) * 0.01, 3)] for i in range(21) for j in range(21)]
pts += [[round(-124 + 57 * i / 49, 3), round(25 + 24 * j / 49, 3)] for i in range(50) for j in range(50)]
pairs = collections.defaultdict(list)
for (lo, la), col in samples(pts, ms):
    z = dbz(lo, la)
    if z is not None and not col.startswith('0 0 0'): pairs[col].append(z)
path = 'data/radar_calib.json'
db = json.load(open(path)) if os.path.exists(path) else {'colors': {}, 'runs': 0}
for c, zs in pairs.items(): db['colors'].setdefault(c, []).extend(round(z, 1) for z in zs); db['colors'][c] = db['colors'][c][-400:]
db['runs'] += 1; db['updated'] = dt.datetime.utcnow().isoformat() + 'Z'; db['maxEchoLastRun'] = centers[0][0] if centers else None
json.dump(db, open(path, 'w'))
print('strongest echo', db['maxEchoLastRun'], 'dBZ; colours this run', len(pairs), '; total colours', len(db['colors']))
