# 新圖紙 11 旗（TASK-0547 階段十一；從夜隼號 draft_flag.py 改，一面變兩面）：plan.json 的 flags ⇒ 旗桿（格）、旗的固定點、旗（帆＋破旗貼圖）、meta、verify_flags.json。
# 用法：python -I -X utf8 -B draft_flags.py <design 資料夾>
#   · 現況照 sk_world.World（船＋桅＋channels＋帆桁轉好）。
#   · 船尾旗（ensign）：船尾拱頂（stern_deco）中線最高那一格上面，往上 staff_len 格一欄（旗桿）、頂上一圈十字鐵帽；格放在船尾裝飾子作品（at 0,0,0 ⇒ 子作品座標 ＝ 世界座標）。
#   · 長旗（pennant）：主桅最上那一層的中心那一欄往上，同上；格放在主桅子作品。
#   · 固定點（同一件子作品）：<旗名>-top ＝ 旗桿頂下 top_below_staff_top 格、<旗名>-bot ＝ 再往下 hoist 格。
#   · 旗：角 hoist_top（固定點）→ fly_top → fly_bottom → hoist_bottom（固定點）；邊 3（hoist）釘住、fly 兩角 free；fly 初始在 +x（順著預設風）。
#     貼圖：左上角 ＝ 角 0（hoist_top）、欄沿 角 0→角 1（hoist → fly）、列沿 角 0→角 3（上 → 下）。
#       ensign：紅白藍橫三條（褪色）＋白帶正中 VOC 交織字母；洞、fly 邊撕爛。pennant：紅白藍沿長邊、尾巴燕尾、尾端撕爛。亂數種子 ＝ 旗名的 crc32。
#   · meta（造船規格 §9.1）：kind=flag、flag=ensign｜pennant ⇒ flags_meta.tsv。
#   · 檢查：旗桿每一格原本是空的、不碰帆桁（assert）、跟底下那一格相連；平的旗（模擬之前）每 0.5 格取樣落在實心的數（按件分）。重跑逐位元組相同。
import sys, os, json, math, zlib, hashlib
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sk_world import World

G = lambda v: ','.join('%.4f' % c for c in v)


def noise_rgb(rng, H, W, rows, n):
    rgb = np.zeros((H, W, 3), float)
    for r0, r1, col in rows: rgb[r0:r1] = col
    return rgb + rng.integers(-n, n + 1, size=(H, W, 1))


def ragged_end(img, rng, tat):
    """fly 那一邊（最後幾欄）撕爛：隨機漫步的鋸齒＋1–2 道往 hoist 那邊的撕裂口（同帆）。"""
    H, W = img.shape[:2]
    walk = np.cumsum(rng.integers(-1, 2, size=H)); walk = walk - walk.min()
    rag = np.clip(np.round(walk * tat / max(1, walk.max())), 0, tat).astype(int)
    for y in range(H):
        if rag[y]: img[y, W - rag[y]:, 3] = 0
    for _ in range(int(rng.integers(1, 3))):
        y0 = rng.uniform(0.15 * H, 0.85 * H); ln = rng.uniform(0.10, 0.25) * W; wd = rng.uniform(0.6, 1.4)
        for k in range(int(ln)):
            hw = wd * (1 - k / ln); yc = y0 + rng.uniform(-0.5, 0.5)
            img[max(0, int(yc - hw)):min(H, int(yc + hw) + 1), W - 1 - k, 3] = 0


def holes(img, rng, n, hr):
    H, W = img.shape[:2]; yy, xx = np.mgrid[0:H, 0:W]
    for _ in range(n):
        cx, cy = rng.uniform(0.2 * W, 0.85 * W), rng.uniform(0.15 * H, 0.85 * H); r = rng.uniform(*hr)
        img[(xx - cx) ** 2 + (yy - cy) ** 2 <= r * r, 3] = 0


