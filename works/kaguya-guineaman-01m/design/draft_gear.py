# 出處：erina-oxford-01m/design/draft_gear.py（2026-11-01 複製；作品 id、persona、船名、單號已換）
# 幾內亞船 步驟 10（TASK-1149）：火藥庫（下層甲板船尾的牆＋門）、火藥桶、艙口格柵、爐灶（廚房）、絞盤、羅經櫃、小艇
#   跟牛津號不同：火藥庫可以不砌後牆（`magazine.aft_wall`，照好旅號）；艙口不蓋艙蓋、鋪格柵（`gear.gratings`：奴隸船的格柵艙口，
#   做法照風暴角號 draft_capstan_grating.py —— 0.05 m 子作品、1 格條 1 格空、外部模型 scale 0.5、kind=grating）
#   輸入：plan.json（gear）＋ 組裝件現在的格子（CLI 匯出，藏掉本階段自己的關聯）＋ parts（砲模型的外框）
#   輸出：masks/gear/magazine.vox.txt（火藥庫子作品，世界座標）、masks/gear/<格柵>.vox.txt（格柵子作品自己的座標）、
#         gear_placement.json（每個模型：放在哪件甲板、at、pivot、scale、meta）、verify_gear.json
#   用法：python -I -X utf8 draft_gear.py <design> [--probe=shift=<模型或格柵名>:<dx>]（反向對照：把一件往 x 推幾格，看碰撞報不報；⛔ 不寫檔）
#   做法參考 calli-cosecha-01m/design/draft_gear.py（模型自動量 z、取樣點不落在實心格）；火藥庫照 Ship_Magazine §8、艙蓋照 Ship_Fittings §9.7。
import sys, os, json, math, subprocess, tempfile
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
import lines as HL
from wio import export_list

HULL = 'kaguya-guineaman-01m'
ASM = HULL + '-assembly'
WORKS = None


def src_cells(work):
    return export_list(work, None)[:, :3].astype(float)


