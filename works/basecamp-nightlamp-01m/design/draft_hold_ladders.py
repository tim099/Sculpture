# 貨艙梯子（TASK-1137；Tim 2026-10-31「補夜燈號」）：hold_ladders.json ＋ 組裝件現在的 export list
#   ⇒ masks/ladders/hold_ladders.vox.txt（子作品 -ladders、船殼座標、關聯 at 0,0,0）、hold_ladder_points.json、verify_hold_ladders.json、sheet12_ladders_hold.png
# 用法：python -I draft_hold_ladders.py <design 資料夾> <組裝件 export list>
#   · 幾何、檢查、給遊戲的四個點全照 draft_ladders.py（Ladders.build_one／flat_from／render_sheet）—— 這支只換掉起點：
#     不開梯口（貨艙口上下兩層本來就開著），組裝件格數照 hold_ladders.json 的 assembly_cells 斷言。
#   · 梯腳落在艙底：Ladders.floor_below 量到的就是那一柱內板的頂 ＋ 1（造船規格 §9.3 ⑥「lo ＝ hold」的同一個意思）。
import sys, os, json, hashlib
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import draft_planking as DP      # noqa: E402
import draft_ladders as DL       # noqa: E402


class HoldLadders(DL.Ladders):
    def __init__(s, design, asm_list):
        s.design = design
        s.plan = json.load(open(os.path.join(design, 'plan.json'), encoding='utf-8'))
        H = json.load(open(os.path.join(design, 'hold_ladders.json'), encoding='utf-8'))
        s.P = dict(s.plan['ladders'])
        s.P.update({'list': H['list'], 'assembly_cells': H['assembly_cells'], 'scuttles': [], 'version': 'hold'})
        w = DP.read_list(asm_list)
        assert len(w) == s.P['assembly_cells'], ('組裝件格數對不上', len(w), s.P['assembly_cells'])
        s.asm_sha = hashlib.sha256(open(asm_list, 'rb').read()).hexdigest()
        s.Wc = w
        xs, ys, zs = zip(*w.keys())
        s.W = np.zeros((DL.NX, DL.NY, max(DL.NZ, max(zs) + 1)), bool)
        s.W[list(xs), list(ys), list(zs)] = True
        s.carve = {}
        s.cells, s.points, s.rows = {}, {}, []

    def write(s):
        out = os.path.join(s.design, 'masks', 'ladders')
        os.makedirs(out, exist_ok=True)
        p = os.path.join(out, 'hold_ladders.vox.txt')
        body = ''.join('%d,%d,%d,%d\n' % (c[0], c[1], c[2], v) for c, v in sorted(s.cells.items()))
        open(p, 'w', encoding='utf-8', newline='\n').write(
            '# 夜燈號 貨艙梯子 %d 座（子作品 -ladders；船殼座標；stampvox at=0,0,0；draft_hold_ladders.py 產，TASK-1137；%d 格）\n'
            % (sum(1 for r in s.rows if r['placed']), len(s.cells)) + body)
        s.files = {'hold_ladders': {'cells': len(s.cells), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}}
        json.dump({'note': '貨艙梯子給遊戲的點（造船規格 §9：<梯名>.foot／.lo／.hi／.head，腳踩的那一格；foot 在艙底）；船殼座標 ＝ 子作品座標（關聯 at 0,0,0）',
                   'points': s.points}, open(os.path.join(s.design, 'hold_ladder_points.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)


def main():
    design, asm = sys.argv[1], sys.argv[2]
    F = HoldLadders(design, asm)
    F.build()
    F.verify()
    F.write()
    F.v['files'] = F.files
    F.v['ladders'] = F.rows
    F.v['assembly_list_sha256'] = F.asm_sha
    json.dump(F.v, open(os.path.join(design, 'verify_hold_ladders.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    if any(r['placed'] for r in F.rows):
        DL.render_sheet(F, os.path.join(design, 'sheet12_ladders_hold.png'))
    print(json.dumps({k: F.v[k] for k in F.v if k not in ('ladders', 'files')}, ensure_ascii=False))
    for r in F.rows:
        print(json.dumps({k: r[k] for k in r if k != 'points'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
