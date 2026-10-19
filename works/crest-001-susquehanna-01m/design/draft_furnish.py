# 蘇士奎哈納號 甲板陳設（造船規格 §9.9 裝飾 deco=1；Tim 2026-10-20「然後可以參考拿破崙號 加上一些裝飾細節」）
#   照拿破崙號 kotoko-napoleon-01m/design/draft_furnish.py（階段十五）—— 三件直接引用 kotoko 的子作品當外部模型（§2.1，⛔ 不重做）：
#     錨鏈繫纜柱 kotoko-napoleon-01m-bitts、桅腳繫索栓圍欄 -fiferail、砲彈架 -shotrack（都是 0.05 m，掛本船 0.1 m ⇒ scale 0.5；pivot 照她的）。
#   ⛔ 爐灶不放：§9.13 起爐灶標 kind=galley 是有功能的廚房（生廚師、加 buff），不是裝飾 —— 要不要給這艘船廚房另外決定。
#   擺在哪（設計決定；本船只有露天砲甲板一層開放甲板，全部放在甲板-gun）：
#     繫索栓圍欄：前桅、主桅、後桅三根，框的中心 ＝ 桅軸（拿破崙號只放主桅、前桅；本船三根桅都在露天甲板上）。
#     繫纜柱：中線、前迴旋砲（x 806）與 cathead（x 868）之間，離 target 最近的；前迴旋砲往船頭轉 45° 掃過的範圍另外留空（下面 PIVOT_KEEP）。
#     砲彈架：後艙口（x 350–366）兩舷圍欄外側 —— 8 吋舷側砲（x 300–412）就在旁邊；P 舷 mirror=y。
#   現況 ＝ 組裝件 links=all 的格 ＋ 所有模型外框（本程式自己掛的除外）；取樣點（每格格心＋八角）不落在現況、梯子端點保留區；腳下：底層每格正下方是實心。
#   輸出：furnish_placement.json、verify_furnish.json。用法：python -I -X utf8 draft_furnish.py <design>
#         apply：python -I -X utf8 draft_furnish.py <design> apply（照 furnish_placement.json 掛模型；已發過的物件 id 照留）
import sys, os, json, math, tempfile, subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import layout as LY
import mio as DB

PERSONA = 'crest-001'
HOST = 'crest-001-susquehanna-01m-deck-gun'
NX, NY, NZ = 1300, 400, 260
OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.3 + 0.4 * (k & 1), 0.3 + 0.4 * ((k >> 1) & 1), 0.3 + 0.4 * ((k >> 2) & 1)] for k in range(8)])
SC = 0.5                                                                  # 子作品 0.05 m ⇒ 船上 0.1 m
DECO = {'deco': 1}
SRC = {'bitts': 'kotoko-napoleon-01m-bitts', 'fiferail': 'kotoko-napoleon-01m-fiferail', 'shotrack': 'kotoko-napoleon-01m-shotrack'}
PIV = {'bitts': [7.5, 20.5, 0], 'fiferail': [19.5, 19.5, 0], 'shotrack': [27.0, 0.0, 0]}    # 照拿破崙號 furnish_placement.json pieces
# 前迴旋砲（砲-10in-前S／前P，ports 0 與往船頭 45°）轉起來掃過的地方：照兩個砲門角度的砲外框聯集再外擴 4 格（設計決定：外框只是現在那一個角度）
PIVOT_KEEP = 4


def sculpt(args):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')


def parts():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace('\\', '/')
        r = sculpt(['op=export', 'format=parts', 'work=' + DB.ASM, 'out=' + out])
        if r.returncode != 0:
            raise SystemExit(r.stdout[-800:])
        return json.load(open(out, encoding='utf-8'))['models']


