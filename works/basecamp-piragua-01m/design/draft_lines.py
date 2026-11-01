# 杉心號 新圖紙 01（TASK-1152 步驟 3）：線形＋挖空的船殼 ⇒ 圖紙 sheet01_lines_v1.png、讀數 verify_lines.json、清單 masks/hull/hull.vox.txt
#   出處：apex-one-punt-01m/design/draft_lines.py（蓬特號）—— 拿掉柱與柱頭；讀數多船尾平板寬、艙內底面積、殼的重量。
#   用法：python -I -X utf8 draft_lines.py [--probe=half_beam=+3]
#   · 只讀 plan.json、不碰作品。船殼 ＝ 線形圍出來的實心往裡留 wall 格；舷頂以上多算 EXTRA 層再量距離 ⇒ 舷頂不會變成一層蓋子。
#   · --probe：反向對照（拿某個線形參數加減重算讀數，⛔ 不寫清單與圖）。
import sys, os, json
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
EXTRA = 20
SX, SY, SZ = 140, 101, 40
X0, X1, ZMAX = 0, SX - 1, SZ - 1
CEDAR_T_PER_M3 = 0.45          # 雪松（Cedrela odorata）氣乾密度約 0.45 t/m³〔估〕—— 只拿來讀「殼有多重」


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def build(plan, probe=None):
    L = HL.Lines(plan, probe)
    hb = plan['hull_build']
    C = {k: V(v) for k, v in hb['colors'].items()}
    wall = V(hb['wall'])
    wl = plan['waterline']['z']
    S = L.solid(X0, X1, ZMAX, 0)
    Sx = np.pad(L.solid(X0, X1, ZMAX, EXTRA), 1)
    core = Sx
    for _ in range(wall):                                # 26 鄰居剝 wall 層 ⇒ 舷側一階一階的地方斜角也補成面相連（6 連通的距離 ≤ wall 會斷成條）
        core = ndimage.binary_erosion(core, structure=np.ones((3, 3, 3), bool))
    shell = S & ~core[1:-1, 1:-1, 1:-1]
    G = np.zeros((SX, SY, SZ), np.uint8)
    G[shell] = C['hull']
    # 外面（面挨著船外空氣的格）照外皮色、水線下塗焦油色；只挨著艙內的格塗內面色；舷頂那一格塗深色帶
    touch_out = ndimage.binary_dilation(~Sx, structure=ndimage.generate_binary_structure(3, 1))[1:-1, 1:-1, 1:-1]   # 在補了邊的陣列上膨脹 ⇒ z 0 那層也挨得到底下的船外
    zz = np.arange(SZ)[None, None, :]
    G[shell & ~touch_out] = C['inner']
    G[shell & touch_out & (zz < wl)] = C['below']
    # 艙底（正上方一格是艙內空氣）一律內面色：底只有 1 格厚，從艙裡往下看的是它（玩家站在上面），v1 塗成焦油色整片黑
    up_hollow = np.zeros_like(shell)
    up_hollow[:, :, :-1] = (S & ~shell)[:, :, 1:]
    G[shell & up_hollow] = C['inner']
    xs = np.arange(X0, X1 + 1) + 0.5
    ztop = np.floor(L.zs(xs) - 0.5).astype(int)          # 每一站舷頂那一格
    for i, x in enumerate(range(X0, X1 + 1)):
        if L.xa <= x + 0.5 <= L.xf and 0 <= ztop[i] <= ZMAX:
            col = G[x, :, ztop[i]]
            col[col > 0] = C['band']
    return L, G, S


def readings(L, G, S, plan):
    wl = plan['waterline']['z']
    occ = G > 0
    R = {}
    lay = S[:, :, wl - 1]                                  # 水線下最上面那一層（z wl−1）
    xs = np.where(lay.any(axis=1))[0] + X0
    R['lwl_cells'] = int(xs.max() - xs.min() + 1) if len(xs) else 0
    R['bwl_cells'] = int(lay.any(axis=0).sum())
    R['beam_cells'] = int(S.any(axis=(0, 2)).sum())
    xo = np.where(occ.any(axis=(1, 2)))[0]
    R['loa_cells'] = int(xo.max() - xo.min() + 1)
    R['loa_x'] = [int(xo.min()), int(xo.max())]
    R['z_max'] = int(np.where(occ.any(axis=(0, 1)))[0].max())
    R['transom_width_cells'] = int(occ[int(L.xa)].any(axis=1).sum())
    R['bow_tip_x'] = int(xo.max())
    R['cells'] = int(occ.sum())
    R['color_counts'] = {str(int(c)): int((G == c).sum()) for c in np.unique(G[occ])}
    lab, n = ndimage.label(occ)
    R['components'] = int(n)
    la, na = ndimage.label(~occ)
    border = set(np.unique(np.r_[la[0].ravel(), la[-1].ravel(), la[:, 0].ravel(), la[:, -1].ravel(), la[:, :, 0].ravel(), la[:, :, -1].ravel()]))
    R['cavities'] = len([i for i in range(1, na + 1) if i not in border])
    R['mirror_diff'] = int((occ != occ[:, ::-1, :]).sum())
    R['hull_mass_t'] = round(R['cells'] * 0.001 * CEDAR_T_PER_M3, 2)
    R['displacement_t'] = round(float(S[:, :, :wl].sum()) * 0.001 * 1.025, 2)
    R['payload_t'] = round(R['displacement_t'] - R['hull_mass_t'], 2)
    # 艙內能站的底面：殼的內面上方一格是空的、還在船裡的格（z 1 那層的空心）
    floor = S[:, :, 1] & ~occ[:, :, 1]
    R['floor_cells'] = int(floor.sum())
    R['midship'] = {'x': int(L.xm), 'sheer_z': round(float(L.zs(L.xm)), 2), 'half_beam_at_sheer': round(float(L.Bs(L.xm)), 2)}
    return R


