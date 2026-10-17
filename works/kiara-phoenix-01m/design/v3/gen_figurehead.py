# -*- coding: utf-8 -*-
"""炎羽號 v3：船首像《炎羽》—— 一隻往前探身的鳳凰（Tim 2026-10-17「可以試著加船頭像(這是妳的船 加上個人特色吧)」）。
船首像是船的個性裝飾 ⇒ 不用共用元件（造船規格 §2.1）。

量到的（2026-10-17）：艏柱前緣 z 44 → x 462、z 56..80 → x 464；艏斜桅下緣 x 466 z 61、472 z 64、478 z 67、484 z 69、490 z 72；
船頭半寬（z 58）x 460 → 6、452 → 13、440 → 19、428 → 25；水線 z 38；錨爪 fluke-a 在 (445,107,45.5) 貼著船殼；hawse (453,104,68)。
造形（全部在 cell 中心取樣，以 y 90.5 為鏡面，一半算完鏡過去）：
  身體  前傾 25° 的橢球，貼艏柱前緣（橙 236，胸口金 248、腹 240）
  頸、頭 二次貝茲 S 形往前伸，頭在艏斜桅下緣下 2 格以上；金喙 248、深藍眼 2、紅冠 224 金尖 248
  翅膀  往後收、貼著船頭兩舷的浮雕（2 格厚）：內紅 224 → 中橙 236 → 外琥珀 244（不用金黃：船殼金帶 216 會吃掉它），
        斜的暗線當羽根，上緣暗紅 128 勾邊＋一道金，下緣鋸齒當飛羽
  尾焰  翅膀下兩道波浪火焰沿船殼往後到 x 450（避開錨爪），暗紅 160 → 紅 192 → 尖端琥珀 244
用法：python -I -X utf8 gen_figurehead.py | apply
"""
import sys, os, json, math, collections
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "v2"))
from common import ASM, HULL, WORKS, senate, export_list, load, write_vox

TMP = os.path.join(HERE, "_tmp")
FH = "kiara-phoenix-01m-figurehead"
P = "persona=kiara"
CY = 90.5

ORANGE, AMBER, GOLD, YELLOW = 236, 244, 248, 240
RED, RED2, RED3, RED4 = 224, 192, 160, 128
EYE = 2


def bez(p0, p1, p2, t):
    return tuple((1 - t) ** 2 * p0[i] + 2 * (1 - t) * t * p1[i] + t * t * p2[i] for i in range(3))


def seg_dist(p, a, b):
    ab = [b[i] - a[i] for i in range(3)]
    ap = [p[i] - a[i] for i in range(3)]
    L2 = sum(v * v for v in ab) or 1e-9
    t = max(0.0, min(1.0, sum(ap[i] * ab[i] for i in range(3)) / L2))
    q = [a[i] + t * ab[i] for i in range(3)]
    return math.sqrt(sum((p[i] - q[i]) ** 2 for i in range(3))), t


def solid(p):
    """回傳這一點（S 半邊、y ≥ 90.5）的顏色或 None。順序：前面的先贏。"""
    x, y, z = p
    # 眼睛、喙、冠（細的先判）
    d, t = seg_dist(p, (485.2, CY, 59.6), (490.0, CY, 58.4))     # 喙：從 1.35 收到 0.45
    if d <= 1.35 - 0.9 * t:
        return GOLD
    for a, b, r in (((481.5, CY, 62.3), (477.4, CY, 63.2), 0.95),
                    ((481.0, CY + 1.4, 61.9), (475.8, CY + 2.4, 61.6), 0.85),
                    ((481.8, CY + 0.8, 62.6), (478.0, CY + 1.2, 64.4), 0.8)):
        d, t = seg_dist(p, a, b)
        if d <= r:
            return GOLD if t > 0.7 else RED
    # 頭
    hd = math.dist(p, (482.6, CY, 59.6))
    if hd <= 3.05:
        return ORANGE
    # 頸（貝茲曲線上取 16 段，半徑 3.0 → 2.3）
    pts = [bez((472.5, CY, 54.5), (476.5, CY, 59.5), (480.5, CY, 59.6), i / 16) for i in range(17)]
    for i in range(16):
        d, t = seg_dist(p, pts[i], pts[i + 1])
        r = 3.0 - 0.7 * (i + t) / 16
        if d <= r:
            return AMBER if z < pts[i][2] - 1.2 else ORANGE      # 喉下一道琥珀
    # 身體：前傾 25° 的橢球
    a = math.radians(25)
    up = (math.sin(a), 0, math.cos(a)); fw = (math.cos(a), 0, -math.sin(a))
    c = (469.6, CY, 48.2)
    d = (x - c[0], y - c[1], z - c[2])
    du = d[0] * up[0] + d[2] * up[2]; df = d[0] * fw[0] + d[2] * fw[2]
    rf, ry, ru = 5.4, 5.0, 8.6
    if (df / rf) ** 2 + (d[1] / ry) ** 2 + (du / ru) ** 2 <= 1:
        if df > 0.3 * rf and du > -0.35 * ru:
            return GOLD
        if du < -0.35 * ru:
            return YELLOW
        return ORANGE
    return None


