# 階段二十 往下通貨艙的梯子＋彈藥庫門口踏板（TASK-0685；Tim 2026-10-17「接著參考憲法號 完成風暴角號的貨倉梯&其他細節吧」）
#   量的（exports/stage20_pre，引擎匯出 550,884 格；walkback.py 整艘量）：下層砲甲板三個艙口往下沒有梯子 ⇒ 掉進貨艙（5.5–6 m）就爬不出來 ——
#     後艙口 x 205–215、y 125–135（甲板站 z 63；上面壓著 下↔上 的 aft 梯子）／主艙口 x 306–322、y 121–139（站 60）／前艙口 x 445–457、y 124–136（站 67）；
#     艙口圍板高 2 格（同憲法號 coaming 2）。貨艙底是一根根肋骨撐的波浪面：中線谷底站 z 4–7、肋骨頂 z 8–9。
#     walkback（起點：head ≥ z 100 的四座梯子）：走得到 122,186、走得回 91,008、回不來 31,634 —— 最大一群 31,019 格就是貨艙（x 121–537、z 5–71）。
#   彈藥庫（階段十三）的門在前艙壁 x 172、y 128–132、門檻 z 28（站 29），比貨艙底高 2.2 m；門正前方 x 175–181、y 128–132 是後桅插到桅座那一段
#     ⇒ 門口鋪一條踏板（x 173–174、貼艙壁），梯子放在桅的旁邊（y 134–138 或 122–126），沿船長往前下到貨艙底。
# 幾何、檢查照 basecamp 憲法號 design/draft_orlop_ladders.py（Orlop.shape／try_one：撞到、頭頂、梯腳底下、梯腳外、扶手柱與扶手繩）—— import，sha256 記進 verify；
#   顏色照本艘階段十三的梯子（plan.json ladders.colors）、扶手繩照 plan.json ladders.manrope。坡度先試 rise 3／run 2，放不下 ⇒ 陡梯 run 1（同憲法號往下通貨艙那一件）。
#   貨艙底不平 ⇒ 梯腳高度 zl 從 5 往上試到 11（兩條側板的腳下要實心、梯腳外 3 格要空）。
# 給遊戲的 foot／lo／hi／head：lo／hi ＝ 最低／最高那一階踏板上第一格（中間那一排）；foot ＝ 梯腳往外第一個站得住的格（腳下實心、上 7 格空，同遊戲 standZ）；
#   head ＝ 艙口那一頭往外第一段連續 3 欄一樣高、頭上 3 格空的平地（階段十三的規則）；彈藥庫梯的 head ＝ 門檻那一格。
# 用法：python -I -X utf8 -B draft_hold_ladders.py <design> <組裝件 export list（梯子加進來之前）>
#   ⇒ masks/ladders/hold.vox.txt（子作品，世界座標 ＝ 子作品座標）、verify_hold_ladders.json
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage

D = os.path.abspath(sys.argv[1]); LIST = os.path.abspath(sys.argv[2])
WORKS = os.path.dirname(os.path.dirname(D))
CON = os.path.join(WORKS, 'basecamp-frigate-constitution-01m', 'design')
sys.path.insert(0, CON)
import draft_orlop_ladders as O                                           # noqa: E402

plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
PL = plan['ladders']
O.C = dict(PL['colors'])
O.MANROPE = dict(PL['manrope'])
O.G['landing'] = 3                                                     # 同憲法號往下通貨艙那一件：梯腳外連續 3 格
PLANK = plan['decks']['colors']['plank']
SUB = 'summit-stormkaap-01m-ladders-hold'
TITLE = '風暴角號｜往下通貨艙的梯子＋彈藥庫門口踏板（階段二十）'
LINK_IN = 'summit-stormkaap-01m-deck-lower'
LINK = '梯子-貨艙'
PATH = '甲板-下/' + LINK
RUNS = [2, 1]
ZL = list(range(5, 12))
Y_HATCH = [[128, 132], [127, 133], [126, 130], [130, 134], [125, 129], [131, 135]]
Y_MAG = [([134, 138], (128, 133)), ([122, 126], (127, 132))]          # （梯子兩條側板、門口踏板的 y 範圍）
LADDERS = [
    {'id': 'hold-main', 'zu': 60, 'cands': [(322, -1), (306, 1)], 'ys': Y_HATCH, 'note': '主艙口（下層砲甲板 x 306–322、y 121–139；主桅 295.5 在後面）'},
    {'id': 'hold-fore', 'zu': 67, 'cands': [(445, 1), (457, -1)], 'ys': Y_HATCH, 'note': '前艙口（x 445–457、y 124–136；上面是 下↔上 的 fore 梯子）'},
    {'id': 'hold-aft', 'zu': 63, 'cands': [(215, -1), (205, 1)], 'ys': Y_HATCH, 'note': '後艙口（x 205–215、y 125–135；上面壓著 下↔上 的 aft 梯子）'},
    {'id': 'hold-mag', 'zu': 27, 'cap': [0], 'cands': [(173, 1)], 'ys': None, 'note': '彈藥庫門（前艙壁 x 172、y 128–132、門檻 z 28）—— 門口踏板 x 173–174；梯子在後桅（x 175–181、y 128–132）旁邊'},
]
HEADR, FLAT, STAND = 3, 3, 7


