# 三叉戟號 shot garland（TASK-0577）：同一層同一舷相鄰兩門砲之間、靠船牆內面，一條 2 格深的木條（136）＋ 每 shot_step 格一顆砲彈（36，放在木條上靠船裡那一格）
#   改自餘燼號 draft_gunfittings.py 的 garlands 段（basecamp；它照憲法號階段二十一）：離兩邊砲門中線各 clear 格、最長 max_len、甲板面上第一層空氣 ＋ z_above_deck。
#   每一欄都要：船殼內面在那一高度找得到（牆離砲門那一排的外緣 ≤ max_wall_depth）、木條兩格與砲彈都是空的（組裝件 links=all 藏本階段 ＋ 砲的實際格 ＋ 其他模型外框）。
#   四層（lower、middle、upper、spar）；只配舷側砲（船尾追擊砲不算相鄰）。每層一件子作品（整船框、at 0,0,0），關聯在那一層甲板子作品裡。
#   輸出：masks/garlands/<層>.vox.txt（世界座標）、verify_garlands.json。用法：python -I -X utf8 draft_garlands.py <design>
import sys, os, json, math, hashlib, tempfile, subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import deco_base as DB

NX, NY, NZ = 1100, 400, 260


def parts():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace(os.sep, '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + DB.ASM, '--arg', 'out=' + out],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            raise SystemExit(r.stdout[-800:])
        return json.load(open(out, encoding='utf-8'))['models']


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    D = os.path.abspath(sys.argv[1])
    plan = HL.load_plan(D)
    G = plan['garlands']
    C = G['colors']
    YC = plan['space']['yc']
    hide = ','.join('甲板-%s/%s' % (d, G['link']) for d in G['decks'])
    try:
        A = DB.export_list(DB.ASM, 'all', ('hide_links=' + hide,))
    except SystemExit:
        A = DB.export_list(DB.ASM, 'all')
    A = A[A[:, 2] < NZ]
    occ = np.zeros((NX, NY, NZ), bool)
    occ[A[:, 0], A[:, 1], A[:, 2]] = True
    vox = occ.copy()
    H = DB.export_list(DB.ASM, '船殼')
    H = H[H[:, 2] < NZ]
    hull = np.zeros((NX, NY, NZ), bool)
    hull[H[:, 0], H[:, 1], H[:, 2]] = True
    VG = json.load(open(os.path.join(D, 'verify_guns.json'), encoding='utf-8'))
    OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.15 + 0.7 * (k & 1), 0.15 + 0.7 * ((k >> 1) & 1), 0.15 + 0.7 * ((k >> 2) & 1)] for k in range(8)])
    tc = {}
    for r in VG['rows']:
        if r['type'] not in tc:
            cc = DB.export_list(VG['types'][r['type']]['work'], None)[:, :3].astype(float)
            tc[r['type']] = (cc[:, None, :] + OFFS[None]).reshape(-1, 3)
        q = (tc[r['type']] - np.array(r['pivot'], float)) * r['scale']
        if r['mirror'] == 'y':
            q[:, 1] = -q[:, 1]
        g = math.radians(r['rotate'][2])
        c_, s_ = round(math.cos(g), 12), round(math.sin(g), 12)
        w = np.floor(np.stack([q[:, 0] * c_ - q[:, 1] * s_, q[:, 0] * s_ + q[:, 1] * c_, q[:, 2]], 1) + np.array(r['at'], float)).astype(int)
        occ[w[:, 0], w[:, 1], w[:, 2]] = True
    nbox = 0
    for m in parts():
        if (m.get('meta') or {}).get('kind') == 'gun':
            continue
        b = m['box']
        occ[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
            max(0, int(math.floor(b[2]))):min(NZ, int(math.ceil(b[5])))] = True
        nbox += 1

    def wall(x, z, sgn):
        ys = range(YC + 15, NY) if sgn > 0 else range(YC - 15, -1, -1)
        for y in ys:
            if hull[x, y, z]:
                return y
        return None

    def floor_z(x, y, z_hi):
        """(x, y) 那一柱從 z_hi 往下第一格實心之上那一格（甲板面上第一層空氣）。"""
        for z in range(z_hi, 0, -1):
            if vox[x, y, z - 1]:
                return z
        return None

    cells, deck_of, rows, notes = {}, {}, [], []
    for deck in G['decks']:
        for side, sgn in (('S', 1), ('P', -1)):
            guns = sorted([r for r in VG['rows'] if r['host_link'] == '甲板-' + deck and 'port_x' in r and r['meta']['side'] == side], key=lambda r: r['meta']['port'])
            for a, b in zip(guns, guns[1:]):
                ca = (a['port_x'][0] + a['port_x'][1] + 1) / 2.0
                cb = (b['port_x'][0] + b['port_x'][1] + 1) / 2.0
                lo, hi = int(math.ceil(ca + G['clear'])), int(math.floor(cb - G['clear']))
                L = min(G['max_len'], hi - lo + 1)
                name = '甲板-%s/%s%02d-%02d' % (deck, side, a['meta']['port'], b['meta']['port'])
                if L < G['min_len']:
                    notes.append('%s：兩門之間只剩 %d 格 ⇒ 不放' % (name, hi - lo + 1))
                    continue
                x0 = (lo + hi) // 2 - L // 2
                zf = [floor_z(x, int(round(a['outer'])) - sgn * 12, int(round(a['deck_z'])) + 4) for x in range(x0, x0 + L)]
                if None in zf:
                    notes.append('%s：量不到甲板面 ⇒ 不放' % name)
                    continue
                zg = max(zf) + G['z_above_deck']
                cl, ok, why = [], True, ''
                for i, x in enumerate(range(x0, x0 + L)):
                    yw = wall(x, zg, sgn)
                    col = np.nonzero(hull[x, :, zg])[0]
                    col = col[col > YC] if sgn > 0 else col[col < YC]
                    oc = None if len(col) == 0 else (col.max() if sgn > 0 else col.min())     # 同一欄、同一高度的船殼最外那格
                    # 🩸 v1 拿前一門砲那一排的外緣當基準 ⇒ 船頭那一段船殼往內收，最靠船頭那一條兩舷都量成太深（8 條）
                    if yw is None or oc is None or abs(yw - oc) > G['max_wall_depth']:
                        ok, why = False, '牆找不到或太深'
                        break
                    cl += [((x, yw - sgn, zg), C['garland']), ((x, yw - 2 * sgn, zg), C['garland'])]
                    if i % G['shot_step'] == 1:
                        cl.append(((x, yw - 2 * sgn, zg + 1), C['shot']))
                if ok and any(occ[p] or p in cells for p, _ in cl):
                    ok, why = False, '碰到東西'
                if not ok:
                    notes.append('%s：%s ⇒ 不放' % (name, why))
                    continue
                for p, c in cl:
                    cells[p] = c
                    deck_of[p] = deck
                rows.append({'name': name, 'x': [x0, x0 + L - 1], 'z': zg, 'shots': sum(1 for _, c in cl if c == C['shot']), 'cells': len(cl)})
    out_works = []
    os.makedirs(os.path.join(D, 'masks', 'garlands'), exist_ok=True)
    for deck in G['decks']:
        ks = sorted(p for p in cells if deck_of[p] == deck)
        txt = '# 三叉戟號 shot garland（甲板-%s）draft_garlands.py —— 世界座標 x,y,z,color（子作品 at 0,0,0）\n' % deck + \
              ''.join('%d,%d,%d,%d\n' % (p + (cells[p],)) for p in ks)
        fn = 'masks/garlands/%s.vox.txt' % deck
        open(os.path.join(D, fn), 'w', encoding='utf-8', newline='\n').write(txt)
        out_works.append({'deck': '甲板-' + deck, 'work': G['works'][deck], 'title': G['titles'][deck], 'host_work': 'gura-tridente-01m-deck-' + deck,
                          'link': G['link'], 'file': fn, 'voxels': len(ks), 'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest()})
    out = {'note': 'draft_garlands.py —— 現況 ＝ 組裝件 links=all 藏 %s（%d 格）＋ 砲的實際格 %d 門 ＋ 其他模型外框 %d' % (hide, len(A), len(VG['rows']), nbox),
           'works': out_works, 'rows': rows, 'notes': notes,
           'counts': {'garlands': len(rows), 'shots': sum(r['shots'] for r in rows), 'cells': len(cells)}}
    with open(os.path.join(D, 'verify_garlands.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(out['counts'], {w['deck']: w['voxels'] for w in out_works})
    for m in notes:
        print('⚠', m)


if __name__ == '__main__':
    main()
