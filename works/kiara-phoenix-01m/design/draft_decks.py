# 炎羽號（kiara-phoenix-01m）新圖紙 04：甲板、艙房與彈藥庫（Phase 4: Decks, Cabins & Magazines）
# 用法：python -I -X utf8 -B draft_decks.py <design 資料夾>

import sys, os, json, math
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draft_lines import Hull, YC, FONT
from draft_hull import build as build_framing

NX, NY, NZ = 576, 181, 100


def build_decks(plan):
    H, solid, d, own_frames, frame_names, frame_layer, aft, dropped = build_framing(plan)
    D = plan['decks']
    F = plan['framing']
    P = plan['planking']

    # 1. 主砲甲板 (Gun Deck): z = 50
    # 內艙範圍: solid 且 d > 1.0 + F['moulded'] + 1.0
    interior_mask = solid & (d > 1.0 + F['moulded'] + 0.8)

    # 桅孔 (Mast holes)
    masts = plan['masts']
    mast_holes = [
        ("fore", masts['fore']['x'], YC, 4.5),
        ("main", masts['main']['x'], YC, 5.0),
        ("mizzen", masts['mizzen']['x'], YC, 3.5),
    ]

    # 艙口 (Hatches)
    hatches = D['hatches']

    gun_deck_voxels = []
    # 主砲甲板板面 (z = 50) 與橫樑 (z = 48, 49)
    for x in range(110, 450):
        # 檢查橫樑位置: 沿 x 每 12 格一根
        is_beam_x = (abs(x - D['beam_x0']) % D['beam_spacing']) < D['beam_sided']
        for y in range(YC - 46, YC + 47):
            if not interior_mask[x, y, 50]: continue

            # 避開桅孔
            in_mast = False
            for m_name, mx, my, mr in mast_holes:
                if (x - mx) ** 2 + (y - my) ** 2 <= mr ** 2:
                    in_mast = True
                    break
            if in_mast: continue

            # 避開艙口
            in_hatch = False
            for h in hatches:
                hx0, hx1 = h['x']
                hdy = h['dy']
                if hx0 <= x <= hx1 and abs(y - YC) <= hdy:
                    in_hatch = True
                    break
            if in_hatch: continue

            # 鋪設甲板面 (z=50, 250 號松木甲板)
            gun_deck_voxels.append((x, y, 50, 250))

            # 鋪設甲板橫樑 (z=48, 49, 136 號橡木樑)
            if is_beam_x:
                gun_deck_voxels.append((x, y, 48, 136))
                gun_deck_voxels.append((x, y, 49, 136))

    # 艙口圍板 (Coamings, 104 號橡木色, 高度 2 格: z=51, 52)
    for h in hatches:
        hx0, hx1 = h['x']
        hdy = h['dy']
        for x in range(hx0 - 1, hx1 + 2):
            for y in range(YC - hdy - 1, YC + hdy + 2):
                is_rim = (x == hx0 - 1 or x == hx1 + 1 or y == YC - hdy - 1 or y == YC + hdy + 1)
                if is_rim and interior_mask[x, y, 50]:
                    gun_deck_voxels.append((x, y, 51, 104))
                    gun_deck_voxels.append((x, y, 52, 104))

    # 船長室地板 (Captain's Cabin Floor, x = 75..110, z = 48)
    for x in range(75, 110):
        for y in range(YC - 38, YC + 39):
            if interior_mask[x, y, 48]:
                gun_deck_voxels.append((x, y, 48, 177))

    # 船長室隔艙壁 (Cabin Bulkhead at x = 110, z = 49..62)
    for y in range(YC - 38, YC + 39):
        for z in range(49, 63):
            # 留兩扇艙門: y 在 YC-12..YC-8 與 YC+8..YC+12 且 z 在 49..58 留空
            door1 = (YC - 12 <= y <= YC - 8) and (49 <= z <= 58)
            door2 = (YC + 8 <= y <= YC + 12) and (49 <= z <= 58)
            if interior_mask[110, y, z] and not door1 and not door2:
                gun_deck_voxels.append((110, y, z, 136))

    # 2. 露天甲板 (Upper Deck: 艏樓 Forecastle, 後甲板 Quarterdeck, 舷側走道 Gangways)
    upper_deck_voxels = []
    for x in range(75, 465):
        # 判斷該 x 處屬於後甲板、走道或艏樓
        is_quarter = (75 <= x <= 215)
        is_forecastle = (380 <= x <= 465)
        is_gangway = (215 < x < 380)

        # 甲板高度隨舷弧 sheer 變化
        sh_z = int(math.floor(H.sheer(x)))
        # 後甲板加高 8 格 (z ≈ 68..76)
        deck_z = sh_z + 8 if is_quarter else sh_z

        for y in range(YC - 46, YC + 47):
            dy = abs(y - YC)
            if not interior_mask[x, y, min(deck_z, 98)]: continue

            # 舷側走道只鋪左右兩側 8 格寬 (dy 在 32..40 之間)
            if is_gangway and not (30 <= dy <= 40):
                continue

            # 避開露天處桅孔
            in_mast = False
            for m_name, mx, my, mr in mast_holes:
                if (x - mx) ** 2 + (y - my) ** 2 <= (mr + 1.0) ** 2:
                    in_mast = True
                    break
            if in_mast: continue

            # 鋪設露天甲板面 (250 號白松木)
            upper_deck_voxels.append((x, y, deck_z, 250))
            # 甲板橫樑
            if (abs(x - D['beam_x0']) % D['beam_spacing']) < D['beam_sided']:
                upper_deck_voxels.append((x, y, deck_z - 1, 136))

    # 以 (x, y, z) 字典去重，確保沒有重複座標
    gun_dict = {}
    for x, y, z, c in gun_deck_voxels:
        gun_dict[(x, y, z)] = c
    gun_deck_voxels = sorted([(x, y, z, gun_dict[(x, y, z)]) for x, y, z in gun_dict.keys()])

    upper_dict = {}
    for x, y, z, c in upper_deck_voxels:
        upper_dict[(x, y, z)] = c
    upper_deck_voxels = sorted([(x, y, z, upper_dict[(x, y, z)]) for x, y, z in upper_dict.keys()])

    return gun_deck_voxels, upper_deck_voxels