class Hold(O.Orlop):
    def __init__(s):
        s.asm_sha = hashlib.sha256(open(LIST, 'rb').read()).hexdigest()
        s.W = np.zeros((1024, 320, O.ZMAX), np.uint8)
        s.n_asm = 0
        for (x, y, z), c in O.read(LIST).items():
            s.n_asm += 1
            if z < O.ZMAX:
                s.W[x, y, z] = c
        s.carve, s.cells, s.kind, s.anchors, s.ropes, s.rows = {}, {}, {}, [], [], []

    def build(s):
        for L in LADDERS:
            got, why, pick, plank = None, [], None, {}
            O.G['cap_up'] = L.get('cap', [0, 1, 2, 3])
            ys = L['ys'] or [m[0] for m in Y_MAG]
            for run in RUNS:
                O.G['run'] = run
                for xe, d in L['cands']:
                    for y in ys:
                        plank = {}
                        if L['ys'] is None:                            # 彈藥庫門口踏板：先鋪上，梯子頂跟它相接
                            py = dict((tuple(m[0]), m[1]) for m in Y_MAG)[tuple(y)]
                            plank = {(x, yy, z): PLANK for x in (173, 174) for yy in range(py[0], py[1] + 1) for z in (27, 28)}
                            if any(s.W[k] for k in plank):
                                why.append('踏板撞到'); continue
                            for k in plank: s.cells[k] = PLANK
                            # 梯腳那一片艙底板（ceiling）：貨艙底是肋骨的波浪面（肋骨 3 格寬頂 z 8–9、谷 4 格寬底 z 5–6）⇒ 兩條側板踩不到同一高度、梯腳外也沒有 3 格平地
                            #   ⇒ 在肋骨頂上鋪一片板（頂面 z 10；x 176–194、梯寬兩邊各多 1 格；只鋪空氣格）。try_one 的「梯腳底下」看 W ⇒ 搜的時候先放進 W，定了再搬到 cells
                            board = {(x, yy, 10): PLANK for x in range(176, 195) for yy in range(y[0] - 1, y[1] + 2) if not s.W[x, yy, 10]}
                            for k in board: s.W[k] = PLANK
                        else:
                            board = {}
                        for zl in ZL:
                            C = {'xe': xe, 'd': d, 'y': y, 'zu': L['zu'], 'zl': zl}
                            for band in O.G['band']:
                                for cap_up in O.G['cap_up']:
                                    got, w = s.try_one(C, band, cap_up)
                                    if got: break
                                    why.append('run %d xe %d d %+d y %s zl %d band %d cap %d：%s' % (run, xe, d, y, zl, band, cap_up, w))
                                if got: break
                            if got:
                                pick = dict(C, run=run); break
                        for k in board: s.W[k] = 0
                        if got:
                            for k in board: s.cells[k] = PLANK; s.kind[k] = 'ceiling'
                            break
                        for k in plank: s.cells.pop(k, None)
                    if got: break
                if got: break
            O.G['run'] = RUNS[0]
            if not got:
                s.rows.append({'id': L['id'], 'placed': False, 'tried': len(why), 'why_head': why[:8], 'why_tail': why[-8:]})
                print('✗', L['id'], len(why), why[-3:])
                continue
            for k, (c, kd) in got['cells'].items():
                s.cells[k] = c; s.kind[k] = kd
            for k in plank:
                s.kind[k] = 'landing'
            for side in ('P', 'S'):
                for which in ('top', 'bot'):
                    s.anchors.append({'name': 'manrope-%s-%s-%s' % (L['id'], side, which), 'at': list(got['tops'][(side, which)]), 'note': '扶手柱頂（階段二十）'})
                s.ropes.append({'name': '梯-%s.manrope-%s' % (L['id'], side), 'from': '%s/manrope-%s-%s-top' % (PATH, L['id'], side),
                                'to': '%s/manrope-%s-%s-bot' % (PATH, L['id'], side), **O.MANROPE})
            s.rows.append({'id': L['id'], 'placed': True, 'run': pick['run'], 'xe': pick['xe'], 'xf': got['xf'], 'd': pick['d'], 'y': pick['y'], 'zu': L['zu'],
                           'zcap': got['zcap'], 'zl': pick['zl'], 'band': got['band'], 'cap_up': got['cap_up'], 'R': got['R'], 'treads': got['treads'],
                           'post_bot': got['post_bot'], 'post_h': got['post_h'], 'cells': len(got['cells']), 'landing': len(plank), 'ceiling': len(board), 'tried_before': len(why), 'note': L['note'],
                           'tread_cells': sorted([list(k) for k, (c, kd) in got['cells'].items() if kd == 'tread'])})
            print('✓', L['id'], json.dumps({k: s.rows[-1][k] for k in ('run', 'xe', 'xf', 'd', 'y', 'zcap', 'zl', 'R', 'cells', 'landing', 'ceiling', 'tried_before')}))

    def stand(s, x, y, z):
        return s.full[x, y, z - 1] and not s.full[x, y, z:z + STAND].any()

    def points(s):
        s.full = s.W > 0
        for k in s.cells:
            s.full[k] = True
        P = {}
        for r in s.rows:
            if not r['placed']:
                continue
            yc = (r['y'][0] + r['y'][1]) // 2
            byz = {}
            for x, y, z in r['tread_cells']:
                if y == yc: byz.setdefault(z, []).append(x)
            zs = sorted(byz)
            lo = (min(byz[zs[0]]) if r['d'] < 0 else max(byz[zs[0]]), yc, zs[0] + 1)
            hi = (max(byz[zs[-1]]) if r['d'] < 0 else min(byz[zs[-1]]), yc, zs[-1] + 1)
            foot = None
            for i in range(1, 12):                                     # 梯腳往外（往下梯的方向）第一個站得住的格；高度在 lo 下面 0–8 格裡、離 lo 最近
                x = lo[0] + r['d'] * i
                zz = [z for z in range(lo[2] - 8, lo[2] + 1) if s.stand(x, yc, z)]
                if zz:
                    foot = (x, yc, max(zz)); break
            if r['id'] == 'hold-mag':
                head = (172, 130, 29)
                assert s.stand(*head), '門檻站不住'
            else:
                head = None                                            # 艙口那一頭往外：連續 3 欄一樣高、站得住（頭上 7 格空，同遊戲 standZ）
                for i in range(1, 25):                                 #   🩸 第一版只要頭上 3 格空 ⇒ hold-aft 挑到 (217,130,62)：頭頂就是 下↔上 aft 梯子的踏板（遊戲站不住）
                    for yy in (yc, yc - 3, yc + 3, yc - 6, yc + 6):     #   中線那一排被別的梯子壓著 ⇒ 往兩舷挪
                        cols = []
                        for j in range(FLAT):
                            x = hi[0] - r['d'] * (i + j)
                            zz = [z for z in range(r['zu'] - 3, r['zu'] + 4) if s.stand(x, yy, z)]
                            cols.append((x, zz[0] if zz else None))
                        if cols[0][1] is not None and all(c[1] == cols[0][1] for c in cols):
                            head = (cols[0][0], yy, cols[0][1]); break
                    if head: break
            P[r['id']] = {'foot': list(foot) if foot else None, 'lo': list(lo), 'hi': list(hi), 'head': list(head) if head else None, 'steps': len(zs)}
        s.P = P

    def verify(s):
        v = {'assembly_list_sha256': s.asm_sha, 'assembly_cells_before': s.n_asm, 'cells': len(s.cells), 'by_kind': {},
             'constitution_module_sha256': hashlib.sha256(open(O.__file__, 'rb').read()).hexdigest()}
        for kd in s.kind.values():
            v['by_kind'][kd] = v['by_kind'].get(kd, 0) + 1
        v['overlap_world'] = sum(1 for k in s.cells if s.W[k] > 0)
        A = s.W > 0
        for k in s.cells: A[k] = True
        lab, n = ndimage.label(A)
        base = set(np.unique(lab[s.W > 0])) - {0}
        v['floating'] = sum(1 for k in s.cells if lab[k] not in base)        # 空腔不在這裡量（W 只到 z < ZMAX）⇒ 看引擎 stats
        v['placed'] = sum(1 for r in s.rows if r['placed']); v['of'] = len(s.rows)
        v['points'] = s.P
        v['points_ok'] = {k: all(p[q] is not None and s.stand(*p[q]) for q in ('foot', 'head')) for k, p in s.P.items()}
        v['anchors'] = s.anchors; v['ropes'] = s.ropes; v['rows'] = s.rows
        v['expect_assembly_after'] = s.n_asm + len(s.cells)
        v['work'], v['title'], v['link_in'], v['link'], v['path'] = SUB, TITLE, LINK_IN, LINK, PATH
        s.v = v

    def write(s):
        out = os.path.join(D, 'masks', 'ladders'); os.makedirs(out, exist_ok=True)
        NL = chr(10)
        rws = sorted(k + (c,) for k, c in s.cells.items())
        txt = '# %s（子作品 %s；世界座標 ＝ 子作品座標，stampvox at=0,0,0；關聯 %s）—— draft_hold_ladders.py 產（%d 格）' % (TITLE, SUB, PATH, len(rws)) + NL + ''.join('%d,%d,%d,%d' % r + NL for r in rws)
        open(os.path.join(out, 'hold.vox.txt'), 'w', encoding='utf-8', newline=NL).write(txt)
        s.v['file'] = {'path': 'masks/ladders/hold.vox.txt', 'cells': len(rws), 'sha256': hashlib.sha256(txt.encode('utf-8')).hexdigest()}
        with open(os.path.join(D, 'verify_hold_ladders.json'), 'w', encoding='utf-8', newline='\n') as f:
            json.dump(s.v, f, ensure_ascii=False, indent=1, sort_keys=True); f.write('\n')


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    F = Hold()
    F.build(); F.points(); F.verify(); F.write()
    print(json.dumps({k: F.v[k] for k in ('cells', 'by_kind', 'overlap_world', 'floating', 'placed', 'of', 'points_ok', 'expect_assembly_after', 'file')}, ensure_ascii=False))
    for k, p in F.P.items():
        print(k, p)


if __name__ == '__main__':
    main()
