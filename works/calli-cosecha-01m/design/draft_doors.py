# 出處：apex-two-galeon-01m/design/draft_doors.py（康塞普西翁號步驟 17 那一段，照抄 —— 收穫號 TASK-1027）
# 收穫號 真的門（kind=door）：船頭 beakhead 艙壁兩扇、船尾兩層 stern walk 各一扇（Tim 2026-10-27 照康塞普西翁號：「開真的可以打開的門(第一人稱模式可以走出去) 船尾有陽台的地方也可以開門出去」）
#   · 門洞是船殼刻的（draft_ports.py ⇒ verify_ports.json doors：門洞範圍、門板的 x）；門板沿用藍鯊號 gura-pinas-01m-door（0.05 m：厚 2、寬 14、高 32 ⇒ 船上 1 × 7 × 16 格）、
#     只縮放高度（scale z ＝ 門板格數 ÷ 32）；掛在門洞那一層甲板的子作品（船尾朝 −x ⇒ rotate 180、beakhead 朝 +x ⇒ 0）
#   · 收穫號的 break 艙壁（draft_decks.py 開的門洞）沒有門板 —— 不在本單
#   輸出：doors_placement.json、verify_doors.json
#   用法：python -I -X utf8 draft_doors.py <design>
import sys, os, json
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools'))
from wio import export_list

SIZE = (2, 14, 32)
PIVOT = (1, 7, 0)
SCALE = 0.5
DECK_WORK = {'alcazar': 'calli-cosecha-01m-deck-alcazar', 'toldilla': 'calli-cosecha-01m-deck-toldilla', 'castillo': 'calli-cosecha-01m-deck-castillo',
             'puente': 'calli-cosecha-01m-deck-puente', 'main': 'calli-cosecha-01m-deck-main'}


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    design = sys.argv[1]
    A = export_list('calli-cosecha-01m-assembly', None, links=None)
    occ = set(map(tuple, A[:, :3].tolist()))
    rows, problems = [], []
    VP = json.load(open(os.path.join(design, 'verify_ports.json'), encoding='utf-8'))
    for dc in VP.get('doors', []):
        yc = (dc['y0'] + dc['y1']) // 2
        fx, zb, mh = dc['door_x'], dc.get('model_z0', dc['z0']), dc['model_h']     # 門板底邊（beakhead：從平台面立起、比門洞低 2 格 ⇒ 連門檻一起蓋）
        out = 1 if dc['face'] == 'fwd' else -1
        cells = [(fx, y, z) for y in range(yc - 3, yc + 4) for z in range(zb, zb + mh)]
        hit = [c for c in cells if c in occ]
        hole = [(x, y, z) for x in range(fx - 6 * out, fx, out) for y in range(dc['y0'], dc['y1'] + 1) for z in range(dc['z0'], dc['z1'] + 1)]
        foot = all((fx, y, zb - 1) in occ for y in range(yc - 3, yc + 4))
        side = 'C' if yc == 160 else ('S' if yc > 160 else 'P')
        nm = '門-%s-%s' % ('beakhead' if dc['face'] == 'fwd' else 'stern-' + dc['deck'], side)
        rows.append({'name': nm, 'host': DECK_WORK[dc['deck']], 'break': 'beakhead 艙壁' if dc['face'] == 'fwd' else '船尾 %s 那一層的 stern walk' % dc['deck'], 'side': side,
                     'at': [fx + 0.5, yc + 0.5, zb], 'rotate': 0 if out > 0 else 180, 'scale_z': mh / 32.0, 'opening': [dc['y1'] - dc['y0'] + 1, dc['z1'] - dc['z0'] + 1],
                     'hits_solid': len(hit), 'opening_solid': sum(1 for h in hole if h in occ), 'foot_ok': foot, 'meta': {'kind': 'door', 'open': 'side'}})
        if hit:
            problems.append('%s 撞實心 %d' % (nm, len(hit)))
        if not foot:
            problems.append('%s 門底下沒有地板' % nm)
    verify = {'doors': len(rows), 'problems': problems, 'rows': rows}
    json.dump({'work': 'gura-pinas-01m-door', 'size': list(SIZE), 'pivot': list(PIVOT), 'scale': SCALE, 'rows': rows},
              open(os.path.join(design, 'doors_placement.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    json.dump(verify, open(os.path.join(design, 'verify_doors.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps({k: verify[k] for k in ('doors', 'problems')}, ensure_ascii=False))
    for r in rows:
        print(' ', r['name'], r['at'], 'rot', r['rotate'], '洞', r['opening'], '撞', r['hits_solid'], '門洞裡實心', r.get('opening_solid'), '腳', r['foot_ok'])


if __name__ == '__main__':
    main()