def main():
    design_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    plan_path = os.path.join(design_dir, "plan.json")
    with open(plan_path, "r", encoding="utf-8") as f:
        plan = json.load(f)

    gun_deck, upper_deck = build_decks(plan)

    work_dir = os.path.dirname(os.path.abspath(plan_path))
    parent_dir = os.path.dirname(work_dir)
    masks_dir = os.path.join(parent_dir, "masks", "decks")
    os.makedirs(masks_dir, exist_ok=True)

    gun_fn = os.path.join(masks_dir, "deck_gun.vox.txt")
    with open(gun_fn, "w", encoding="utf-8") as f:
        for x, y, z, c in gun_deck:
            f.write(f"{x},{y},{z},{c}\n")

    upper_fn = os.path.join(masks_dir, "deck_upper.vox.txt")
    with open(upper_fn, "w", encoding="utf-8") as f:
        for x, y, z, c in upper_deck:
            f.write(f"{x},{y},{z},{c}\n")

    verify_path = os.path.join(work_dir, "verify_decks.json")
    with open(verify_path, "w", encoding="utf-8") as f:
        json.dump({
            "gun_deck_voxels": len(gun_deck),
            "upper_deck_voxels": len(upper_deck),
            "total_deck_voxels": len(gun_deck) + len(upper_deck)
        }, f, indent=2, ensure_ascii=False)

    print(f"✓ 甲板遮罩生成完畢:")
    print(f"  · 主砲甲板與艙房: {len(gun_deck)} 格 → {gun_fn}")
    print(f"  · 露天甲板(艏樓/後甲板/走道): {len(upper_deck)} 格 → {upper_fn}")
    print(f"✓ 驗證檔已保存: {verify_path}")


if __name__ == "__main__":
    main()
