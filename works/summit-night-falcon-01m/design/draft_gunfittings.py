# 階段十四：砲具與砲索 —— 船牆與甲板上的環首螺栓（一件子作品，一舷＋鏡像）＋每門 5 條繩
# 設計 plan.json gunfittings（出處 provenance gunfittings.*）；砲 verify_guns.json（階段十三）；現況 nf_state stage12（砲具加進來之前，全部子作品）。
# 環只算 S 舷（y > 80），P 舷用 mirror=y 關聯；組裝件左右差 0（階段十三 stats）⇒ 每個量測在 P 舷鏡過去再量一次，兩邊都過才放。
#   · 船牆上的環：砲門開口外側（aft：x0−1−off、fwd：x1+1+off）、甲板頂格 ＋4 那一層，牆內面第一格空氣；
#     要求：那一格空、不在任何一門砲（模型）裡；繩 cascabel → 環、eye-aft／fwd → 環 不穿過別的實心、不穿過別門砲。
#   · 甲板上的環：train 往船裡 back 格、甲板頂格 ＋1；正下方要是甲板；train → 環 不穿過實心。
#   · 自己這門砲的網格不算擋（實船 breeching 穿過 cheek 上的孔、tackle 掛在 cheek 外側）。
# 輸出：masks/gunfittings/side.vox.txt（子作品座標）、verify_gunfittings.json（stamp_order、anchors、ropes、讀數）
# 用法：python -I -X utf8 -B draft_gunfittings.py <design 資料夾>
import sys, os, json, hashlib
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(__file__))
sys.path.insert(0, D)
from nf_state import state_after, occupancy, NX, NY, NZ

plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
F = plan['gunfittings']
VG = json.load(open(os.path.join(D, 'verify_guns.json'), encoding='utf-8'))
W = state_after(D, 'stage12')
occ = occupancy(W)
H = W['hull']

# ── 每門砲佔的世界格（模型取樣點落到的格）＋ 世界座標的固定點 ──
gcells = [tuple(map(int, l.split(',')[:3])) for l in open(os.path.join(D, VG['gun']['file']), encoding='utf-8') if not l.startswith('#')]
gc = np.array(gcells, float)
offs = np.array([[0.5, 0.5, 0.5]] + [[0.15 + 0.7 * (k & 1), 0.15 + 0.7 * ((k >> 1) & 1), 0.15 + 0.7 * ((k >> 2) & 1)] for k in range(8)])
samp = (gc[:, None, :] + offs[None]).reshape(-1, 3)
piv = np.array(VG['gun']['pivot']); S = VG['scale']


def to_world(Q, r):
    q = (np.asarray(Q, float) - piv) * S
    if r['mirror'] == 'y':
        q[..., 1] = -q[..., 1]
    return q + np.array(r['at'])


guns = {}
for r in VG['rows']:
    w = np.floor(to_world(samp, r)).astype(int)
    pts = {k: to_world(np.array(v, float) + 0.5, r) for k, v in VG['gun']['anchors'].items()}
    guns[r['model']] = {'row': r, 'cells': set(map(tuple, w)), 'pts': pts}
allgun = set().union(*(g['cells'] for g in guns.values()))


def mir(k):
    return (k[0], 160 - k[1], k[2])


def mirc(v):
    return np.array([v[0], 161 - v[1], v[2]])


def line_hits(a, b, own, allow):
    """a→b（連續座標）經過的格：實心（allow 不算）或別門砲（own 不算）。"""
    a, b = np.asarray(a, float), np.asarray(b, float)
    n = int(np.linalg.norm(b - a) * 4) + 2
    hit = set()
    for t in np.linspace(0, 1, n):
        q = tuple(int(np.floor(v)) for v in a + (b - a) * t)
        if q in allow:
            continue
        if occ[q] or (q in allgun and q not in own):
            hit.add(q)
    return sorted(hit)