def sheet(L, G, plan, R, path):
    sc = 7
    W = SX * sc + 40
    H = 60 + SZ * sc + 30 + SY * sc // 2 + 30 + 20 * sc + 70
    im = Image.new('RGB', (W, H), (246, 240, 226))
    d = ImageDraw.Draw(im)
    f, fs = font(22), font(15)
    d.text((20, 10), '杉心號 新圖紙 01：線形、挖空的船殼（0.1 m／格；側面、平面、船中與船尾剖面）', fill=(40, 30, 20), font=f)
    oy = 50
    for x in range(SX):                                  # 側面：沿 +y 看，取 y 最小的非空
        for z in range(SZ):
            nz = np.nonzero(G[x, :, z])[0]
            if len(nz):
                d.rectangle([20 + x * sc, oy + (SZ - 1 - z) * sc, 20 + x * sc + sc - 1, oy + (SZ - z) * sc - 1], fill=rgb(int(G[x, nz[0], z])))
    wl = plan['waterline']['z']
    d.line([20, oy + (SZ - wl) * sc, 20 + SX * sc, oy + (SZ - wl) * sc], fill=(30, 90, 200), width=2)
    d.text((24, oy + (SZ - wl) * sc + 4), 'DWL z %d' % wl, fill=(30, 90, 200), font=fs)
    for x in range(0, SX, 10):
        d.text((20 + x * sc, oy + SZ * sc + 2), str(x), fill=(90, 80, 70), font=fs)
    oy2 = oy + SZ * sc + 30                              # 平面（俯視：最高那一格）
    for x in range(SX):
        for y in range(0, SY, 2):
            nz = np.nonzero(G[x, y, :])[0]
            if len(nz):
                d.rectangle([20 + x * sc, oy2 + y // 2 * sc, 20 + x * sc + sc - 1, oy2 + y // 2 * sc + sc - 1], fill=rgb(int(G[x, y, nz[-1]])))
    oy3 = oy2 + SY * sc // 2 + 30 + 14 * sc               # 剖面：船中、船尾平板（y 30–70、z 0–13）
    s2 = sc
    for k, (x, lab) in enumerate(((int(L.xm), '船中 x %d' % int(L.xm)), (int(L.xa), '船尾平板 x %d' % int(L.xa)), (int(L.xa) + 1, '平板內一站 x %d' % (int(L.xa) + 1)))):
        ox = 20 + k * 44 * s2
        for y in range(30, 71):
            for z in range(0, 14):
                if G[x, y, z]:
                    d.rectangle([ox + (y - 30) * s2, oy3 - z * s2, ox + (y - 30) * s2 + s2 - 1, oy3 - z * s2 + s2 - 1], fill=rgb(int(G[x, y, z])))
        d.text((ox, oy3 + s2 + 4), lab, fill=(40, 30, 20), font=fs)
    txt = 'LOA %d 格（x %d–%d）｜寬 %d｜LWL %d｜BWL %d｜船尾平板寬 %d｜排水量 %.2f t（殼 %.2f t、可載 %.2f t）｜元件 %d｜空腔 %d｜鏡像差 %d' % (
        R['loa_cells'], R['loa_x'][0], R['loa_x'][1], R['beam_cells'], R['lwl_cells'], R['bwl_cells'], R['transom_width_cells'],
        R['displacement_t'], R['hull_mass_t'], R['payload_t'], R['components'], R['cavities'], R['mirror_diff'])
    d.text((20, H - 30), txt, fill=(40, 30, 20), font=fs)
    im.save(path)


def main():
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = float(v)
    plan = HL.load_plan()
    L, G, S = build(plan, probe or None)
    R = readings(L, G, S, plan)
    if probe:
        print(json.dumps({'probe': probe, **R}, ensure_ascii=False))
        return
    os.makedirs(os.path.join(HERE, 'masks', 'hull'), exist_ok=True)
    pts = np.argwhere(G > 0)
    with open(os.path.join(HERE, 'masks', 'hull', 'hull.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 杉心號 船殼（draft_lines.py）x,y,z,color —— at 0,0,0\n')
        f.write('\n'.join('%d,%d,%d,%d' % (x, y, z, G[x, y, z]) for x, y, z in pts) + '\n')
    with open(os.path.join(HERE, 'verify_lines.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    sheet(L, G, plan, R, os.path.join(HERE, 'sheet01_lines_v1.png'))
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
