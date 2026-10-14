# 三叉戟號 rammer／sponge（TASK-0576）：每門舷側砲正上方的橫樑底下一對，平行砲身（沿 y）、外端離船殼內面 clear_wall 格
#   改自餘燼號 draft_gunfittings.py 的 rammer／sponge 段（basecamp；它照憲法號階段二十二）：長 28（放不下 22）、桿 136、頭 2×2（rammer 104、sponge 218）、
#   離外端 6、22 格兩道鐵箍 36；z ＝ 頭上天花板（那一段 y 全部同高）底下一格；候選照「長的 ＞ 低的（掛在橫樑底下，⛔ 不要卡在兩根樑之間、艙裡看不到）＞ 靠砲中線」挑。
#   只做有天花板的三層（lower、middle、upper）；上甲板（spar）是露天的、頭上沒東西掛；船尾兩門追擊砲的砲軸是 x ⇒ 不做（照實記）。
#   每層一件子作品（at 0,0,0 的整船框 ⇒ 清單就是世界座標），關聯在那一層甲板子作品裡（藏甲板一起藏）。
#   現況 ＝ 組裝件 links=all（藏本階段的關聯）＋ 模型外框（砲、桶…）；牆從船殼量。
#   輸出：masks/implements/<層>.vox.txt、verify_implements.json。用法：python -I -X utf8 draft_implements.py <design>
import sys, os, json, math, hashlib, tempfile, subprocess
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hull_lines as HL
import layout as LY
import deco_base as DB

NX, NY, NZ = 1100, 400, 260