def wing_band(x):
    """翅膀在 x 那一欄的 z 範圍（含）；x 從肩 466 往船尾到 428。"""
    t = (466 - x) / 38.0
    if t < 0 or t > 1:
        return None
    zu = 56 + 8 * min(t / 0.68, 1) + (6 * (t - 0.68) / 0.32 if t > 0.68 else 0)   # 上緣：往後升，翼尖翹起
    zl = 47 + 7 * min(t / 0.68, 1) + (9 * (t - 0.68) / 0.32 if t > 0.68 else 0)   # 下緣
    saw = ((466 - x) % 5) / 5.0                                                    # 飛羽鋸齒
    zl = zl - 2.5 * (1 - saw)
    return zl, zu, t


def plume(x, k):
    """尾焰第 k 道在 x 的中心 z；x 從 463 往船尾到 450。"""
    if not (450 <= x <= 463):
        return None
    s = (463 - x) / 13.0
    zc = (45.2 if k == 0 else 41.8) + 1.1 * math.sin((463 - x) / 3.2 + k * 1.7) + (0.8 * s if k == 0 else 0.3 * s)
    half = 1.2 - 0.6 * s
    return zc, half, s


def main():
    apply = len(sys.argv) > 1 and sys.argv[1] == "apply"
    hull = load(os.path.join(TMP, "hull.txt"))
    hocc = set((x, y, z) for x, y, z, c in hull)
    hw = collections.defaultdict(lambda: -1)
    for x, y, z, c in hull:
        if y >= 90 and y > hw[(x, z)]:
            hw[(x, z)] = y
    asm = load(os.path.join(TMP, "asm.txt"))
    occ = {(x, y, z) for x, y, z, c in asm}
    other = occ - hocc                                                 # 船殼以外（艏斜桅、甲板…）

    half = {}
    # 1. 身體、頸、頭、喙、冠
    for x in range(462, 496):
        for y in range(90, 100):
            for z in range(36, 70):
                c = solid((x + 0.5, y + 0.5, z + 0.5))
                if c is not None:
                    half[(x, y, z)] = c
    # 眼：頭的 S 側表面、靠前上方那一格
    eye = max((k for k in half if half[k] == ORANGE and abs(k[0] - 483) <= 0 and k[2] == 60), key=lambda k: k[1])
    half[eye] = EYE
    # 2. 翅膀（浮雕在船殼外 2 格；肩部 x > 464 沒有船殼 ⇒ 從身體側面長出來）
    for x in range(428, 468):
        wb = wing_band(x)
        if not wb:
            continue
        zl, zu, t = wb
        base = RED if t < 0.32 else (ORANGE if t < 0.66 else AMBER)       # 船殼的金帶是 216 ⇒ 翅膀外段不用金黃，免得融進去
        dark = {RED: RED3, ORANGE: RED2, AMBER: RED}[base]
        for z in range(int(math.floor(zl)), int(math.ceil(zu)) + 1):
            if not (zl <= z + 0.5 <= zu + 0.5):
                continue
            h = hw[(x, z)]
            if x > 464:
                ys = (94, 95, 96)
            elif h < 0:
                continue
            else:
                ys = (h + 1, h + 2)
            col = dark if ((466 - x) + (z - int(zl))) % 5 == 0 and x < 464 else base   # 斜的羽根線
            if z + 0.5 >= zu - 0.5:                        # 上緣一道暗紅勾邊（跟船殼分開）
                col = RED4
            elif z + 0.5 >= zu - 1.5:
                col = GOLD
            for y in ys:
                half.setdefault((x, y, z), col)
    # 3. 尾焰兩道
    for x in range(450, 464):
        for k in (0, 1):
            pz = plume(x, k)
            if not pz:
                continue
            zc, hh, s = pz
            col = RED3 if s < 0.35 else (RED2 if s < 0.75 else AMBER)
            for z in range(int(zc - hh - 1), int(zc + hh + 2)):
                if abs(z + 0.5 - zc) > hh + 0.25:
                    continue
                h = hw[(x, z)]
                if h < 0:
                    continue
                for y in (h + 1, h + 2):
                    half.setdefault((x, y, z), col)
    # 鏡過去
    cells = dict(half)
    for (x, y, z), c in half.items():
        cells[(x, 180 - y, z)] = c
    # 量：不准蓋到任何既有的格；離船殼以外的部件（艏斜桅…）至少 1 格
    clash = [k for k in cells if k in occ]
    near = [k for k in cells if any((k[0] + dx, k[1] + dy, k[2] + dz) in other
                                     for dx in (-1, 0, 1) for dy in (-1, 0, 1) for dz in (-1, 0, 1))]
    touch = sum(1 for k in cells if any((k[0] + d[0], k[1] + d[1], k[2] + d[2]) in hocc
                                        for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))))
    xs = [k[0] for k in cells]; ys = [k[1] for k in cells]; zs = [k[2] for k in cells]
    lo = (min(xs), min(ys), min(zs)); hi = (max(xs), max(ys), max(zs))
    size = tuple(hi[i] - lo[i] + 1 for i in range(3))
    print(f"船首像 {len(cells)} 格；外框 {lo}..{hi}（{size}）；碰撞 {len(clash)}；離艏斜桅等 ≤1 格 {len(near)}；貼船殼 {touch} 格")
    print("  顏色", collections.Counter(cells.values()).most_common(), "眼", eye)
    if clash or near:
        print("  ", clash[:6], near[:6])
    if not apply:
        f = write_vox(os.path.join(TMP, "figurehead_preview.txt"), [(*k, c) for k, c in sorted(cells.items())])
        return
    if clash or near:
        raise SystemExit("✗ 有碰撞 ⇒ 不套用")
    if not os.path.exists(os.path.join(WORKS, FH)):
        senate("op=work", "sub=create", f"id={FH}", P, "account=Myth", f"parent_work={HULL}",
               "title=炎羽號 船首像《炎羽》", f"size={size[0]},{size[1]},{size[2]}", "tags=sub")
    senate("op=work", "sub=update", f"work={FH}", P, f"size={size[0]},{size[1]},{size[2]}", "meters_per_voxel=0.1", "tags=sub")
    want = {(x - lo[0], y - lo[1], z - lo[2]): c for (x, y, z), c in cells.items()}
    now = {(x, y, z): c for x, y, z, c in export_list(FH, os.path.join(TMP, "fh_now.txt"))}
    if now != want:
        if now:
            write_vox(os.path.join(TMP, "fh_carve.txt"), [(*k, v) for k, v in sorted(now.items())])
            senate("op=carvevox", f"work={FH}", P, "at=0,0,0", f"voxels={os.path.join(TMP, 'fh_carve.txt')}",
                   f"expect_pixels={len(now)}", "share=0")
        write_vox(os.path.join(TMP, "fh_stamp.txt"), [(*k, v) for k, v in sorted(want.items())])
        senate("op=stampvox", f"work={FH}", P, "at=0,0,0", f"voxels={os.path.join(TMP, 'fh_stamp.txt')}",
               f"expect_pixels={len(want)}", "share=0")
    links = {l["name"]: l for l in json.load(open(os.path.join(WORKS, ASM, "links.json"), encoding="utf-8"))["links"]}
    if "船首像" not in links:
        senate("op=work", "sub=link", f"work={ASM}", P, "name=船首像", f"source_work={FH}", f"at={lo[0]},{lo[1]},{lo[2]}",
               "note=v3：船首像《炎羽》（鳳凰；design/v3/gen_figurehead.py）")
    print("done")


if __name__ == "__main__":
    main()
