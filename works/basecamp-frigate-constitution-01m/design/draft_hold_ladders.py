# 往下通貨艙（hold）的梯子（Tim 2026-10-16：「憲法號彈藥庫掉下去後上不去了」「需要梯子」「憲法號可以參考實際船加上更多梯子嗎」）
#   量的（Blockside 第一人稱，constitution.vxk）：orlop 地板 z 41（站 42）上往下通到貨艙底（站 17）的開口 —— after hatch X 274–285 與 X 307–319 兩處（落差 2.5 m）；
#   船中段沒有 orlop（只有前後兩塊平台）⇒ main hatch X 392–419 從 berth deck（站 60）直接到貨艙底（4.3 m）。三處往下都沒有梯子 ⇒ 掉下去就上不來。
#   實船：orlop 的艙口往下通 hold、彈藥庫，艙口放梯子（模型論壇的 1927 配置；權威圖紙沒找到）。
# 幾何、顏色、扶手跟 draft_orlop_ladders.py 同一套（rise 3／run 2、band 4→3、cap_up 0–3、headroom 8、landing 5、扶手柱高 9）；艙口本來就開著 ⇒ 不刻梯口。
#   每一處給幾組候選（從哪一頭往下 × 橫向的位置），照順序試，第一組放得下的就用（跟 draft_orlop_ladders.py 一樣的檢查：撞到、頭頂、梯腳底下、梯腳外、扶手）。
# 用法：python -I draft_hold_ladders.py <組裝件 export list（梯子加進來之前）>
#   ⇒ masks/ladders/hold.vox.txt（梯子子作品，世界座標）、rig_points_hold_ladders.json、hold_ladder_ropes.json、verify_hold_ladders.json
import sys, os, json, hashlib
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_orlop_ladders as O

HERE = os.path.dirname(os.path.abspath(__file__))
SUB = 'basecamp-frigate-constitution-01m-ladders-hold'
TITLE = '憲法號 往下通貨艙的梯子'
LINK = '甲板-orlop/梯子-貨艙'   # 掛在 orlop 甲板子作品底下（跟 berth → orlop 那一件 甲板-orlop/梯子 並排）


# 坡度：先試跟上面幾層一樣的 rise 3／run 2；放不下（艙口短、旁邊有艙壁）⇒ 陡梯 rise 3／run 1（實船往下通貨艙的梯子本來就陡；第一人稱照固定點爬，陡不陡都爬得了）
RUNS = [2, 1]
# 梯腳外的空地：豎井只有 1.3 m 長（after hatch X 274–286）⇒ 0.5 m 放不下；照 ladder_points.py 找梯腳點要的「連續 3 格」⇒ 0.3 m
O.G['landing'] = 3


def opts(x0, x1, ys):
    return [(xe, d, y) for xe, d in ((x0, 1), (x1, -1)) for y in ys]


# 貨艙底是 V 形船殼：中線 y 158–162 頂面 z 16（站 17），y 157、163 那一排低一格 ⇒ 梯子放中線 y 158–162（兩條側板都踩在 z 16 上）先試。
# 艙口底下是隔開的豎井：after hatch 前後是艙壁 X 271–273、287–289；X 307–319 那一處底下 X 306–308 是艙壁 ⇒ 梯頂從 309 起；main hatch 底下 X 389–391、398–400 是艙壁、420–422 中線是主桅的桅座。
Y = [[158, 162], [157, 163], [154, 160], [160, 166]]
LADDERS = [
    {'id': 'hold-aft', 'zu': 42, 'zl': 17, 'cands': [(274, 1, y) for y in Y] + [(285, -1, y) for y in Y],
     'note': 'after hatch（orlop X 274–285、y 153–167；上面 berth、gun 也開著）—— 後彈藥庫（X 200–271）前面；底下是 X 274–286 × y 153–167 的豎井'},
    {'id': 'hold-mid', 'zu': 42, 'zl': 17, 'cands': [(319, -1, y) for y in Y] + [(309, 1, y) for y in Y],
     'note': 'orlop X 307–319、y 151–169 的艙口（上面 berth 開著）；底下 X 309–320'},
    {'id': 'hold-main', 'zu': 60, 'zl': 17, 'cands': [(419, -1, y) for y in Y] + [(401, 1, y) for y in Y] + [(392, 1, y) for y in Y],
     'note': 'main hatch（berth X 392–419、y 141–179；船中段沒有 orlop）'},
]