def main(design):
    plan = HL.load_plan(design)
    A = DB.export_list(DB.ASM, 'all')
    A = A[A[:, 2] < NZ]
    occ = np.zeros((NX, NY, NZ), bool)
    occ[A[:, 0], A[:, 1], A[:, 2]] = True
    solid = occ.copy()                                                    # 腳下只看格子
    own = {'甲板-gun/' + n for n in ('繫纜柱', '繫索栓圍欄-fore', '繫索栓圍欄-main', '繫索栓圍欄-mizzen', '砲彈架-S', '砲彈架-P')}
    PM = [m for m in parts() if m['path'] not in own]                    # 本程式自己掛的不算（套用之後重跑讀到的還是同一份）
    for m in PM:
        b = m['box']
        occ[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
            max(0, int(math.floor(b[2]))):min(NZ, int(math.ceil(b[5])))] = True
    keep = []
    for m in PM:                                                          # 前迴旋砲轉 45° 的範圍：外框繞砲的 pivot 轉到每個砲門角度，取聯集
        mt = m.get('meta') or {}
        if mt.get('mount') != 'pivot' or mt.get('side') == 'C':
            continue
        b = m['box']
        cx, cy = (b[0] + b[3]) / 2, (b[1] + b[4]) / 2
        corners = np.array([[x, y] for x in (b[0], b[3]) for y in (b[1], b[4])], float) - [cx, cy]
        pts = []
        for a in [float(v) for v in str(mt.get('ports', '0')).split(',')]:
            t = math.radians(a)
            pts.append(corners @ np.array([[math.cos(t), math.sin(t)], [-math.sin(t), math.cos(t)]]) + [cx, cy])
        P = np.vstack(pts)
        x0, y0 = np.floor(P.min(0)).astype(int) - PIVOT_KEEP
        x1, y1 = np.ceil(P.max(0)).astype(int) + PIVOT_KEEP
        occ[max(0, x0):x1, max(0, y0):y1, int(math.floor(b[2])):int(math.ceil(b[5]))] = True
        keep.append({'gun': m['path'], 'x': [int(x0), int(x1)], 'y': [int(y0), int(y1)]})
    reserved = np.zeros((NX, NY), bool)                                   # 甲板-gun 的梯子端點前後 6、兩側 4 格
    LP = json.load(open(os.path.join(design, 'ladder_points.json'), encoding='utf-8'))
    for nm, L in sorted(LP.items()):
        for end, deck in (('head', L['up']), ('foot', L['lo'])):
            if deck == 'gun':
                x, y, _ = L['points'][end]
                reserved[x - 6:x + 7, y - 4:y + 5] = True
    yc = plan['space']['yc'] + 0.5

    src = {k: DB.export_list(w, None)[:, :3] for k, w in SRC.items()}

    def world(Q, piv, at, mir):
        q = (Q - np.asarray(piv, float)) * SC
        if mir:
            q[:, 1] = -q[:, 1]
        return q + np.asarray(at, float)

    def test(k, at, mir):
        cells = src[k].astype(float)
        W = world((cells[:, None, :] + OFFS[None]).reshape(-1, 3), PIV[k], at, mir)
        i = np.floor(W).astype(int)
        if (i < 0).any() or (i[:, 2] >= NZ).any() or occ[i[:, 0], i[:, 1], i[:, 2]].any() or reserved[i[:, 0], i[:, 1]].any():
            return None
        bot = cells[cells[:, 2] == 0]
        b = np.floor(world(bot + [0.5, 0.5, 0.5], PIV[k], at, mir)).astype(int)
        sup = int(solid[b[:, 0], b[:, 1], b[:, 2] - 1].sum())
        lo, hi = W.min(0), W.max(0)
        return {'support': [sup, len(b)], 'box': [round(float(v), 3) for v in list(lo) + list(hi)]}

    def commit(k, at, mir):
        cells = src[k].astype(float)
        i = np.floor(world((cells[:, None, :] + OFFS[None]).reshape(-1, 3), PIV[k], at, mir)).astype(int)
        occ[i[:, 0], i[:, 1], i[:, 2]] = True

    def zd(x):
        return float(LY.deck_z(plan, 'gun', x)) + 1.0

    rows, log = [], {}

    def put(k, name, xs, target, ys=(0.0,), mirror=False, full=True):
        cands = []
        for x in xs:
            for dy in ys:
                at = [x, yc + dy, zd(x)]
                r = test(k, at, mirror)
                if r and (r['support'][0] == r['support'][1] if full else r['support'][0] > 0):
                    cands.append((abs(x - target) + abs(dy) * 0.01, at, r))
        assert cands, '%s 擺不下' % name
        _, at, r = min(cands, key=lambda c: (c[0], c[1][0], c[1][1]))
        commit(k, at, mirror)
        rows.append({'model': name, 'piece': k, 'source_work': SRC[k], 'host_work': HOST, 'path': '甲板-gun/' + name,
                     'at': [round(v, 3) for v in at], 'mirror': 'y' if mirror else 'none', 'pivot': PIV[k], 'scale': SC, 'meta': DECO,
                     'candidates': len(cands), **r})
        log[name] = [min(c[1][0] for c in cands), max(c[1][0] for c in cands)]

    def halves(a, b):
        return [a + k * 0.5 for k in range(int((b - a) / 0.5) + 1)]

    for key in ('mizzen', 'main', 'fore'):
        mx0 = next(m['x'] for m in plan['masts']['rows'] if m['key'] == key)
        mx = float(LY.mast_axis_x(plan, key, zd(mx0)))
        put('fiferail', '繫索栓圍欄-' + key, [round(mx * 2) / 2.0], mx, full=False)
    put('bitts', '繫纜柱', halves(790, 862), 845)
    hz = next(h for h in plan['decks_build']['hatches'] if h['name'] == '後艙口')
    hx = (hz['x0'] + hz['x1'] + 1) / 2.0
    for side, mir in (('S', False), ('P', True)):
        sgn = -1 if mir else 1
        put('shotrack', '砲彈架-' + side, [hx], hx, ys=[sgn * (hz['half'] + d) for d in halves(1.5, 8)], mirror=mir)

    out = {'note': 'draft_furnish.py —— 現況 ＝ 組裝件 links=all（%d 格）＋ 模型外框 %d；前迴旋砲轉動範圍留空 %s' % (len(A), len(PM), keep),
           'rows': rows, 'ranges': log, 'sources': {k: {'work': w, 'cells': int(len(src[k]))} for k, w in SRC.items()}}
    for f, d in (('furnish_placement.json', {'rows': rows}), ('verify_furnish.json', out)):
        with open(os.path.join(design, f), 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(d, fh, ensure_ascii=False, indent=1, sort_keys=True)
            fh.write('\n')
    for r in rows:
        print(r['path'], 'at', r['at'], r['mirror'], 'support', r['support'], 'box', r['box'], '候選', r['candidates'])
    print('範圍', log, '留空', keep)


def apply(design):
    rows = json.load(open(os.path.join(design, 'furnish_placement.json'), encoding='utf-8'))['rows']
    have = {m['name']: m for m in json.load(open(os.path.join(os.path.dirname(design), '..', HOST, 'models.json'), encoding='utf-8'))['models']}

    def num(v):
        return ('%.3f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v
    for r in rows:
        meta = dict(r['meta'])
        old = (have.get(r['model']) or {}).get('meta') or {}
        if 'id' in old:
            meta['id'] = old['id']                                       # 已經發過的物件 id 照留（§12.2）
        o = sculpt(['op=work', 'sub=model', 'persona=' + PERSONA, 'work=' + r['host_work'], 'name=' + r['model'], 'source_work=' + r['source_work'],
                    'at=' + ','.join(num(v) for v in r['at']), 'pivot=' + ','.join(num(float(v)) for v in r['pivot']), 'rotate=0,0,0',
                    'scale=' + num(r['scale']), 'mirror=' + r['mirror'], 'overwrite=1', 'meta=' + json.dumps(meta, ensure_ascii=False, sort_keys=True),
                    'note=蘇士奎哈納號 甲板陳設 %s（draft_furnish.py；引用拿破崙號 %s，§2.1；deco=1 §9.9）' % (r['model'], r['source_work'])])
        if o.returncode:
            raise SystemExit('✗ %s：%s' % (r['model'], (o.stdout + o.stderr)[-800:]))
        print('✓', r['model'])


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    d = os.path.abspath(sys.argv[1])
    (apply if len(sys.argv) > 2 and sys.argv[2] == 'apply' else main)(d)