def parts():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=parts', '--arg', 'work=' + DB.ASM, '--arg', 'out=' + out],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0:
            raise SystemExit(r.stdout[-800:])
        return json.load(open(out, encoding='utf-8'))['models']


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    D = os.path.abspath(sys.argv[1])
    plan = HL.load_plan(D)
    I = plan['implements']
    C = I['colors']
    YC = plan['space']['yc']
    hide = ','.join('甲板-%s/%s' % (d, I['link']) for d in I['decks'])
    try:
        A = DB.export_list(DB.ASM, 'all', ('hide_links=' + hide,))
    except SystemExit:
        A = DB.export_list(DB.ASM, 'all')
    A = A[A[:, 2] < NZ]
    occ = np.zeros((NX, NY, NZ), bool)
    occ[A[:, 0], A[:, 1], A[:, 2]] = True
    H = DB.export_list(DB.ASM, '船殼')
    H = H[H[:, 2] < NZ]
    hull = np.zeros((NX, NY, NZ), bool)
    hull[H[:, 0], H[:, 1], H[:, 2]] = True
    vox = occ.copy()                                                     # 天花板只看格子（🩸 v1 連砲的外框一起看：36 磅砲外框頂到 z 107，正好在橫樑底下那一段 ⇒ 同一根桿下面有的 y 碰到外框、有的碰到樑 ⇒ 下砲甲板一根都放不上）
    nbox = 0
    VG = json.load(open(os.path.join(D, 'verify_guns.json'), encoding='utf-8'))
    OFFS = np.array([[0.5, 0.5, 0.5]] + [[0.15 + 0.7 * (k & 1), 0.15 + 0.7 * ((k >> 1) & 1), 0.15 + 0.7 * ((k >> 2) & 1)] for k in range(8)])
    tc = {}
    for r in VG['rows']:                                                 # 砲：實際的格（格心＋八角），⛔ 不用外框
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
    for m in parts():
        if (m.get('meta') or {}).get('kind') == 'gun':
            continue
        b = m['box']
        occ[max(0, int(math.floor(b[0]))):int(math.ceil(b[3])), max(0, int(math.floor(b[1]))):int(math.ceil(b[4])),
            max(0, int(math.floor(b[2]))):min(NZ, int(math.ceil(b[5])))] = True
        nbox += 1

    def wall(x, z, sgn):
        """船殼內面：從中線往那一舷第一格船殼。"""
        ys = range(YC + 15, NY) if sgn > 0 else range(YC - 15, -1, -1)
        for y in ys:
            if hull[x, y, z]:
                return y
        return None

    cells, kinds, rows, notes = {}, {}, [], []
    for deck in I['decks']:
        guns = sorted([r for r in VG['rows'] if r['host_link'] == '甲板-' + deck and 'port_x' in r], key=lambda r: (r['meta']['side'], r['meta']['port']))
        for r in guns:
            sgn = 1 if r['meta']['side'] == 'S' else -1
            c = int(round((r['port_x'][0] + r['port_x'][1] + 1) / 2.0))
            dz = int(round(r['deck_z']))
            used = []
            got = {}
            for kind, head in (('rammer', C['rammer_head']), ('sponge', C['sponge_head'])):
                cands = []
                for L in I['lengths']:
                    for dx in I['dx_try']:
                        x = c + dx
                        if any(abs(x - u) < 2 for u in used):
                            continue
                        zt = dz + I['ceiling_from']
                        yw = wall(x, zt, sgn)
                        if yw is None:
                            continue
                        y1 = yw - sgn * I['clear_wall']                      # 外端（頭）那一格
                        ys = [y1 - sgn * k for k in range(L)]                 # 從頭往船裡
                        zc = set()
                        for y in ys:
                            col = np.nonzero(vox[x, y, zt:dz + I['ceiling_max']])[0]
                            zc.add(zt + int(col.min()) if len(col) else None)
                        if len(zc) != 1 or None in zc:
                            continue
                        z = zc.pop() - 1
                        cl = []
                        for k, y in enumerate(ys):
                            col_ = head if k <= 1 else (C['iron'] if k in I['bands'] else C['staff'])
                            cl.append(((x, y, z), col_))
                        cl += [((x, ys[0], z - 1), head), ((x, ys[1], z - 1), head)]
                        if any(occ[p] or p in cells for p, _ in cl):
                            continue
                        cands.append((-L, z, abs(dx), dx, x, ys, z, cl))
                if not cands:
                    notes.append('%s/%s 上方放不下 %s ⇒ 不放' % (deck, r['model'], kind))
                    continue
                _, _, _, dx, x, ys, z, cl = min(cands, key=lambda t: t[:4])
                for p, col_ in cl:
                    cells[p] = col_
                    kinds[p] = deck
                got[kind] = {'x': x, 'y': [min(ys), max(ys)], 'z': z, 'len': len(ys), 'dx': dx}
                used.append(x)
            rows.append({'gun': '甲板-%s/%s' % (deck, r['model']), **got})
    skipped = [r['host_link'] + '/' + r['model'] for r in VG['rows'] if r['host_link'] in ('甲板-' + d for d in I['decks']) and 'port_x' not in r]
    out_works = []
    os.makedirs(os.path.join(D, 'masks', 'implements'), exist_ok=True)
    for deck in I['decks']:
        ks = sorted(p for p in cells if kinds[p] == deck)
        txt = '# 三叉戟號 rammer／sponge（甲板-%s）draft_implements.py —— 世界座標 x,y,z,color（子作品 at 0,0,0）\n' % deck + \
              ''.join('%d,%d,%d,%d\n' % (p + (cells[p],)) for p in ks)
        fn = 'masks/implements/%s.vox.txt' % deck
        open(os.path.join(D, fn), 'w', encoding='utf-8', newline='\n').write(txt)
        out_works.append({'deck': '甲板-' + deck, 'work': I['works'][deck], 'title': I['titles'][deck], 'host_work': 'gura-tridente-01m-deck-' + deck,
                          'link': I['link'], 'file': fn, 'voxels': len(ks), 'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest()})
    assert sum(w['voxels'] for w in out_works) == len(cells), '格沒分乾淨'
    cnt = {k: sum(1 for r in rows if k in r) for k in ('rammer', 'sponge')}
    out = {'note': 'draft_implements.py —— 現況 ＝ 組裝件 links=all 藏 %s（%d 格）＋ 砲的實際格 %d 門 ＋ 其他模型外框 %d' % (hide, len(A), len(VG['rows']), nbox),
           'works': out_works, 'rows': rows, 'notes': notes, 'skipped_guns': skipped,
           'counts': {'cells': len(cells), 'rammer': cnt['rammer'], 'sponge': cnt['sponge'], 'guns': len(rows)}}
    with open(os.path.join(D, 'verify_implements.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(out['counts'], {w['deck']: w['voxels'] for w in out_works}, '跳過', skipped)
    for m in notes:
        print('⚠', m)


if __name__ == '__main__':
    main()
