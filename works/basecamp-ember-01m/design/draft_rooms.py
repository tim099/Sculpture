# 餘燼號 階段八a：房間、艙壁與兩座梯子（plan.json rooms_build）
#   憲法號 orlop／berth／gun deck 的艙壁、舷側艙房、梯子照換算搬到餘燼號 orlop／berth／下層砲甲板：
#     房間與艙壁 ⇒ 逐格平移（x < 439 不動、x ≥ 472 推 +66；量過沒有一格落在拉長那一段）
#     梯子 ⇒ 一座一座整座搬（26 連通一塊 ＝ 一座；整座在 x < 472 不動、整座在 x ≥ 472 推 +66、跨界擋下）
#     reuse=true 的舷側艙房 ⇒ 換算後跟憲法號逐格相同 ⇒ 直接關聯憲法號那件（這裡只驗、不出清單）
#   ⇒ masks/rooms/<名>.vox.txt（bulkheads／ladders：世界座標、at 0,0,0；side：子作品本地座標）、rooms_placement.json、verify_rooms.json、sheet07_rooms_v1.png
# 用法：python -I draft_rooms.py <design 資料夾>
#   量：跟組裝件現況（links=all）重疊、露到船外、鏡像差、接不接得到船殼、組裝件預期格數與結構（元件、空腔）
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_profile as DP   # noqa: E402

CON = 'basecamp-frigate-constitution-01m'
YC = 160


def cells_of(work, links='none'):
    a = DP.export_list(work, links)
    return {(int(x), int(y), int(z)): int(c) for x, y, z, c in a}