def parts_boxes():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace('\\', '/')
        subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + ASM, '--arg', 'out=' + out],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
        P = json.load(open(out, encoding='utf-8'))
    return {m['path']: m['box'] for m in P['models']}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    probe = [a.split('=', 1)[1] for a in sys.argv[2:] if a.startswith('--probe')]
    plan = HL.load_plan(design)
    L = HL.Lines(plan)
    YC = L.YC
    GE = plan['gear']
    lk = json.load(open(os.path.join(os.path.dirname(os.path.dirname(design if os.path.isabs(design) else os.path.abspath(design))), ASM, 'links.json'), encoding='utf-8'))
    names = {l['name'] for l in lk.get('links', lk)}
    hide = ','.join(n for n in ('彈藥庫',) if n in names)
    A = export_list(ASM, None, links=None, hide_links=hide or None)
    occ = set(map(tuple, A[:, :3].astype(int).tolist()))
    boxes = parts_boxes()
    own_models = set()
    for g in GE['models'] + GE.get('gratings', []):
        own_models.add(g['host_link'] + '/' + g['name'])
    gun_boxes = {p: b for p, b in boxes.items() if p not in own_models}
    # ── 火藥庫的牆（世界座標）──
    M = GE['magazine']
    x0, x1 = M['x_aft'], M['x_fwd']
    zf = plan['decks']['orlop']['z'] + 1                       # 底艙平台第一層空氣
    xs = np.arange(0, plan['space']['x'])
    wall = {}
    for x in ((x0, x1) if M.get('aft_wall', True) else (x1,)):          # 照好旅號：不砌後牆（後牆會把船尾那一段封成空腔）⇒ 火藥庫往後一直到船殼
        ztop = int(math.floor(float(L.gun_z(x + 0.5)))) - 1      # 炮甲板板子底下那一格
        for z in range(zf, ztop + 1):
            h = float(L.hb(np.array([x + 0.5]), np.array([z + 0.5]))[0])
            if h < 0:
                continue
            for y in range(YC - int(h), YC + int(h) + 1):
                if (x, y, z) in occ:
                    continue
                if x == x1 and abs(y - YC) <= M['door_half'] and z < zf + M['door_h']:
                    continue
                wall[(x, y, z)] = M['color']
    # 牆只留船殼裡面那一段（外面那幾格是船殼本身 ⇒ 已經跳過；剩下的要連到船殼或甲板）
    # ── 房間裡的空氣 ⇒ blast；門 ⇒ door ──
    air = [(x, y, z) for x in range(x0 + 1, x1) for z in range(zf, zf + 12) for y in range(YC - 30, YC + 31)
           if (x, y, z) not in occ and float(L.hb(np.array([x + 0.5]), np.array([z + 0.5]))[0]) - 3 >= abs(y - YC)]
    c = np.array(air, float).mean(0)
    blast = min(air, key=lambda p: (p[0] - c[0]) ** 2 + (p[1] - c[1]) ** 2 + (p[2] - c[2]) ** 2)
    anchors = {'blast': list(blast), 'door': [x1, YC, zf]}
    # ── 艙口格柵（照風暴角號：本地 z 0–1 ＝ 中線縱橫各一根 hatch bar、z 2 橫條、z 3 縱條 ⇒ 從上面看 x 偶 或 y 偶 是條、奇奇是洞；
    #    外部模型 pivot 0、scale 0.5 ⇒ 本地格 l 落在世界 at ＋ l // 2；格柵頂 ＝ 圍板頂）──
    GC = GE.get('grating_colors', {})
    grat, gsolid, grows = {}, set(), []
    for g in GE.get('gratings', []):
        NX, NY = g['open'][0] * 2, g['open'][1] * 2
        cells = {}
        for lx in range(NX):
            for ly in range(NY):
                if ly % 2 == 0: cells[(lx, ly, 2)] = GC['cross']
                if lx % 2 == 0: cells[(lx, ly, 3)] = GC['long']
        for lx in range(NX):
            for z in (0, 1): cells[(lx, NY // 2 - 1, z)] = cells[(lx, NY // 2, z)] = GC['bar']
        for ly in range(NY):
            for z in (0, 1): cells[(NX // 2 - 1, ly, z)] = cells[(NX // 2, ly, z)] = GC['bar']
        at = list(g['at'])
        if probe and probe[0].split('=')[1].split(':')[0] == g['name']:
            at[0] += int(probe[0].split(':')[1])
        wc = {(at[0] + lx // 2, at[1] + ly // 2, at[2] + lz // 2) for lx, ly, lz in cells}
        hit = sorted(wc & occ)
        # 圍板頂那一圈（開口外一格）要全是實心；格柵頂（世界）＝ 圍板頂 ＋ 1
        x0g, y0g, x1g, y1g = g['at'][0] - 1, g['at'][1] - 1, g['at'][0] + g['open'][0], g['at'][1] + g['open'][1]
        ring = [(x, y, g['coaming_top']) for x in range(x0g, x1g + 1) for y in (y0g, y1g)] + [(x, y, g['coaming_top']) for x in (x0g, x1g) for y in range(y0g + 1, y1g)]
        r = {'name': g['name'], 'size': [NX, NY, 4], 'cells': len(cells), 'hit_world': len(hit), 'world_top': max(k[2] for k in wc) + 1,
             'coaming_ring_solid': sum(1 for k in ring if k in occ), 'coaming_ring': len(ring)}
        grows.append(r)
        grat[g['name']] = cells
        gsolid |= wc
    # ── 模型擺放：自動量 z（腳下那一層甲板的頂）、取樣點（格心＋八角往裡縮 0.2）不落在實心格、不進砲的外框 ──
    def corners(cells):
        o = np.array([[0.5, 0.5, 0.5]] + [[(0.2, 0.8)[k & 1], (0.2, 0.8)[(k >> 1) & 1], (0.2, 0.8)[(k >> 2) & 1]] for k in range(8)])
        return (cells[:, None, :] + o[None]).reshape(-1, 3)
    cache = {}
    rows, bad = [], []
    for g in GE['models']:
        w = g['source_work']
        if w not in cache:
            cache[w] = corners(src_cells(w))
        P0 = cache[w]
        piv = np.array(g['pivot'], float)
        sc = np.array(g['scale'] if isinstance(g['scale'], list) else [g['scale']] * 3, float)
        at = np.array(g['at'], float)
        if probe and probe[0].split('=')[1].split(':')[0] == g['name']:
            at[0] += float(probe[0].split(':')[1])
        Pw = (P0 - piv) * sc + at
        hit = sum(1 for p in np.floor(Pw).astype(int).tolist() if tuple(p) in occ or tuple(p) in wall or tuple(p) in gsolid)
        lo, hi = Pw.min(0), Pw.max(0)
        gun_hit = [p for p, b in gun_boxes.items() if not (hi[0] <= b[0] or lo[0] >= b[3] or hi[1] <= b[1] or lo[1] >= b[4] or hi[2] <= b[2] or lo[2] >= b[5])]
        # 腳下：最底下那層取樣點正下方 1 格是實心的比例
        bot = Pw[Pw[:, 2] <= lo[2] + 0.25]
        sup = float(np.mean([any(tuple(np.floor(p - [0, 0, 1]).astype(int)) in S for S in (occ, wall, gsolid)) for p in bot]))
        r = {'name': g['name'], 'host': g['host'], 'hit_samples': hit, 'gun_box_overlap': gun_hit, 'support': round(sup, 2),
             'box': [round(v, 2) for v in list(lo) + list(hi)]}
        rows.append(r)
        if hit or gun_hit or (g.get('need_support', True) and sup < 0.5):
            bad.append(r)
    gbad = [r for r in grows if r['hit_world'] or r['coaming_ring_solid'] < r['coaming_ring']]
    R = {'magazine_wall_cells': len(wall), 'anchors': anchors, 'air_cells': len(air), 'models': rows, 'gratings': grows, 'problems': bad + gbad,
         'powder_lb': 100 * sum(1 for g in GE['models'] if g['meta'].get('kind') == 'powder')}
    if probe:
        print(json.dumps({'probe': probe[0], 'problems': [(b['name'], b['hit_samples'], b['gun_box_overlap']) for b in bad] +
                          [(b['name'], b['hit_world'], '圍板 %d／%d' % (b['coaming_ring_solid'], b['coaming_ring'])) for b in gbad]}, ensure_ascii=False))
        return
    od = os.path.join(design, 'masks', 'gear')
    os.makedirs(od, exist_ok=True)
    with open(os.path.join(od, 'magazine.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 幾內亞船 火藥庫（%s；世界座標，at 0,0,0）\n' % ('前後兩道牆＋門' if GE['magazine'].get('aft_wall', True) else '前牆＋門，往後到船殼'))
        for k in sorted(wall):
            f.write('%d,%d,%d,%d\n' % (k + (wall[k],)))
    gplace = []
    for g in GE.get('gratings', []):
        fn = g['work_suffix'] + '.vox.txt'
        with open(os.path.join(od, fn), 'w', encoding='utf-8', newline='\n') as f:
            f.write('# %s —— draft_gear.py 產；子作品自己的座標（%d 格）\n' % (g['title'], len(grat[g['name']])))
            for k in sorted(grat[g['name']]):
                f.write('%d,%d,%d,%d\n' % (k + (grat[g['name']][k],)))
        gplace.append({'name': g['name'], 'work': HULL + '-' + g['work_suffix'], 'title': g['title'], 'host': g['host'], 'host_link': g['host_link'],
                       'file': 'masks/gear/' + fn, 'size': [g['open'][0] * 2, g['open'][1] * 2, 4], 'cells': len(grat[g['name']]),
                       'at': g['at'], 'pivot': [0, 0, 0], 'scale': 0.5, 'meta': {'kind': 'grating'}})
    json.dump({'anchors': anchors, 'models': GE['models'], 'gratings': gplace, 'magazine_meta': dict(GE['magazine']['meta'], powder_lb=R['powder_lb'])},
              open(os.path.join(design, 'gear_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(R, open(os.path.join(design, 'verify_gear.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v for k, v in R.items() if k not in ('models', 'gratings')}, ensure_ascii=False))
    for r in rows:
        print(' ', r['name'], 'hit', r['hit_samples'], 'gun', len(r['gun_box_overlap']), 'support', r['support'], 'box', r['box'])
    for r in grows:
        print(' ', r['name'], 'cells', r['cells'], 'hit', r['hit_world'], 'top', r['world_top'], '圍板', '%d／%d' % (r['coaming_ring_solid'], r['coaming_ring']))


if __name__ == '__main__':
    main()
