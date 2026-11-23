# 海鷗號 桅的幾何（TASK-0024）：plan.json layout.masts ⇒ 每根桅的軸與格子。draft_decks.py（開桅孔）與 draft_masts.py（桅本身）共用同一支，
#   孔跟桅一定對得上。只讀 plan.json。
#   · 軸：腳 (x+0.5, YC+0.5, heel_z)，往船頭傾 rake_deg（x 隨 z 增加），頂 top_z（鉛直高度）。
#   · 截面：格心離軸 ≤ r 的格（每一層 z 照那一層的軸心算）。
import math


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def mast_rows(plan):
    """主桅腳踩在船中艙底（z 2）、頂在舷頂以上 above_rail_m；前桅腳踩在船頭艙底（z 5）、頂在平台站面以上 above_platform_m。"""
    lay = {k: V(v) for k, v in plan['layout'].items() if k != 'src'}
    m = lay['masts']
    rail_z = V(plan['lines']['deck_side_z']) + 1                 # 舷頂面（船中）
    stand = lay['bow_platform']['board_z'] + 1
    return {
        'main': {'x': m['main']['x'], 'heel_z': 2, 'top_z': int(round(rail_z + m['main']['above_rail_m'] * 10)), 'rake_deg': m['main']['rake_deg'], 'r': m['main']['r']},
        'fore': {'x': m['fore']['x'], 'heel_z': 5, 'top_z': int(round(stand + m['fore']['above_platform_m'] * 10)), 'rake_deg': m['fore']['rake_deg'], 'r': m['fore']['r']},
    }


def axis_x(row, z):
    return row['x'] + 0.5 + (z + 0.5 - row['heel_z']) * math.tan(math.radians(row['rake_deg']))


def section(row, z, yc, r=None):
    r = row['r'] if r is None else r
    xc = axis_x(row, z)
    cells = []
    for x in range(int(math.floor(xc - r - 1)), int(math.ceil(xc + r + 1)) + 1):
        for dy in range(-3, 4):
            if (x + 0.5 - xc) ** 2 + dy * dy <= r * r + 1e-9:
                cells.append((x, yc + dy, z))
    return cells


def mast_cells(plan, name, yc):
    row = mast_rows(plan)[name]
    out = []
    for z in range(row['heel_z'], row['top_z']):
        out += section(row, z, yc)
    return out
