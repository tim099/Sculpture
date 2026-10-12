# 餘燼號 階段七：索具（plan.json rigging）—— 憲法號的 channels／pin rails／fife rails、繩、帆照同一套換算搬過來
#   換算：
#     拉長 S(x)：x < 439 不動；439..471 原地＋複製到 +33／+66（格）—— 點（固定點、繩端座標）只取原地那一份；x ≥ 472 推 +66
#     船殼類（channels，掛在船殼外面、chain plates 往下接）：z < 109 不動、z ≥ 109 抬 23、[109,132) 複製 z 108 那一層
#     甲板類（pin rails、fife rails，站在上甲板上）：整件抬 23（同上甲板）
#     繩端座標、帆角座標：z < 109 不動、z ≥ 109 抬 23（索具的座標全在 109 以上）
#   ⇒ masks/rigging/{channels,belaying,fiferails}.vox.txt（各自子作品的座標）、rigging_placement.json（關聯、固定點、繩、帆、風）、verify_rigging.json
# 用法：python -I draft_rigging.py <design 資料夾>
import sys, os, json, re, hashlib
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_profile as DP   # noqa: E402
from draft_decks import stretch_x   # noqa: E402

CON = 'basecamp-frigate-constitution-01m'
WORKS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
YC = 160
COORD = re.compile(r'^(-?[\d.]+),(-?[\d.]+),(-?[\d.]+)$')