def build():
    R = F['ring']; DR = F['deck_ring']
    pr = plan['decks']['ports']
    cells, anchors, ropes, notes, rows = {}, [], [], [], []
    for n, st in enumerate(pr['stations'], 1):
        gS, gP = guns[f'砲-S{n}'], guns[f'砲-P{n}']
        r = gS['row']
        dt = r['deck_top']
        x0, x1 = r['opening_x']
        z = dt + R['z_above_deck']
        row = {'n': n, 'rings': {}, 'deck_ring': None}
        for side, sg, xe in (('aft', -1, x0 - 1), ('fwd', 1, x1 + 1)):
            done = None
            for off in R['offset']:
                x = xe + sg * off
                ys = [y for y in range(R['wall_scan_from'], NY) if H[x, y, z]]
                if not ys:
                    continue
                k = (x, ys[0] - 1, z)
                if occ[k] or k in allgun or occ[mir(k)] or mir(k) in allgun:
                    continue
                kc = np.array(k) + 0.5
                h = line_hits(gS['pts']['cascabel'], kc, gS['cells'], {k}) + line_hits(gS['pts']['eye-' + side], kc, gS['cells'], {k}) \
                    + line_hits(gP['pts']['cascabel'], mirc(kc), gP['cells'], {mir(k)}) + line_hits(gP['pts']['eye-' + side], mirc(kc), gP['cells'], {mir(k)})
                if h:
                    continue
                done = (off, k)
                break
            if done is None:
                notes.append(f'砲門 {n} 的 {side} 環：offset {R["offset"]} 都不行 ⇒ 不放，那一側 breeching／tackle 不掛')
                continue
            off, k = done
            cells[k] = R['color']
            nm = f'ring-{n}-{side}'
            anchors.append({'name': nm, 'kind': 'ring', 'world': list(k), 'gun': n, 'side': side})
            row['rings'][side] = {'offset': off, 'cell': list(k)}
        tr = gS['pts']['train']
        for back in DR['back']:
            k = (int(np.floor(tr[0])), int(np.floor(tr[1])) - back, dt + 1)
            if occ[k] or k in allgun or not occ[(k[0], k[1], dt)] or occ[mir(k)] or mir(k) in allgun or not occ[(k[0], 160 - k[1], dt)]:
                continue
            kc = np.array(k) + 0.5
            if line_hits(tr, kc, gS['cells'], {k}) or line_hits(gP['pts']['train'], mirc(kc), gP['cells'], {mir(k)}):
                continue
            cells[k] = DR['color']
            anchors.append({'name': f'deck-{n}', 'kind': 'deck_ring', 'world': list(k), 'gun': n})
            row['deck_ring'] = {'back': back, 'cell': list(k)}
            break
        if row['deck_ring'] is None:
            notes.append(f'砲門 {n} 的甲板環找不到位置 ⇒ train tackle 不掛')
        rows.append(row)
    # ── 繩（掛在組裝件；端點 model:甲板-主/砲-XN/<點>、砲具／砲具-鏡像/<環>）──
    RP = F['ropes']
    for row in rows:
        n = row['n']
        for sd, fl in (('S', '砲具'), ('P', '砲具-鏡像')):
            g = f'model:甲板-主/砲-{sd}{n}'
            for side in ('aft', 'fwd'):
                if side not in row['rings']:
                    continue
                ring = f'{fl}/ring-{n}-{side}'
                ropes.append(dict(name=f'砲-{sd}{n}.breeching-{side}', **{'from': g + '/cascabel', 'to': ring}, **RP['breeching'], group='guns/breeching'))
                ropes.append(dict(name=f'砲-{sd}{n}.tackle-{side}', **{'from': f'{g}/eye-{side}', 'to': ring}, **RP['tackle'], group='guns/tackle'))
            if row['deck_ring']:
                ropes.append(dict(name=f'砲-{sd}{n}.train', **{'from': g + '/train', 'to': f'{fl}/deck-{n}'}, **RP['train'], group='guns/train'))
    return cells, anchors, ropes, notes, rows


def main():
    cells, anchors, ropes, notes, rows = build()
    fa = np.array(F['frame_at']); fs = np.array(F['frame_size'])
    for k in cells:
        assert all(fa <= np.array(k)) and all(np.array(k) < fa + fs), ('框外', k)
        assert k[1] > 80
    path = os.path.join(D, 'masks', 'gunfittings', 'side.vox.txt')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    txt = '# 夜隼號砲具（一舷，S）draft_gunfittings.py —— 子作品座標 x,y,z,color；世界 ＝ ＋frame_at\n' + \
          ''.join(f'{k[0] - fa[0]},{k[1] - fa[1]},{k[2] - fa[2]},{c}\n' for k, c in sorted(cells.items()))
    open(path, 'w', encoding='utf-8', newline='\n').write(txt)
    for a in anchors:
        a['at'] = [int(v) for v in np.array(a['world']) - fa]
    out = {'note': 'draft_gunfittings.py（階段十四）—— 現況 nf_state stage12＋verify_guns.json',
           'work': F['work'], 'frame_at': F['frame_at'], 'frame_size': F['frame_size'],
           'links': [{'name': '砲具', 'at': F['frame_at'], 'mirror': ''},
                     {'name': '砲具-鏡像', 'at': [F['frame_at'][0], 161 - F['frame_at'][1] - F['frame_size'][1], F['frame_at'][2]], 'mirror': 'y'}],
           'stamp_order': {'fittings': [{'name': 'gunfittings_side', 'op': 'stampvox', 'file': 'masks/gunfittings/side.vox.txt', 'at': [0, 0, 0],
                                         'origin_world': F['frame_at'], 'voxels': len(cells), 'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest()}]},
           'anchors': anchors, 'ropes': ropes, 'rows': rows, 'notes': notes,
           'counts': {'ring_cells': len(cells), 'anchors': len(anchors), 'ropes': len(ropes)}}
    with open(os.path.join(D, 'verify_gunfittings.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for row in rows:
        print(row['n'], {s: (v['offset'], v['cell']) for s, v in row['rings'].items()}, 'deck', row['deck_ring'])
    print('cells', len(cells), 'anchors', len(anchors), 'ropes', len(ropes))
    for m in notes:
        print('⚠', m)


if __name__ == '__main__':
    main()
