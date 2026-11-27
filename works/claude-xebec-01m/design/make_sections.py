# 利劍號 步驟 3：Chapman Pl. LVIII No.17 的剖面表（重新對號）⇒ sections.json
#   讀數來源：references/chapman_lines_agent_2026-11-24.json（Paperclip FAR-92 .work/FAR-92/sayf/research/lines_agent/lines.json 的副本：
#   lines_agent 從 4000 px 掃描追線，每 0.25 m 一點，比例 20.537 px／瑞典呎）。
#   ⚠ lines_agent 的標號照「由外往內的順序」給，錯了：Claude-Ojousama 照每條線跟 body plan 斜線的交點、對最近的標號重新對號
#   （艉段斜線 (2114,618)→(1975,735)、艏段 (2135,618)→(2300,755)；交點都落在標號下方 4–9 px，一致）：
#     艏段 agent「midship,B,D,F,H,K,M」＝ 實際 F,H,K,M,N,O,P；艉段 agent「4,6,10,12,14,16,17,(None#10)」＝ 實際 6,8,10,12,14,15,16,17。
#     agent 艉段最外那條（它標 midship，跟斜線不相交）當 midship 船中（設計決定：xebec 船中 4–D 幾站幾乎一樣；它是最外的一條）。
#   座標：X 從 AP 往前、Z 從龍骨底、Y 半寬，都 × TABLE_K（0.99341：讓圖上 Lpp 131.2 呎對齊 Chapman 尺寸表的 130 1/3 呎）。
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = json.load(open(os.path.join(HERE, '..', 'references', 'chapman_lines_agent_2026-11-24.json'), encoding='utf-8'))
K = json.load(open(os.path.join(HERE, 'plan.json'), encoding='utf-8'))['lines']['table_k']['v']   # 跟 plan.json 同一個值（lines.py 會檢查）
ST = {s['label']: s['X'] for s in SRC['stations']}
# (agent 的 side、order_from_outside) ⇒ 實際站名
MAP = {('aft_left', 0): 'midship', ('aft_left', 2): '6', ('aft_left', 3): '8', ('aft_left', 5): '10', ('aft_left', 6): '12',
       ('aft_left', 7): '14', ('aft_left', 8): '15', ('aft_left', 9): '16', ('aft_left', 10): '17',
       ('fore_right', 0): 'F', ('fore_right', 1): 'H', ('fore_right', 2): 'K', ('fore_right', 3): 'M',
       ('fore_right', 4): 'N', ('fore_right', 5): 'O', ('fore_right', 6): 'P'}
out = []
for s in SRC['body_plan']['sections']:
    key = (s['side_on_plate'], s['order_from_outside'])
    if key not in MAP:
        continue
    lab = MAP[key]
    X = ST[lab]
    out.append({'station': lab, 'X': round(X * K, 3), 'agent_label': s['label_by_order'], 'agent_side': s['side_on_plate'],
                'ZY': [[round(z * K, 3), round(y * K, 3)] for z, y in s['points_ZY_every_0.25m']]})
# 12、10 站 lines_agent 只追到 Z 1.5／2.0 m：上半段補 verifier3 在原圖上逐列追的線（references/chapman_bodyplan_trace_verifier3_2026-11-24.json，
#   像素 [x, y]：body plan 中線 x 2125.5、基線 y 773.1388、0.014457 m/px）——verifier3 抓到內插的 12 站上半段窄到 5.6 格（2026-11-24）。
#   只取比 agent 最高點還高的那段，每 0.25 m 重取樣。
VT = json.load(open(os.path.join(HERE, '..', 'references', 'chapman_bodyplan_trace_verifier3_2026-11-24.json'), encoding='utf-8'))
CX, BY, MPX = 2125.5, 773.1387559808612, 0.014457
for r in out:
    if r['station'] in ('12', '10'):
        P = VT['L' + r['station']]
        zs = [(BY - y) * MPX * K for x, y in P]; ys = [abs(x - CX) * MPX * K for x, y in P]
        o = sorted(range(len(zs)), key=lambda i: zs[i])
        zs = [zs[i] for i in o]; ys = [ys[i] for i in o]
        ztop = max(p[0] for p in r['ZY'])
        z = (int(ztop / 0.25) + 1) * 0.25 * K
        add = []
        while z <= zs[-1]:
            j = next(i for i in range(1, len(zs)) if zs[i] >= z)
            y = ys[j - 1] + (ys[j] - ys[j - 1]) * (z - zs[j - 1]) / max(1e-9, zs[j] - zs[j - 1])
            add.append([round(z, 3), round(y, 3)])
            z += 0.25 * K
        r['ZY'] += add
        r['upper_from'] = 'verifier3 rt3 trace（Z > %.2f）' % ztop
out.sort(key=lambda r: r['X'])
json.dump({'source': 'Chapman 1768 Pl. LVIII No.17 body plan, lines_agent trace, relabelled by diagonal crossings', 'K': K,
           'sections': out}, open(os.path.join(HERE, 'sections.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
for r in out:
    zs = [p[0] for p in r['ZY']]
    print(r['station'], r['X'], 'agent', r['agent_label'], 'Z %.2f–%.2f' % (min(zs), max(zs)), len(zs))