class Rig:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.G = s.plan['rigging']
        s.St = s.plan['stretch']
        s.cut, s.h = s.plan['band']['cut_z'], s.plan['band']['height']
        s.read = {}
        s.flags = []

    def jload(s, work, fn):
        p = os.path.join(WORKS, work, fn)
        return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else None

    def px(s, x):
        """點的 x（連續）：取原地那一份。"""
        x0, L, n = s.St['x_from'], s.St['length'], s.St['copies']
        if x < x0 + L:
            if x >= x0:
                s.flags.append(('point_in_stretch_block', x))
            return x
        return x + L * n

    def pz(s, z):
        return z if z < s.cut else z + s.h

    def point(s, x, y, z):
        return [s.px(x), y, s.pz(z)]

    # ── 配件子作品 ──
    def fittings(s):
        s.fit = {}
        for nm, F in s.G['fittings'].items():
            src = DP.export_list(CON + '-' + F['source'])
            at = F['con_at']
            cells = {}
            for x, y, z, c in src:
                wx, wy, wz = int(x) + at[0], int(y) + at[1], int(z) + at[2]
                for xx in stretch_x(wx, s.St):
                    if F['kind'] == 'deck':
                        cells[(xx, wy, wz + s.h)] = int(c)
                    else:
                        cells[(xx, wy, wz if wz < s.cut else wz + s.h)] = int(c)
                        if wz == s.cut - 1:
                            for dz in range(s.h):
                                cells[(xx, wy, s.cut + dz)] = int(c)
            s.read['con_' + nm] = int(len(src))
            if F.get('clear_upper_ports'):
                # chain plates 在 z 108 那一層避開的是下層砲門；往下複製 23 層之後會從上層砲門前面穿過 ⇒ 擋在上層開口 (x, z) 欄前面的格不放
                up = s.upper_ports()
                gone = [k for k in cells if (k[0], k[2]) in up]
                for k in gone:
                    del cells[k]
                s.read['cleared_in_front_of_upper_ports_' + nm] = len(gone)
            # 固定點（子作品座標 → 世界 → 換算）
            A = (s.jload(CON + '-' + F['source'], 'anchors.json') or {'anchors': []})['anchors']
            anchors = []
            for a in A:
                wx, wy, wz = a['at'][0] + at[0], a['at'][1] + at[1], a['at'][2] + at[2]
                nz = wz + s.h if F['kind'] == 'deck' else s.pz(wz)
                anchors.append({'name': a['name'], 'world': [s.px(wx), wy, nz], 'con_world': [wx, wy, wz]})
            s.fit[nm] = {'cells': cells, 'anchors': anchors}

    def frames(s):
        # 每件配件的新外框：照舊的 at（y／z 不變，x 照舊的起點）＋ 放得下的大小
        s.place = {}
        for nm, F in s.G['fittings'].items():
            cells = s.fit[nm]['cells']
            ks = np.array(sorted(cells))
            at = list(F['con_at'])
            if F['kind'] == 'deck':
                at[2] += s.h if at != [0, 0, 0] else 0
            if F.get('full'):
                at = [0, 0, 0]
            lo = ks.min(0)
            assert all(lo[i] >= at[i] for i in range(3)), (nm, lo, at)
            size = [int(max(ks.max(0)[i] - at[i] + 1, F['con_size'][i])) for i in range(3)]
            if F.get('full'):
                size = F['con_size']
            s.place[nm] = {'work': F['work'], 'at': at, 'size': size, 'cells': len(cells), 'link': F['link'], 'mirror_link': F.get('mirror_link'),
                           'parent_link_work': F.get('parent_link_work')}
            if F.get('mirror_link'):
                s.place[nm]['mirror_at'] = [at[0], 321 - at[1] - size[1], at[2]]
            for a in s.fit[nm]['anchors']:
                a['local'] = [a['world'][i] - at[i] for i in range(3)]

    def upper_ports(s):
        if not hasattr(s, '_up'):
            s._up = set()
            for line in open(os.path.join(s.design, 'masks', 'ports', 'upper_carve.vox.txt'), encoding='utf-8'):
                if line.startswith('#') or not line.strip():
                    continue
                x, y, z, c = map(int, line.split(','))
                for xx in stretch_x(x, s.St):            # 上層開口是拉長之前量的 ⇒ 照拉長換算（含複製的兩份）
                    s._up.add((xx, z))
        return s._up

    # ── 繩、帆 ──
    def ropes(s):
        R = s.jload(CON + '-assembly', 'ropes.json')['ropes']
        skip_g = set(s.G['skip_groups'])
        skip_link = set(s.G['skip_links'])
        out, skipped = [], {}

        def conv(e):
            # 座標端點：每個分量照原本的寫法 —— 原本帶小數 ⇒ 照樣帶小數（%.2f）；原本是整數 ⇒ 整數（引擎把整數當格心）
            # （第一版用 %g，`118.00` 變成 `141` ⇒ 被當成格心、多 0.5 格；18 條 lanyard 量到）
            m = COORD.match(e)
            if m:
                q = s.point(*map(float, m.groups()))
                return ','.join(('%.2f' % v) if '.' in t else ('%d' % round(v)) for v, t in zip(q, m.groups()))
            return e
        for r in R:
            g = r.get('group', '')
            why = None
            if any(g == k or g.startswith(k + '/') for k in skip_g):
                why = 'group ' + g.split('/')[0]
            else:
                for e in (r['from'], r['to']):
                    head = e.split(':', 1)[-1].split('/')[0] if e.startswith(('model:',)) else e.split('/')[0]
                    if head in skip_link:
                        why = 'link ' + head
            if why:
                skipped[why] = skipped.get(why, 0) + 1
                continue
            r2 = dict(r)
            r2['from'], r2['to'] = conv(r['from']), conv(r['to'])
            out.append(r2)
        # 子繩（rope:…）排在母繩之後
        names = {r['name'] for r in out}
        bad_parent = [r['name'] for r in out for e in (r['from'], r['to']) if e.startswith('rope:') and e[5:].split('/')[0] not in names]
        assert not bad_parent, ('子繩的母繩沒搬', bad_parent[:5])
        out.sort(key=lambda r: any(e.startswith('rope:') for e in (r['from'], r['to'])))
        s.rope_list = out
        s.read['ropes'] = len(out)
        s.read['ropes_skipped'] = skipped
        S = s.jload(CON + '-assembly', 'sails.json')
        sails = []
        for sl in S['sails']:
            s2 = dict(sl)
            s2['corners'] = [dict(c, at=conv(c['at'])) for c in sl['corners']]
            s2['color'] = s.G['sail_color']
            sails.append(s2)
        s.sails = sails
        s.wind = S['wind']
        s.seconds = S['seconds']
        s.read['sails'] = len(sails)
        H = s.jload(CON, 'anchors.json')['anchors']
        s.hull_anchors = [{'name': a['name'], 'at': s.point(*a['at']), 'con_at': a['at']} for a in H]

    def verify(s):
        v = {}
        # 組裝件「加配件之前」：藏起這一階段的關聯（套用之後重跑也一樣）
        import subprocess, tempfile
        hide = ','.join(F['link'] if not F.get('parent_link_work') else '甲板-spar/' + F['link'] for F in s.G['fittings'].values())
        hide += ',' + ','.join(F['mirror_link'] for F in s.G['fittings'].values() if F.get('mirror_link'))
        with tempfile.TemporaryDirectory() as d:
            out = os.path.join(d, 'a.txt').replace('\\', '/')
            r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=basecamp-ember-01m-assembly',
                                '--arg', 'out=' + out, '--arg', 'hide_links=' + hide], capture_output=True, text=True, encoding='utf-8', errors='replace')
            assert r.returncode == 0, (r.stdout + r.stderr)[-500:]
            a = np.loadtxt(out, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
        R = {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}
        assert len(R) == s.G['assembly_before'], ('組裝件現況跟 plan 記的不一樣', len(R))
        hull = {(int(x), int(y), int(z)) for x, y, z, c in DP.export_list('basecamp-ember-01m')}
        v['hull_anchor_on_solid'] = {h['name']: tuple(int(t) for t in h['at']) in hull for h in s.hull_anchors}
        allc = {}
        for nm, F in s.fit.items():
            cells = dict(F['cells'])
            if s.G['fittings'][nm].get('mirror_link'):
                cells.update({(x, 320 - y, z): c for (x, y, z), c in F['cells'].items()})
            ov = sum(1 for k in cells if k in R)
            cross = sum(1 for k in cells if k in allc)
            v[nm] = {'cells_one_side': len(F['cells']), 'cells_both': len(cells), 'overlap_assembly': ov, 'overlap_other': cross,
                     'anchors': len(F['anchors'])}
            allc.update(cells)
        # chain plates vs 上層砲門：上層開口（從船殼量）的 (x, z) 欄外面有沒有 channels 的格
        up = set()
        for line in open(os.path.join(s.design, 'masks', 'ports', 'upper_carve.vox.txt'), encoding='utf-8'):
            if line.startswith('#') or not line.strip():
                continue
            x, y, z, c = map(int, line.split(','))
            for xx in stretch_x(x, s.St):            # 上層開口是拉長之前量的 ⇒ 照拉長換算（含複製的兩份）
                up.add((xx, z))
        v['channels_cols_in_front_of_upper_ports'] = len(up & {(x, z) for (x, y, z) in s.fit['channels']['cells']})
        for k, c in allc.items():
            R.setdefault(k, c)
        v['assembly_expect'] = len(R)
        st = DP.Ember.structure(None, R)
        v['structure_expect'] = st
        # 每件配件要接到組裝件
        arr = np.array(sorted(R))
        lo = arr.min(0)
        A = np.zeros(tuple(arr.max(0) - lo + 1), bool)
        A[tuple((arr - lo).T)] = True
        lab, n = ndimage.label(A)
        hl = lab[tuple(np.array(next(iter(hull))) - lo)]
        v['not_connected'] = {nm: sum(1 for k in F['cells'] if lab[tuple(np.array(k) - lo)] != hl) for nm, F in s.fit.items()}
        v['flags'] = s.flags[:20]
        v['flags_count'] = len(s.flags)
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'rigging')
        os.makedirs(out, exist_ok=True)
        files = {}
        for nm, F in s.fit.items():
            at = s.place[nm]['at']
            p = os.path.join(out, nm + '.vox.txt')
            rows = sorted((k[0] - at[0], k[1] - at[1], k[2] - at[2], c) for k, c in F['cells'].items())
            open(p, 'w', encoding='utf-8', newline='\n').write('# %s（子作品座標；組裝件座標 ＝ 這裡 ＋ %s）（%d 格）\n' % (nm, ','.join(map(str, at)), len(rows))
                                                               + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
            files[nm] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        json.dump({'fittings': s.place, 'anchors': {nm: F['anchors'] for nm, F in s.fit.items()}, 'hull_anchors': s.hull_anchors,
                   'ropes': s.rope_list, 'sails': s.sails, 'wind': s.wind, 'seconds': s.seconds},
                  open(os.path.join(s.design, 'rigging_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        return files


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    G = Rig(design)
    G.fittings()
    G.frames()
    G.ropes()
    v = {'read': G.read}
    v.update(G.verify())
    v['placement'] = G.place
    v['files'] = G.write()
    json.dump(v, open(os.path.join(design, 'verify_rigging.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v[k] for k in v if k != 'files'}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