def ensign_png(name, T, C):
    W, H = T['px']; rng = np.random.default_rng(zlib.crc32(name.encode('utf-8')))
    b = [0, H // 3, 2 * H // 3, H]
    img = np.zeros((H, W, 4), np.uint8)
    rgb = noise_rgb(rng, H, W, [(b[0], b[1], C['red']), (b[1], b[2], C['white']), (b[2], b[3], C['blue'])], 10)
    # VOC 交織字母：大 V，O 在左臂、C 在右臂（白帶正中）
    mono = np.zeros((H, W), bool)
    cx, top, bot = W / 2, b[1] + 1, b[2] - 2
    half = (bot - top) * 0.55
    for t in np.linspace(0, 1, 60):
        z = top + t * (bot - top)
        for s in (-1, 1):
            x = cx + s * half * (1 - t)
            mono[int(round(z)), int(round(x))] = True
    yy, xx = np.mgrid[0:H, 0:W]
    r = 2.6; oy = top + (bot - top) * 0.35
    ring = lambda ox: np.abs(np.hypot(xx - ox, yy - oy) - r) < 0.6
    mono |= ring(cx - half * 0.62)
    mono |= ring(cx + half * 0.62) & (xx < cx + half * 0.62 + 1.2)      # C：右邊開口
    rgb[mono] = np.array(C['monogram'], float) + rng.integers(-4, 5, size=(int(mono.sum()), 1))
    img[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8); img[:, :, 3] = 255
    holes(img, rng, T['holes'], T['hole_r'])
    ragged_end(img, rng, T['tatter_px'])
    return img


def pennant_png(name, T, C):
    W, H = T['px']; rng = np.random.default_rng(zlib.crc32(name.encode('utf-8')))
    img = np.zeros((H, W, 4), np.uint8)
    rgb = noise_rgb(rng, H, W, [(0, H // 3, C['red']), (H // 3, 2 * H // 3, C['white']), (2 * H // 3, H, C['blue'])], 10)
    img[:, :, :3] = np.clip(rgb, 0, 255).astype(np.uint8); img[:, :, 3] = 255
    f = T['fork_px']
    for x in range(W - f, W):                                            # 燕尾：從中線往兩邊開口
        t = (x - (W - f) + 1) / f
        hw = t * H / 2 * 0.9
        img[int(round(H / 2 - hw)):int(round(H / 2 + hw)), x, 3] = 0
    holes(img, rng, T['holes'], T['hole_r'])
    ragged_end(img, rng, T['tatter_px'])
    return img


def main():
    d = sys.argv[1]
    plan = json.load(open(os.path.join(d, 'plan.json'), encoding='utf-8')); FL = plan['flags']
    w = World(d, with_yards=True); lab, names, YC = w.lab, w.names, w.YC
    td = os.path.join(d, 'textures'); od = os.path.join(d, 'masks', 'flags'); os.makedirs(od, exist_ok=True)
    stamp, anchors, sails, meta, hits, staffs = {}, {}, [], [], {}, {}
    for fname, maker in (('ensign', ensign_png), ('pennant', pennant_png)):
        F = FL[fname]
        P = np.argwhere(lab == w.code(F['on']))
        if F['on'] == 'stern_deco': P = P[P[:, 1] == YC]                  # 拱頂中線那一排
        zt = int(P[:, 2].max()); T = P[P[:, 2] == zt]
        xc, yc = int(np.round(T[:, 0].mean())), int(np.round(T[:, 1].mean()))
        assert yc == YC, (fname, yc)
        assert lab[xc, yc, zt] == w.code(F['on']), (fname, '底下那一格不是', F['on'])
        z0, z1 = zt + 1, zt + F['staff_len']
        cells = {(xc, YC, z): FL['staff_color'] for z in range(z0, z1 + 1)}
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)): cells[(xc + dx, YC + dy, z1 + 1)] = FL['cap_color']
        for c in cells: assert lab[c] == 0, (fname, '旗桿撞到', c, names[lab[c]])
        rows = sorted((k[0], k[1], k[2], v) for k, v in cells.items())
        text = ''.join('%d,%d,%d,%d\n' % x for x in rows)
        open(os.path.join(od, fname + '_staff.vox.txt'), 'w', encoding='utf-8', newline='\n').write(text)
        stamp[fname] = {'name': fname + '-staff', 'work': F['work'], 'op': 'stampvox', 'file': 'masks/flags/%s_staff.vox.txt' % fname, 'at': [0, 0, 0],
                        'voxels': len(rows), 'sha256': hashlib.sha256(text.encode('utf-8')).hexdigest()}
        staffs[fname] = {'x': xc, 'base_z': zt, 'z': [z0, z1 + 1], 'cells': len(rows), 'on': F['on']}
        ztop = z1 - F['top_below_staff_top']; zbot = ztop - F['hoist']
        anchors[fname] = [{'work': F['work'], 'name': '%s-top' % fname, 'at': [xc, YC, ztop], 'kind': 'flag-hoist'},
                          {'work': F['work'], 'name': '%s-bot' % fname, 'at': [xc, YC, zbot], 'kind': 'flag-hoist'}]
        ht, hb = [xc + 0.5, YC + 0.5, ztop + 0.5], [xc + 0.5, YC + 0.5, zbot + 0.5]
        ft, fb = [ht[0] + F['fly'], ht[1], ht[2]], [hb[0] + F['fly'], hb[1], hb[2]]
        img = maker(fname, F, FL['colors'])
        Image.fromarray(img, 'RGBA').save(os.path.join(td, fname + '.png'), optimize=False)
        sails.append({'name': fname, 'corners': ['%s/%s-top' % (F['link'], fname), G(ft), G(fb), '%s/%s-bot' % (F['link'], fname)],
                      'corner_names': ['hoist_top', 'fly_top', 'fly_bottom', 'hoist_bottom'], 'corners_world': [ht, ft, fb, hb],
                      'bind': '3', 'free': 'fly_top,fly_bottom', 'fullness': F['fullness'], 'res': F['res'], 'color': plan['sails']['color'],
                      'texture': 'textures/%s.png' % fname, 'texture_px': list(F['px']),
                      'texture_sha256': hashlib.sha256(open(os.path.join(td, fname + '.png'), 'rb').read()).hexdigest(),
                      'note': {'ensign': '船尾旗（荷蘭三色＋VOC 字母，褪色撕爛）—— 船尾拱頂上的旗桿', 'pennant': '長旗（三色、燕尾）—— 主桅頂的旗桿'}[fname]})
        meta.append(('sail', fname, {'kind': 'flag', 'flag': fname}))
        # 平的旗碰撞（每 0.5 格取樣；離 hoist < 1.2 格的不算）
        h = {}
        A, B, Cc = np.array(ht), np.array(ft), np.array(hb)
        for u in np.linspace(0, 1, 2 * F['fly'] + 1):
            if u * F['fly'] < 1.2: continue
            for v in np.linspace(0, 1, 2 * F['hoist'] + 1):
                c = tuple(int(math.floor(x)) for x in A + u * (B - A) + v * (Cc - A))
                if lab[c]: h[names[lab[c]]] = h.get(names[lab[c]], 0) + 1
        hits[fname] = h
    with open(os.path.join(d, 'flags_meta.tsv'), 'w', encoding='utf-8', newline='\n') as fo:
        fo.write('# 階段十一：旗的 meta（造船規格 §9.1）—— senate cmd sculpture --arg op=work --arg sub=meta --arg file=<這個檔的絕對路徑>\n')
        for part, name, m in meta: fo.write('%s\t%s\t%s\n' % (part, name, json.dumps(m, ensure_ascii=False, sort_keys=True)))
    V = {'stamp': stamp, 'staff': staffs, 'anchors': anchors, 'sails': sails, 'meta': [list(x) for x in meta], 'flat_flag_hits': hits,
         'wind': plan['sails']['wind'], 'seconds': plan['sails']['seconds']}
    with open(os.path.join(d, 'verify_flags.json'), 'w', encoding='utf-8', newline='\n') as fo:
        json.dump(V, fo, ensure_ascii=False, indent=2, sort_keys=True); fo.write('\n')
    print(json.dumps({k: V[k] for k in ('staff', 'anchors', 'flat_flag_hits')}, ensure_ascii=False))
    print({s['name']: s['corners'] for s in sails})


if __name__ == '__main__':
    main()