class Rooms:
    def __init__(s, design):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        s.B = s.plan['rooms_build']
        s.St = s.plan['stretch']
        s.A = cells_of(s.B['assembly'], 'all')
        assert len(s.A) == s.B['assembly_before'], ('組裝件現況跟 plan 記的不一樣', len(s.A))
        s.read = {'assembly_before': len(s.A)}
        s.out = {}          # 名 ⇒ {'cells': 世界座標 dict, 'work', 'title', 'deck_work', 'link', 'at', 'at_mirror', 'kind'}
        s.ladder_log = {}

    def shift(s, x):
        x0, L, n = s.St['x_from'], s.St['length'], s.St['copies']
        assert not (x0 <= x < x0 + L), ('房間格落在拉長那一段', x)
        return x if x < x0 else x + L * n

    def build(s):
        for deck, D in s.B['decks'].items():
            # 艙壁：世界座標
            b = D['bulkheads']
            src = cells_of(CON + '-' + b['from'])
            s.read['con_' + b['from']] = len(src)
            s.out[deck + '-bulkheads'] = {'cells': {(s.shift(x), y, z): c for (x, y, z), c in src.items()}, 'work': b['work'], 'title': b['title'],
                                          'deck_work': D['deck_work'], 'link': b['link'], 'kind': 'world'}
            # 舷側艙房：本地座標 ＋ at（S 舷）＋ mirror（P 舷）
            sd = D['side']
            loc = cells_of(CON + '-' + sd['from'])
            s.read['con_' + sd['from']] = len(loc)
            ax, ay, az = sd['at']
            world = {(s.shift(x + ax), y + ay, z + az): c for (x, y, z), c in loc.items()}
            moved = {(x - ax, y - ay, z - az): c for (x, y, z), c in world.items()}
            same = moved == loc
            if sd.get('reuse'):
                assert same, ('reuse 的舷側艙房換算後不同', sd['from'])
            s.out[deck + '-side'] = {'cells': world, 'local': moved, 'work': sd.get('work', CON + '-' + sd['from']), 'title': sd.get('title', ''),
                                     'deck_work': D['deck_work'], 'link': sd['link'], 'at': sd['at'], 'at_mirror': sd['at_mirror'],
                                     'reuse': bool(sd.get('reuse')), 'same_as_con': same,
                                     'size': [max(k[0] for k in moved) + 1, max(k[1] for k in moved) + 1, max(k[2] for k in moved) + 1], 'kind': 'side'}
            # 梯子：整座搬
            if 'ladders' in D:
                L = D['ladders']
                src = cells_of(CON + '-' + L['from'])
                s.read['con_' + L['from']] = len(src)
                s.out[deck + '-ladders'] = {'cells': s.move_whole(src, deck), 'work': L['work'], 'title': L['title'],
                                            'deck_work': D['deck_work'], 'link': L['link'], 'kind': 'world'}

    def move_whole(s, src, deck):
        arr = np.array(sorted(src))
        lo = arr.min(0)
        A = np.zeros(tuple(arr.max(0) - lo + 1), bool)
        A[tuple((arr - lo).T)] = True
        lab, n = ndimage.label(A, structure=np.ones((3, 3, 3), bool))
        x0, L, k = s.St['x_from'], s.St['length'], s.St['copies']
        out, log = {}, []
        for i in range(1, n + 1):
            pts = [tuple(int(v) for v in p) for p in (np.argwhere(lab == i) + lo)]
            xs = [p[0] for p in pts]
            if max(xs) < x0 + L:
                dx = 0
            elif min(xs) >= x0 + L:
                dx = L * k
            else:
                raise SystemExit('梯子跨過拉長的邊界（x %d..%d）—— 要人決定' % (min(xs), max(xs)))
            for p in pts:
                out[(p[0] + dx, p[1], p[2])] = src[p]
            log.append({'x': [min(xs), max(xs)], 'cells': len(pts), 'dx': dx})
        s.ladder_log[deck] = sorted(log, key=lambda d: d['x'][0])
        return out

    def placed(s):
        # 組裝件裡實際會出現的格：world 件照放；side 件放 S 舷＋鏡到 P 舷（mirror=y：同一件在自己的框裡翻 y，at.y 換成 at_mirror）
        P = {}
        for nm, O in s.out.items():
            if O['kind'] == 'world':
                P[nm] = dict(O['cells'])
            else:
                H = O['size'][1]
                ax, ay, az = O['at']
                mx, my, mz = O['at_mirror']
                cells = {}
                for (x, y, z), c in O['local'].items():
                    cells[(x + ax, y + ay, z + az)] = c
                    cells[(x + mx, (H - 1 - y) + my, z + mz)] = c
                P[nm] = cells
        return P

    def verify(s):
        P = s.placed()
        v = {'cells_placed': {k: len(c) for k, c in P.items()}}
        names = list(P)
        ov = {}
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                n = sum(1 for k in P[names[i]] if k in P[names[j]])
                if n:
                    ov[names[i] + '×' + names[j]] = n
        v['overlap_between_new'] = ov
        v['overlap_assembly'] = {k: sum(1 for kk in D if kk in s.A) for k, D in P.items()}
        # 露到船外：比那一欄、那一舷的組裝件外緣還外面 —— 外緣取上下 ±12 層裡最寬的那一層
        # ⚠ 不能只看同一層：砲門那幾層（約 8 層高）牆是開通的，那一列只剩中線附近的柱子（|dy| 0、9），
        #   第一版照同一層量 ⇒ 艦長室 48 格、梯子 16 格被判成「露到船外」，其實離真的船牆還有 30 格。
        row = {}
        for (x, y, z) in s.A:
            k = (x, z, 1 if y > YC else -1)
            row[k] = max(row.get(k, -1), abs(y - YC))

        def outer(x, z, sg):
            return max((row.get((x, zz, sg), -1) for zz in range(z - 12, z + 13)), default=-1)
        v['outside_hull'] = {k: sum(1 for (x, y, z) in D if abs(y - YC) > outer(x, z, 1 if y > YC else -1)) for k, D in P.items()}
        v['mirror_mismatch'] = {k: sum(1 for (x, y, z), c in D.items() if D.get((x, 320 - y, z)) != c) for k, D in P.items()}
        R = dict(s.A)
        for D in P.values():
            R.update(D)
        v['assembly_expect'] = len(R)
        v['added'] = len(R) - len(s.A)
        v['structure_expect'] = DP.Ember.structure(None, R)
        arr = np.array(sorted(R))
        lo = arr.min(0)
        G = np.zeros(tuple(arr.max(0) - lo + 1), bool)
        G[tuple((arr - lo).T)] = True
        lab, n = ndimage.label(G)
        hull = lab[tuple(np.array(next(iter(s.A))) - lo)]
        v['not_connected'] = {k: sum(1 for kk in D if lab[tuple(np.array(kk) - lo)] != hull) for k, D in P.items()}
        v['side_same_as_con'] = {k: O['same_as_con'] for k, O in s.out.items() if O['kind'] == 'side'}
        v['ladders'] = s.ladder_log
        s.P = P
        return v

    def write(s):
        out = os.path.join(s.design, 'masks', 'rooms')
        os.makedirs(out, exist_ok=True)
        files, place = {}, {}
        for nm, O in s.out.items():
            entry = {'work': O['work'], 'title': O['title'], 'deck_work': O['deck_work'], 'link': O['link'], 'kind': O['kind']}
            if O['kind'] == 'side':
                entry.update({'at': O['at'], 'at_mirror': O['at_mirror'], 'reuse': O['reuse'], 'size': O['size']})
            place[nm] = entry
            if O.get('reuse'):
                continue
            D = O['local'] if O['kind'] == 'side' else O['cells']
            p = os.path.join(out, nm + '.vox.txt')
            rows = sorted((k[0], k[1], k[2], c) for k, c in D.items())
            what = '子作品本地座標' if O['kind'] == 'side' else '世界座標，子作品 at 0,0,0'
            open(p, 'w', encoding='utf-8', newline='\n').write('# %s（%s）（%d 格）\n' % (nm, what, len(rows)) + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
            files[nm] = {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}
            place[nm]['file'] = 'masks/rooms/' + nm + '.vox.txt'
            place[nm]['cells'] = len(rows)
        json.dump(place, open(os.path.join(s.design, 'rooms_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        return files

    def sheet(s, path):
        # 三層各一張：從上往下看那一層的 z 範圍（灰 ＝ 組裝件現況、彩 ＝ 這一階段加的）
        layers = [('orlop', 42, 61), ('berth', 60, 84), ('lower', 82, 104)]
        sc, x0, x1, y0, y1 = 1, 90, 780, 95, 226
        Wd, Hd = (x1 - x0) * sc, (y1 - y0) * sc
        im = Image.new('RGB', (Wd + 40, (Hd + 40) * 3 + 60), (250, 249, 244))
        d = ImageDraw.Draw(im)
        d.text((20, 10), '餘燼號 新圖紙 07 v1：房間、艙壁、梯子（從上往下看各層；灰 ＝ 現況、彩 ＝ 新加）', font=DP.font(16), fill=(30, 30, 30))
        px = im.load()
        for i, (nm, za, zb) in enumerate(layers):
            ox, oy = 20, 45 + i * (Hd + 40)
            d.text((ox, oy), nm, font=DP.font(14), fill=(60, 60, 60))
            for (x, y, z) in s.A:
                if za <= z <= zb and x0 <= x < x1 and y0 <= y < y1:
                    px[ox + (x - x0) * sc, oy + 20 + (y1 - 1 - y) * sc] = (205, 205, 205)
            top = {}
            for k, D in s.P.items():
                if not k.startswith(nm):
                    continue
                for (x, y, z), c in D.items():
                    if (x, y) not in top or z > top[(x, y)][0]:
                        top[(x, y)] = (z, c)
            for (x, y), (z, c) in top.items():
                if x0 <= x < x1 and y0 <= y < y1:
                    px[ox + (x - x0) * sc, oy + 20 + (y1 - 1 - y) * sc] = DP.rgb(c)
        im = im.resize((im.width * 2, im.height * 2), Image.NEAREST)
        im.save(path)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = os.path.abspath(sys.argv[1])
    R = Rooms(design)
    R.build()
    v = {'read': R.read}
    v.update(R.verify())
    v['files'] = R.write()
    R.sheet(os.path.join(design, 'sheet07_rooms_v1.png'))
    json.dump(v, open(os.path.join(design, 'verify_rooms.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({k: v[k] for k in v if k != 'files'}, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
