# 步驟 7 主桅與拉丁帆桁（kiara-tunis-sandal-01m-mast / kiara-tunis-sandal-01m-yard）：
#   - 主桅：於 (x=81, y=50) 從艙底鋪板頂 z=2 起立至 z=56（頂端帶滑輪桅首塊 calcet 與帽頭）
#   - 拉丁帆桁：水平 78 格（7.8 m）於子作品沿 +X 建置，帶接榫加厚段與繩箍，設 pivot / sling / peak / fore / earing-A / earing-F / top-00..14
#   - 掛入桅子作品並以 rotate=0,34,0°（前傾下伏）懸於桅左舷 y=48.5, z=42.0，確保與船殼／甲板／裝飾／桅桿零碰撞
#   用法：python -I -X utf8 draft_masts.py [--probe=mast_x=+3]
import sys, os, json, math
import numpy as np
from scipy import ndimage
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SX, SY, SZ = 136, 101, 110
YC = 50


def rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def load_vox(path, shape=(SX, SY, 30)):
    a = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    G = np.zeros(shape, np.uint8)
    if len(a):
        G[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]
    return G


def build(probe):
    dx_m = int(probe.get('mast_x', 0))
    mx = 81 + dx_m

    # 1. 主桅 (136, 101, 110)
    M = np.zeros((SX, SY, SZ), np.uint8)
    # 桅跟與穿過座板桅孔 (z 2..6)：十字補強，z=4 為深木桅圍襯
    for z in range(2, 7):
        col = 68 if z in (2, 4) else 136
        M[mx - 1:mx + 2, YC, z] = col
        M[mx, YC - 1:YC + 2, z] = col
    # 主桅身 (z 7..51)，帶繩箍節
    for z in range(7, 52):
        M[mx, YC, z] = 68 if z in (18, 30, 42, 48) else 136
    # 地中海拉丁桅首 calcet (z 52..55) 與金頂帽 (z 56)
    for z in range(52, 56):
        M[mx - 1:mx + 1, YC, z] = 68
    M[mx, YC, 56] = 208

    # 2. 拉丁帆桁 (84, 5, 5)：x 2..79 長 78 格 (7.8 m)，中心軸 y=2, z=2
    Y = np.zeros((84, 5, 5), np.uint8)
    for x in range(2, 80):
        # 中央雙木搭接段 x=28..64 較粗
        Y[x, 2, 2] = 136
        if 28 <= x <= 64:
            Y[x, 2, 3] = 68 if x in (30, 38, 46, 54, 62) else 136
    # 雙端飾帽
    Y[2, 2, 2] = 68
    Y[79, 2, 2] = 68

    # 帆桁固定點（未旋轉、子作品內格點）
    anchors = [
        ('pivot',    (47, 2, 2), '步驟 7 帆桁轉軸'),
        ('sling',    (47, 2, 3), '步驟 7 帆桁吊環'),
        ('fore',     (79, 2, 2), '步驟 7 拉丁帆桁前端 car'),
        ('earing-F', (77, 2, 2), '步驟 7 帆桁前帆角'),
        ('peak',     (2, 2, 2),  '步驟 7 帆桁上尖端 peak'),
        ('earing-A', (4, 2, 2),  '步驟 7 帆桁後上帆角'),
    ]
    xs_top = list(range(4, 78, 5))
    if xs_top[-1] != 77:
        xs_top.append(77)
    for idx, tx in enumerate(xs_top):
        tz = 3 if 28 <= tx <= 64 else 2
        anchors.append((f'top-{idx:02d}', (tx, 2, tz), '步驟 7 帆桁綁繩點'))

    # 掛載參數（rotate 0, 34, 0° 繞 Y 軸前俯、pivot 對齊主桅 y 左側）
    mount = {
        'name': 'yard',
        'work': 'kiara-tunis-sandal-01m-yard',
        'at': [float(mx) + 0.5, 48.5, 39.0],
        'pivot': [47.5, 2.5, 2.5],
        'rotate': [0.0, 34.0, 0.0],
        'meta': {
            'id': 'yard-1',
            'kind': 'yard',
            'mast': 'main',
            'yard': 'gaff',
            'rig': 'lateen',
            'sail': 'lateen',
            'length_m': 7.8,
            'length_ft': 25.6,
            'diameter_in': 6,
            'diameter_m': 0.15,
            'pivot_anchor': 'pivot',
            'turn_axis': 'z',
            'rotate_y_deg': 34.0,
            'rotate_z_deg': 0,
        },
    }
    return M, Y, anchors, mount


