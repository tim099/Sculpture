# 餘燼號 階段六：桅杆（plan.json masts_build）
#   憲法號四件桅杆子作品（links=none 的格＋models.json 的帆桁模型＋anchors.json 的固定點）照船殼同一套換算搬過來：
#     三根桅：x 照拉長（前桅 +66）；z < cut 不動、z ≥ cut 抬 +23、[cut, cut+23) 每層 ＝ 憲法號 z cut−1 那一層的複製（下桅加長 23）
#     艏斜桅：整根平移 (+66, 0, +23)（對準船殼跟著抬高的艏斜桅開口）
#     帆桁模型：來源照舊是憲法號的 -yard-* 子作品；at 照同一套換算（全部在切口以上 ⇒ z +23）；spanker boom 另外照 plan 改（縮短＋抬高）
#   ⇒ masks/masts/<桅>.vox.txt（世界座標，子作品 at 0,0,0）、masts_placement.json（模型與固定點）、verify_masts.json
# 用法：python -I draft_masts.py <design 資料夾>
import sys, os, json, hashlib, copy
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_profile as DP   # noqa: E402
from draft_decks import stretch_x   # noqa: E402

CON = 'basecamp-frigate-constitution-01m'
WORKS = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
YC = 160


class Masts:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.M = s.plan['masts_build']
        s.St = s.plan['stretch']
        s.cut, s.h = s.plan['band']['cut_z'], s.plan['band']['height']
        s.read = {}
        s.cells, s.models, s.anchors = {}, {}, {}

    def xmap(s, x):
        r = stretch_x(x, s.St)
        assert len(r) == 1, ('桅杆的格落在拉長複製那一段', x)
        return r[0]

    def pmap(s, kind, x, y, z):
        """連續或整數座標的換算（模型的 at、固定點）。"""
        if kind == 'translate':
            dx, dy, dz = s.M['bowsprit_shift']
            return [x + dx, y + dy, z + dz]
        xx = s.xmap(int(np.floor(x))) + (x - np.floor(x))
        return [xx, y, z if z < s.cut else z + s.h]

    def build(s):
        for nm, D in s.M['works'].items():
            src = DP.export_list(CON + '-' + D['source'])
            C = {(int(x), int(y), int(z)): int(c) for x, y, z, c in src}
            s.read['con_' + nm] = len(C)
            out = {}
            if D['kind'] == 'translate':
                dx, dy, dz = s.M['bowsprit_shift']
                for (x, y, z), c in C.items():
                    out[(x + dx, y + dy, z + dz)] = c
            else:
                for (x, y, z), c in C.items():
                    xx = s.xmap(x)
                    out[(xx, y, z if z < s.cut else z + s.h)] = c
                    if z == s.cut - 1:
                        for dz in range(s.h):
                            out[(xx, y, s.cut + dz)] = c
                s.read['band_layer_' + nm] = sum(1 for k in C if k[2] == s.cut - 1)
            s.cells[nm] = out
            # 模型（帆桁）
            root = os.path.join(WORKS, CON + '-' + D['source'])
            mm = json.load(open(os.path.join(root, 'models.json'), encoding='utf-8'))['models'] if os.path.exists(os.path.join(root, 'models.json')) else []
            ML = []
            for m in mm:
                m2 = {k: m[k] for k in ('name', 'work', 'pivot', 'rotate', 'scale', 'mirror', 'note')}
                m2['meta'] = m.get('meta', {})
                m2['at'] = s.pmap(D['kind'], *m['at'])
                ov = s.M.get('model_override', {}).get(m['name'])
                if ov:
                    m2['at'][2] += ov.get('dz', 0)
                    if 'scale' in ov:
                        m2['scale'] = ov['scale']
                    m2['override'] = ov
                ML.append(m2)
            s.models[nm] = ML
            A = json.load(open(os.path.join(root, 'anchors.json'), encoding='utf-8'))
            AL = A['anchors'] if isinstance(A, dict) else A
            s.anchors[nm] = [{'name': a['name'], 'at': [int(round(v)) for v in s.pmap(D['kind'], *a['at'])], 'con_at': a['at'], 'note': a.get('note', '')} for a in AL]

    def verify(s):
        deco = json.load(open(os.path.join(s.design, 'deco_placement.json'), encoding='utf-8'))
        # 現在的組裝件（船殼＋裝飾＋甲板）用引擎匯出
        a = DP.export_list('basecamp-ember-01m-assembly', links='all')
        R = {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}
        s.read['assembly_now'] = len(R)
        assert len(R) == s.M['assembly_before'], ('組裝件現況跟 plan 記的不一樣', len(R))
        v = {'cells': {k: len(c) for k, c in s.cells.items()}}
        v['overlap_assembly'] = {k: sum(1 for kk in c if kk in R) for k, c in s.cells.items()}
        v['overlap_between'] = {}
        names = list(s.cells)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                n = sum(1 for k in s.cells[names[i]] if k in s.cells[names[j]])
                if n:
                    v['overlap_between'][names[i] + '×' + names[j]] = n
        v['mirror_mismatch'] = {k: sum(1 for (x, y, z), cc in c.items() if c.get((x, 320 - y, z)) != cc) for k, c in s.cells.items()}
        v['x_max'] = max(k[0] for c in s.cells.values() for k in c)
        v['z_max'] = max(k[2] for c in s.cells.values() for k in c)
        for c in s.cells.values():
            for k, cc in c.items():
                R.setdefault(k, cc)
        v['assembly_expect'] = len(R)
        v['structure_expect'] = DP.Ember.structure(None, R)
        # spanker boom vs 中間那盞燈籠（模型外框，粗估：boom 沿 x 的尾端 vs 燈籠的 x 範圍）
        lant = [l for l in deco['lantern']['at']]
        boom = [m for m in s.models['mizzen'] if m['name'] == 'yard-spanker-boom'][0]
        sx = boom['scale'][0]
        end_x = boom['at'][0] - sx * (boom['pivot'][0] - 0)
        v['boom'] = {'at': boom['at'], 'scale': boom['scale'], 'end_x': round(end_x, 2),
                     'lantern_x_max': max(l['at'][0] for l in lant) + deco['lantern']['size'][0] * deco['lantern']['scale'] / 2,
                     'poop_deck_z': s.plan['decks_build']['poop']['z_top']}
        v['models'] = {k: len(m) for k, m in s.models.items()}
        v['anchors'] = {k: len(a) for k, a in s.anchors.items()}
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'masts')
        os.makedirs(out, exist_ok=True)
        files = {}
        for nm, c in s.cells.items():
            p = os.path.join(out, nm + '.vox.txt')
            rows = sorted((k[0], k[1], k[2], cc) for k, cc in c.items())
            open(p, 'w', encoding='utf-8', newline='\n').write('# 桅杆 %s（世界座標，子作品 at 0,0,0）（%d 格）\n' % (nm, len(rows)) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
            files[nm] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
        json.dump({'models': s.models, 'anchors': s.anchors}, open(os.path.join(s.design, 'masts_placement.json'), 'w', encoding='utf-8', newline='\n'),
                  ensure_ascii=False, indent=1)
        return files


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    M = Masts(design)
    M.build()
    v = {'read': M.read}
    v.update(M.verify())
    v['files'] = M.write()
    json.dump(v, open(os.path.join(design, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v[k] for k in v if k != 'files'}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
