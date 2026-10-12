# 階段二十五：上 deadeye ＋ lanyards（靜索下端的掛法）⇒ design/rig_deadeyes.json
# 用法：python -I rig_deadeyes.py <design 資料夾>
#   之後照 ropes_apply.py <design> rig_deadeyes.json 下 CLI（overwrite=1，重跑一樣）
#   ⚠ 順序：rig_standing_apply.py 會把 shroud／backstay 的下端改回 channel 的 deadeye 固定點 ⇒ 重跑它之後要再跑一次本清單
#   · 下 deadeye：channels 子作品裡的 3×3（去四角）2 格厚、面朝舷外；固定點在它頂那一格（draft_channels.py）
#   · 上 deadeye：一段短而粗的繩當圓盤 —— 軸朝舷外、直徑 = 下 deadeye、長 = 下 deadeye 的厚，中心在 shroud 線上離下 deadeye 中心 SPACING 格
#   · lanyards：三條細繩，兩顆 deadeye 之間沿 shroud 方向、照船長方向排開
#   · shroud／backstay：下端改成上 deadeye 的頂（座標端點），上端不動
import sys, os, json
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import draft_planking as DP        # noqa: E402

D = os.path.abspath(sys.argv[1])
P = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['channels']
R = json.load(open(os.path.join(D, 'rig_standing.json'), encoding='utf-8'))
SPACING = 8.0                         # 兩顆 deadeye 中心的距離（格）
DIA = float(P['deadeye']['size'])      # 3
THK = float(P['deadeye']['thick'])     # 2
HOLE = 0.9                             # lanyard 照船長方向排開的距離
DEADEYE_C = '#%02x%02x%02x' % tuple(DP.rgb332(P['colors']['deadeye']))
LANYARD_C, LANYARD_T = '#a08458', 0.25
YC = 160

W = {}
for a in R['anchors']:
    W[a['link'] + '/' + a['name']] = np.array(a['world'], float)


def world(ref):
    if ref in W:
        return W[ref]
    link, rest = ref.split('/', 1)
    if link.endswith('-鏡像'):
        p = W[link[:-len('-鏡像')] + '/' + rest].copy()
        p[1] = 2 * YC - p[1]
        return p
    raise KeyError(ref)


def xyz(p):
    return '%.2f,%.2f,%.2f' % tuple(p)


ropes, rows = [], []
for r in R['ropes']:
    if not r['from'].startswith('channels'):
        continue
    top = world(r['from'])                       # 下 deadeye 頂那一格（格心）
    side = 1.0 if top[1] > YC else -1.0           # S 舷往 +y
    Lc = top + np.array([0.0, -side * (THK - 1) / 2, -(DIA - 1) / 2])   # 下 deadeye 的中心（3 格高、2 格厚）
    H = world(r['to'])
    u = (H - Lc) / np.linalg.norm(H - Lc)
    U = Lc + u * SPACING
    n = np.array([0.0, side, 0.0])
    a = np.array([1.0, 0.0, 0.0]) - u * u[0]
    a /= np.linalg.norm(a)
    base = r['name']
    ropes.append({'name': base + '.deadeye', 'from': xyz(U - n * THK / 2), 'to': xyz(U + n * THK / 2), 'thickness': DIA, 'slack': 1.0,
                  'color': DEADEYE_C, 'group': 'upper deadeye（一段粗繩當圓盤）'})
    for k, off in (('a', -HOLE), ('b', 0.0), ('c', HOLE)):
        ropes.append({'name': '%s.lanyard-%s' % (base, k), 'from': xyz(Lc + a * off + u * (DIA / 2)), 'to': xyz(U + a * off - u * (DIA / 2)),
                      'thickness': LANYARD_T, 'slack': 1.0, 'color': LANYARD_C, 'group': 'lanyard'})
    nr = dict(r)
    nr['from'] = xyz(U + u * (DIA / 2))
    nr['group'] = r['group'] + '（下端改到上 deadeye 頂）'
    ropes.append(nr)
    rows.append({'rope': base, 'lower_center': [round(v, 2) for v in Lc], 'upper_center': [round(v, 2) for v in U],
                 'shroud_len_before': round(float(np.linalg.norm(H - top)), 2), 'shroud_len_after': round(float(np.linalg.norm(H - (U + u * DIA / 2))), 2)})

# 錨的 cat fall：2026-10-12 掛過（兩段、越過 cap rail）⇒ Tim「錨我覺得不用繩子 看起來有點怪」⇒ 拿掉，不再產生

out = {'note': '階段二十五：上 deadeye（粗繩圓盤）＋ lanyards ＋ shroud／backstay 下端改到上 deadeye。掛在組裝件；端點是世界座標或關聯路徑',
       'spacing': SPACING, 'deadeye_color': DEADEYE_C, 'ropes': ropes, 'rows': rows}
json.dump(out, open(os.path.join(D, 'rig_deadeyes.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
print('ropes', len(ropes), '（deadeye', sum(1 for x in ropes if x['name'].endswith('.deadeye')), '、lanyard', sum(1 for x in ropes if '.lanyard-' in x['name']),
      '、改下端', len(rows), '）；deadeye 色', DEADEYE_C)
d = [x['shroud_len_before'] - x['shroud_len_after'] for x in rows]
print('shroud 縮短 %.2f–%.2f 格' % (min(d), max(d)))
