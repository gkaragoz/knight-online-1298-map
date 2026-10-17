"""Builds index.html from OpenKO-db SQL + client minimaps (DXT).
Usage: python3 build.py <OpenKO-db/ManualSetup> <ko-client-assets/Zones>
"""
import sys, os, io, json, base64
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))
from sqlparse import parse_inserts
from dxt2png import load, dds_wrap
from PIL import Image

sql_dir, zones_dir = sys.argv[1], sys.argv[2]
here = os.path.dirname(os.path.abspath(__file__))

raw = {}
for f in ['6_InsertData_K_NPCPOS.sql','6_InsertData_K_MONSTER.sql','6_InsertData_K_NPC.sql','6_InsertData_ZONE_INFO.sql']:
    for k, v in parse_inserts(os.path.join(sql_dir, f)).items(): raw.setdefault(k, []).extend(v)

# zone id -> (display name, minimap dxt stem or None, world size in units)
# minimap choice comes from the client Data/Zones.tbl (client id = zone*10); size from the server .smd header.
ZONES = {
  1:  ('Karus', 'karus2004', 2048), 2: ('El Morad', 'elmo2004', 2048),
  11: ('Karus Eslant', 'eslantzone', 1024), 12: ('El Morad Eslant', 'eslantzone', 1024),
  21: ('Moradon', 'moradon', 512), 30: ('Delos', 'war_a', 1024),
  32: ('Desperation Abyss', None, 512), 33: ('Hell Abyss', None, 512),
  51: ('Orc Prisoner Quest', 'clanfight_b', 256), 52: ('Blood Don Quest', 'clanfight_b', 256),
  53: ('Goblin Quest', 'clanfight_b', 256), 54: ('Cape Quest', 'clanfight_b', 256),
  55: ('Forgotten Temple', 'clanfight_b', 256),
  101: ('Lunar War', 'battlezone', 1024), 102: ('Dark Lunar War', 'battlezone_b', 1024),
  201: ('Colony Zone', 'freezone_b', 2048),
}

def jpeg_uri(stem):
    p = next(os.path.join(zones_dir, stem + e) for e in ('.dxt', '.DXT') if os.path.exists(os.path.join(zones_dir, stem + e)))
    w, h, fmt, mip, data = load(p)
    im = Image.open(io.BytesIO(dds_wrap(w, h, b'DXT1', data[:((w+3)//4)*((h+3)//4)*8]))).convert('RGB')
    b = io.BytesIO(); im.save(b, 'JPEG', quality=86, optimize=True)
    return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()

images = {s: jpeg_uri(s) for s in sorted({z[1] for z in ZONES.values() if z[1]})}

mon = {m['sSid']: m for m in raw['K_MONSTER']}
npc = {m['sSid']: m for m in raw['K_NPC']}
npcs, spawns = {}, {}
for r in raw['K_NPCPOS']:
    z = r['ZoneID']
    if z not in ZONES: continue
    is_npc = r['ActType'] >= 100          # same rule as AIServerApp::LoadNpcPosTable
    t = (npc if is_npc else mon).get(r['NpcID'])
    if not t: continue
    key = ('n' if is_npc else 'm') + str(r['NpcID'])
    npcs[key] = [t['strName'], t['sLevel'], t['iHpPoint'], t['iExp'], t['sAc'], t['sAtk'], 1 if is_npc else 0, t['bySearchRange']]
    spawns.setdefault(z, []).append([key,
        min(r['LeftX'], r['RightX']), min(r['TopZ'], r['BottomZ']),
        max(r['LeftX'], r['RightX']), max(r['TopZ'], r['BottomZ']),
        r['NumNPC'], r['RegTime']])

data = {
  'zones': [{'id': k, 'name': v[0], 'img': v[1], 'size': v[2]} for k, v in ZONES.items() if k in spawns],
  'images': images, 'npcs': npcs, 'spawns': {str(k): v for k, v in spawns.items()},
}
tpl = open(os.path.join(here, 'template.html'), encoding='utf-8').read()
out = tpl.replace('/*__DATA__*/', 'window.__DATA__ = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';')
open(os.path.join(here, 'index.html'), 'w', encoding='utf-8').write(out)
json.dump({k: v for k, v in data.items() if k != 'images'}, open(os.path.join(here, 'spawns.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('zones', len(data['zones']), 'unique npcs', len(npcs), 'slots', sum(len(v) for v in spawns.values()), 'html KB', len(out)//1024)