def yard_world_boxes(Y, mount):
    pts = np.argwhere(Y > 0)
    px, py, pz = mount['pivot']
    ax, ay, az = mount['at']
    ang = math.radians(mount['rotate'][1])  # +Y 軸旋轉：+X -> -Z
    ca, sa = math.cos(ang), math.sin(ang)
    wpts = []
    for x, y, z in pts:
        dx = (x + 0.5) - px
        dy = (y + 0.5) - py
        dz = (z + 0.5) - pz
        wx = ax + dx * ca + dz * sa
        wy = ay + dy
        wz = az - dx * sa + dz * ca
        wpts.append((wx, wy, wz))
    return wpts


def main():
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = float(v)

    H = load_vox(os.path.join(HERE, 'masks', 'hull', 'hull.vox.txt'))
    D = load_vox(os.path.join(HERE, 'masks', 'deck', 'deck_main.vox.txt'))
    occ = np.zeros((SX, SY, SZ), bool)
    occ[:, :, :30] = (H > 0) | (D > 0)

    M, Y, anchors, mount = build(probe)
    m_occ = M > 0
    overlap_hull = int((m_occ[:, :, :30] & (H > 0)).sum())
    overlap_deck = int((m_occ[:, :, :30] & (D > 0)).sum())

    # 檢查主桅自己的格子是否符合 shipcheck「最低帆桁轉軸往下 10–40 格、中線 ±4」
    pz = mount['pivot'][2]
    az = mount['at'][2]
    z_lo = max(0, int(math.floor(az - 40)))
    z_hi = min(SZ - 1, int(math.ceil(az - 10)))
    mast_in_band = int(m_occ[:, YC - 4:YC + 5, z_lo:z_hi + 1].sum())

    # 檢查帆桁旋轉至世界空間後有無撞船／撞桅
    yw = yard_world_boxes(Y, mount)
    yard_hits = 0
    for wx, wy, wz in yw:
        ix, iy, iz = int(math.floor(wx)), int(math.floor(wy)), int(math.floor(wz))
        if 0 <= ix < SX and 0 <= iy < SY and 0 <= iz < SZ:
            if occ[ix, iy, iz] or m_occ[ix, iy, iz]:
                yard_hits += 1

    # 計算 fore 與 peak 座標與 lateen 限角
    ax, ay, az = mount['at']
    px, py, pz = mount['pivot']
    ang = math.radians(mount['rotate'][1])
    ca, sa = math.cos(ang), math.sin(ang)
    fore_x = ax + (79.5 - px) * ca
    fore_z = az - (79.5 - px) * sa
    peak_x = ax + (2.5 - px) * ca
    peak_z = az - (2.5 - px) * sa
    horiz_fore_m = (fore_x - ax) * 0.1
    lateen_max_deg = round(math.degrees(math.asin(min(1.0, 2.5 / max(0.01, horiz_fore_m)))), 1)

    _, n_mast = ndimage.label(M > 0)
    _, n_yard = ndimage.label(Y > 0)
    mir_mast = int((M != M[:, ::-1, :]).sum())

    R = {
        'mast_cells': int((M > 0).sum()),
        'yard_cells': int((Y > 0).sum()),
        'mast_components': int(n_mast),
        'yard_components': int(n_yard),
        'mast_mirror_color_diff': mir_mast,
        'mast_overlap_hull': overlap_hull,
        'mast_overlap_deck': overlap_deck,
        'mast_in_shipcheck_band': mast_in_band,
        'yard_world_hits': yard_hits,
        'fore_world': [round(fore_x, 2), round(ay, 2), round(fore_z, 2)],
        'peak_world': [round(peak_x, 2), round(ay, 2), round(peak_z, 2)],
        'horiz_pivot_to_fore_m': round(horiz_fore_m, 2),
        'lateen_max_swing_deg': lateen_max_deg,
        'anchor_count': len(anchors),
    }

    if probe:
        print(json.dumps({'probe': probe, **{k: R[k] for k in ('mast_overlap_hull', 'mast_overlap_deck', 'mast_in_shipcheck_band')}}, ensure_ascii=False))
        return

    out_dir = os.path.join(HERE, 'masks', 'masts')
    os.makedirs(out_dir, exist_ok=True)
    for fn, arr in [('mast.vox.txt', M), ('yard.vox.txt', Y)]:
        pts = np.argwhere(arr > 0)
        with open(os.path.join(out_dir, fn), 'w', encoding='utf-8', newline='\n') as f:
            f.write(f'# 突尼斯湖轉運艇 Sandal {fn}（draft_masts.py）x,y,z,color\n')
            for x, y, z in pts:
                f.write(f'{x},{y},{z},{arr[x, y, z]}\n')

    with open(os.path.join(HERE, 'yard_anchors.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(anchors, f, indent=2, ensure_ascii=False)
    with open(os.path.join(HERE, 'yard_mount.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(mount, f, indent=2, ensure_ascii=False)
    with open(os.path.join(HERE, 'verify_masts.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, indent=1, ensure_ascii=False)

    # 側視＋俯視圖紙 sheet03_masts_v1.png
    sc = 6
    W, Hh = SX * sc + 40, 60 + 82 * sc + 60
    im = Image.new('RGB', (W, Hh), (246, 240, 226))
    d = ImageDraw.Draw(im)
    f, fs = font(21), font(14)
    d.text((20, 10), '突尼斯湖轉運艇 Sandal 新圖紙 03：主桅 (z=2..56) 與 7.8 m 拉丁帆桁 (34°)', fill=(40, 30, 20), font=f)
    oy = 40 + 76 * sc
    A = np.where(M > 0, M, 0)
    A[:, :, :30] = np.where(A[:, :, :30] > 0, A[:, :, :30], np.where(D > 0, D, H))
    for x in range(SX):
        for z in range(76):
            nz = np.nonzero(A[x, :, z])[0]
            if len(nz):
                c = int(A[x, YC, z]) if A[x, YC, z] else int(A[x, nz[-1], z])
                d.rectangle([20 + x * sc, oy - z * sc, 20 + x * sc + sc - 1, oy - z * sc + sc - 1], fill=rgb(c))
    # 疊畫旋轉後的帆桁紅棕投影
    for wx, wy, wz in yw:
        gx, gz = int(math.floor(wx)), int(math.floor(wz))
        d.rectangle([20 + gx * sc, oy - gz * sc, 20 + gx * sc + sc - 1, oy - gz * sc + sc - 1], fill=(170, 50, 20))
    for x in range(0, SX, 10):
        d.text((20 + x * sc, oy + sc + 2), str(x), fill=(90, 80, 70), font=fs)
    d.text((20, Hh - 30), '桅 %d 格 (元件 %d、鏡像差 %d)｜桁 %d 格 (元件 %d、碰撞 %d)｜fore (%.1f, %.1f)｜peak (%.1f, %.1f)｜擺角限 %.1f°' % (
        R['mast_cells'], R['mast_components'], R['mast_mirror_color_diff'],
        R['yard_cells'], R['yard_components'], R['yard_world_hits'],
        fore_x, fore_z, peak_x, peak_z, lateen_max_deg), fill=(40, 30, 20), font=fs)
    im.save(os.path.join(HERE, 'sheet03_masts_v1.png'))
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
