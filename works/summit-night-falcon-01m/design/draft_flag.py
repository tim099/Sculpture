# 新圖紙 12 旗（TASK-0529 階段十二）：plan.json 的 flag ⇒ 主桅 truck 上的旗桿（主桅子作品的格）、旗的兩個固定點、旗（帆＋貼圖）、verify_flag.json。
# 用法：python -I -X utf8 -B draft_flag.py <design 資料夾>
#   · 現況照 nf_state.state_after('stage10')（階段十一的帆是布，不是格）。
#   · 旗桿：truck 最上那一層（鐵）的格的中心那一欄，從 truck 上一格往上 staff_len 格（一格粗）；頂上一圈十字鐵帽。每一格都要是空的（assert）。
#   · 固定點（主桅子作品，世界座標 ＝ 子作品座標）：flag-top ＝ 旗桿頂下 top_below_staff_top 格、flag-bot ＝ 再往下 hoist 格。
#   · 旗：角 hoist_top（主桅/flag-top）→ fly_top → fly_bottom → hoist_bottom（主桅/flag-bot）；邊 3（hoist）釘住、fly 兩角 free；fly 初始在 +x（順著預設風）。
#     貼圖：左上角 ＝ 角 0（hoist_top）、欄沿 角 0→角 1、列沿 角 0→角 3。
#   · 檢查：平的旗（模擬之前）每 0.5 格取樣落在實心（格、帆桁）的數；旗桿格跟現況、帆桁的重疊。重跑逐位元組相同。
import sys, os, json, hashlib, math
import numpy as np
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import YC
from nf_state import state_after, occupancy, NX, NY, NZ
from draft_running import Run, G


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8')); F = plan['flag']; M = plan['masts']
    r = Run(d)                                   # 讀 stage10 ＋ 帆桁模型
    W = r.W; occ = occupancy(W); A = W['mast_' + F['mast']]
    tz = M[F['mast']]['truck_z'] + 1             # truck 兩層：truck_z、truck_z＋1
    t = np.argwhere(A[:, :, tz] == M['colors']['iron'])
    assert len(t), '找不到 truck 最上層'
    xc = int(np.round(t[:, 0].mean()))
    yc = int(np.round(t[:, 1].mean())); assert yc == YC, (yc, YC)
    cells = {}
    z0, z1 = tz + 1, tz + F['staff_len']
    for z in range(z0, z1 + 1): cells[(xc, YC, z)] = F['staff_color']
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)): cells[(xc + dx, YC + dy, z1 + 1)] = F['cap_color']
    yards = np.zeros_like(occ)
    for nm, P in r.Y.items():
        from draft_yards import rot
        for c in r.yard_cells[nm][:, :3] + np.asarray(P['origin']):
            yards[tuple(int(math.floor(v)) for v in rot([c[i] + 0.5 for i in range(3)], P['at'], P['rotate'][1], P['rotate'][2]))] = True
    for c in cells: assert not occ[c] and not yards[c], ('旗桿撞到', c)
    g = np.zeros((NX, NY, NZ), bool)
    for c in cells: g[c] = True
    g |= A > 0
    comp = int(ndimage.label(g)[1])
    ztop = z1 - F['top_below_staff_top']; zbot = ztop - F['hoist']
    anchors = [('flag-top', (xc, YC, ztop), 'flag-hoist'), ('flag-bot', (xc, YC, zbot), 'flag-hoist')]
    ht, hb = [xc + 0.5, YC + 0.5, ztop + 0.5], [xc + 0.5, YC + 0.5, zbot + 0.5]
    ft, fb = [ht[0] + F['fly'], ht[1], ht[2]], [hb[0] + F['fly'], hb[1], hb[2]]
    lk = {'main': '主桅', 'fore': '前桅'}[F['mast']]
    tex = os.path.normpath(os.path.join(d, F['texture'])).replace('\\', '/')
    from PIL import Image
    im = Image.open(tex); assert list(im.size) == F['texture_px'], (im.size, F['texture_px'])
    sail = {'name': 'ensign', 'corners': ['%s/flag-top' % lk, G(ft), G(fb), '%s/flag-bot' % lk], 'corner_names': ['hoist_top', 'fly_top', 'fly_bottom', 'hoist_bottom'],
            'corners_world': [ht, ft, fb, hb], 'bind': '3', 'free': 'fly_top,fly_bottom', 'fullness': F['fullness'], 'res': F['res'], 'texture': tex,
            'texture_sha256': hashlib.sha256(open(tex, 'rb').read()).hexdigest(), 'color': plan['sails']['color'],
            'note': '夜隼號的旗（v3：俯衝的隼）—— 階段十二，主桅 truck 上的旗桿'}
    # 平的旗碰撞
    hit = {}
    for u in np.linspace(0, 1, 61):
        for v in np.linspace(0, 1, 41):
            p = np.array(ht) + u * (np.array(ft) - np.array(ht)) + v * (np.array(hb) - np.array(ht))
            if u * F['fly'] < 1.2: continue
            c = tuple(int(math.floor(x)) for x in p)
            for k, vv in list(r.W.items()) + [('yards', yards)]:
                if (vv[c] > 0 if vv.dtype != bool else vv[c]): hit[k] = hit.get(k, 0) + 1
    rows = sorted((k[0], k[1], k[2], c) for k, c in cells.items())
    text = ''.join('%d,%d,%d,%d\n' % x for x in rows)
    od = os.path.join(d, 'masks', 'flag'); os.makedirs(od, exist_ok=True)
    open(os.path.join(od, 'staff.vox.txt'), 'w', encoding='utf-8', newline='\n').write(text)
    V = {'stamp_order': {'mast_main': [{'name': 'staff', 'op': 'stampvox', 'file': 'masks/flag/staff.vox.txt', 'at': [0, 0, 0], 'voxels': len(rows),
                                        'origin_world': [0, 0, 0], 'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}]},
         'staff': {'x': xc, 'z': [z0, z1 + 1], 'cells': len(rows), 'truck_top_z': tz, 'mast_components_after': comp},
         'anchors': {'mast_' + F['mast']: [{'name': n, 'at': list(c), 'world': list(c), 'kind': k} for n, c, k in anchors]},
         'sail': sail, 'flat_flag_hits': hit}
    with open(os.path.join(d, 'verify_flag.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(V, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps({k: V[k] for k in ('staff', 'anchors', 'flat_flag_hits')}, ensure_ascii=False))
    print(sail['corners'])


if __name__ == '__main__':
    main()