class Hold(O.Orlop):
    def __init__(s, asm):
        s.S = {'ladders': []}
        s.asm_sha = hashlib.sha256(open(asm, 'rb').read()).hexdigest()
        s.W = np.zeros((1024, 320, O.ZMAX), np.uint8)
        s.n_asm = 0
        for (x, y, z), c in O.read(asm).items():
            s.n_asm += 1
            if z < O.ZMAX:
                s.W[x, y, z] = c
        s.carve, s.cells, s.kind, s.anchors, s.ropes, s.rows = {}, {}, {}, [], [], []

    def build(s):
        for L in LADDERS:
            got, why, pick = None, [], None
            for run, (xe, d, y) in [(r, c) for r in RUNS for c in L['cands']]:
                O.G['run'] = run
                C = {'xe': xe, 'd': d, 'y': y, 'zu': L['zu'], 'zl': L['zl']}
                for band in O.G['band']:
                    for cap_up in O.G['cap_up']:
                        got, w = s.try_one(C, band, cap_up)
                        if got:
                            break
                        why.append('run %d xe %d d %+d y %s band %d cap %d：%s' % (run, xe, d, y, band, cap_up, w))
                    if got:
                        break
                if got:
                    pick = dict(C, run=run)
                    break
            O.G['run'] = RUNS[0]
            if not got:
                s.rows.append({'id': L['id'], 'placed': False, 'why': why, 'tried': len(why)})
                continue
            for k, (c, kd) in got['cells'].items():
                s.cells[k] = c
                s.kind[k] = kd
            for side in ('P', 'S'):
                for which in ('top', 'bot'):
                    s.anchors.append({'name': 'manrope-%s-%s-%s' % (L['id'], side, which), 'world': list(got['tops'][(side, which)])})
                s.ropes.append({'name': '梯-%s.manrope-%s' % (L['id'], side),
                                'from': '%s/manrope-%s-%s-top' % (LINK, L['id'], side), 'to': '%s/manrope-%s-%s-bot' % (LINK, L['id'], side), **O.MANROPE})
            s.rows.append({'id': L['id'], 'placed': True, 'run': pick['run'], 'xe': pick['xe'], 'xf': got['xf'], 'd': pick['d'], 'y': pick['y'], 'zcap': got['zcap'], 'zl': L['zl'],
                           'band': got['band'], 'cap_up': got['cap_up'], 'R': got['R'], 'treads': got['treads'], 'post_bot': got['post_bot'],
                           'post_h': got['post_h'], 'cells': len(got['cells']), 'tried_before': len(why), 'note': L['note']})

    def write(s):
        D = HERE
        out = os.path.join(D, 'masks', 'ladders')
        os.makedirs(out, exist_ok=True)
        p = os.path.join(out, 'hold.vox.txt')
        body = ''.join('%d,%d,%d,%d\n' % (k + (c,)) for k, c in sorted(s.cells.items()))
        open(p, 'w', encoding='utf-8', newline='\n').write('# %s（子作品 %s；世界座標，stampvox at=0,0,0；關聯 %s）—— draft_hold_ladders.py 產（%d 格）\n' % (TITLE, SUB, LINK, len(s.cells)) + body)
        s.files = {'hold': {'cells': len(s.cells), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}}
        json.dump({'note': '往下通貨艙的梯子扶手柱的柱頂（manrope-<梯>-<P|S>-<top|bot>；P ＝ y 小那一側）；世界座標；子作品 at 0,0,0', 'points': s.anchors},
                  open(os.path.join(D, 'rig_points_hold_ladders.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
        json.dump({'note': '往下通貨艙的每座梯子兩條扶手繩（掛在組裝件；端點是關聯路徑）', 'ropes': s.ropes},
                  open(os.path.join(D, 'hold_ladder_ropes.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    F = Hold(sys.argv[1])
    F.build()
    F.verify()
    F.write()
    F.v['files'] = F.files
    json.dump(F.v, open(os.path.join(HERE, 'verify_hold_ladders.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({k: F.v[k] for k in F.v if k != 'ladders'}, ensure_ascii=False))
    for r in F.rows:
        print(json.dumps(r, ensure_ascii=False))


if __name__ == '__main__':
    main()
