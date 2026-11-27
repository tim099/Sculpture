# 蠍子號 步驟 7 讀數（TASK-0023）：引擎組出來的組裝件 vs 設計、桅的關聯 meta、帆桁模型與固定點回讀 ⇒ verify_step7_assembly.json
#   出處：步驟 5、6 的「引擎組出來的組裝件」比法（export format=list links=all；tools/wio.py）；模型與關聯照作品的 models.json／links.json 讀回（CLI 寫的檔）。
#   用法：python -I -X utf8 tools/check_masts.py
#   設計 ＝ 船殼 hull_01＋步驟 6 換色＋甲板-main（扣桅孔）＋船首平台＋spur＋艉台＋主桅（篷與帆桁是外部模型，不在格子清單裡）。
import json, os, sys
import numpy as np
from scipy import ndimage

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKS = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import wio
T = 'claude-galiot-01m'
PLAN = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))
YC = int(PLAN['space']['yc'])


def load(fn):
    a = np.loadtxt(os.path.join(HERE, fn), delimiter=',', comments='#', dtype=np.int32, ndmin=2)
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


want = load('masks/hull/hull_01.vox.txt')
want.update(load('masks/step6/hull_paint.vox.txt'))
hole = load('masks/masts/deck_hole.vox.txt')
want.update({k: c for k, c in load('masks/decks/deck_main.vox.txt').items() if k not in hole})
for fn in ('masks/decks/bow.vox.txt', 'masks/deco/spur.vox.txt', 'masks/deco/poop.vox.txt', 'masks/masts/main.vox.txt'):
    want.update(load(fn))
a = wio.export_list(T + '-assembly', None, links='all')
have = {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}
R = {'assembly': {'have': len(have), 'want': len(want), 'missing': sum(1 for k in want if k not in have), 'extra': sum(1 for k in have if k not in want),
                  'color_diff': sum(1 for k in want if k in have and have[k] != want[k])}}
S = np.zeros(tuple(int(v) + 2 for v in a[:, :3].max(axis=0)), bool)
S[a[:, 0], a[:, 1], a[:, 2]] = True
_, n = ndimage.label(S)
R['assembly']['components_6'] = int(n)
R['assembly']['cavities'] = int((ndimage.binary_fill_holes(S) & ~S).sum())
mm = {k: c for k, c in have.items() if k in load('masks/masts/main.vox.txt')}
R['assembly']['mast_cells_in_export'] = len(mm)

links = json.load(open(os.path.join(WORKS, T + '-assembly', 'links.json'), encoding='utf-8'))
masts = [l for l in links['links'] if (l.get('meta') or {}).get('kind') == 'mast']
R['mast_links'] = [{k: l.get(k) for k in ('name', 'work', 'at', 'turn', 'mirror', 'meta')} for l in masts]
mod = json.load(open(os.path.join(WORKS, T + '-mast-main', 'models.json'), encoding='utf-8'))
R['yard_models'] = [{k: m.get(k) for k in ('name', 'work', 'at', 'pivot', 'rotate', 'scale', 'meta')} for m in mod.get('models', [])]
R['sub_works'] = {}
for w in ('mast-main', 'yard-main'):
    wj = json.load(open(os.path.join(WORKS, T + '-' + w, 'work.json'), encoding='utf-8'))
    R['sub_works'][w] = {k: wj.get(k) for k in ('size_x', 'size_y', 'size_z', 'meters_per_voxel', 'tags', 'parent_work')}
anc = json.load(open(os.path.join(WORKS, T + '-yard-main', 'anchors.json'), encoding='utf-8'))['anchors']
YL = json.load(open(os.path.join(HERE, 'yards_lateen.json'), encoding='utf-8'))['main']
got = {a['name']: [int(round(v - 0.5)) if isinstance(v, float) and v % 1 else int(v) for v in a['at']] for a in (anc if isinstance(anc, list) else [dict(v, name=k) for k, v in anc.items()])}
R['yard_anchors'] = {'count': len(got), 'design': len(YL['anchors']), 'same_cells': sum(1 for k, v in YL['anchors'].items() if got.get(k) == v),
                     'pivot': got.get('pivot'), 'fore': got.get('fore'), 'peak': got.get('peak')}
pl = json.load(open(os.path.join(HERE, 'yards_placement.json'), encoding='utf-8'))[0]
ym = next((m for m in R['yard_models'] if m['name'] == pl['name']), None)
R['checks'] = {
    'one_kind_mast_link': len(masts) == 1 and masts[0]['meta'].get('mast') == 'main',
    'yard_meta_mast_matches_link': bool(ym) and ym['meta'].get('mast') == masts[0]['meta'].get('mast'),
    'yard_meta_equals_design': bool(ym) and ym['meta'] == pl['meta'],
    'yard_at_pivot_equal_design': bool(ym) and [float(v) for v in ym['at']] == pl['at'] and [float(v) for v in ym['pivot']] == pl['pivot'],
    'yard_anchors_equal_design': R['yard_anchors']['same_cells'] == R['yard_anchors']['design'] == R['yard_anchors']['count'],
    'mast_link_turn0_no_mirror': len(masts) == 1 and not masts[0].get('turn') and masts[0].get('mirror') in (None, '', 'none'),
}
with open(os.path.join(HERE, 'verify_step7_assembly.json'), 'w', encoding='utf-8', newline='\n') as f:
    json.dump(R, f, ensure_ascii=False, indent=1)
print(json.dumps(R, ensure_ascii=False))
