# 步驟 6 裝飾子作品與模型配置（kiara-tunis-sandal-01m-bitt / fender / stem-orn / stern-orn）：
#   - 全部裝飾以外部模型 (work sub=model) 掛入組裝件並標 meta {"deco": 1}
#   - 嚴格避開船殼、甲板、貨艙區 (x=46..78, z>=2)、桅孔及艉中線舵葉通道 (x<=18, y=49..51)
#   用法：python -I -X utf8 draft_deco.py [--probe=shift_y=-1]
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SX, SY, SZ = 136, 101, 30
YC = 50


def rgb(i):
    return ((i >> 5 & 7) * 255 // 7, (i >> 2 & 7) * 255 // 7, (i & 3) * 255 // 3)


def font(sz):
    for f in ('C:/Windows/Fonts/msjh.ttc', 'C:/Windows/Fonts/msyh.ttc', 'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(f):
            return ImageFont.truetype(f, sz)
    return ImageFont.load_default()


def load_vox(path, shape=(SX, SY, SZ)):
    a = np.loadtxt(path, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    G = np.zeros(shape, np.uint8)
    if len(a):
        G[a[:, 0], a[:, 1], a[:, 2]] = a[:, 3]
    return G


def build_models():
    models = {}

    # 1. 繫纜柱 bitt (3, 5, 4), pivot=(1.5, 2.5, 0.0)
    B = np.zeros((3, 5, 4), np.uint8)
    B[1, 2, 0:3] = 68     # 深木主柱
    B[1, 1:4, 2] = 136    # 橫繫纜木角（y 1..3）
    B[1, 2, 3] = 208      # 赭黃柱帽
    models['bitt'] = {'vox': B, 'pivot': [1.5, 2.5, 0.0]}

    # 2. 護舷靠墊 fender (5, 3, 5), pivot=(2.5, 1.5, 0.0)
    F = np.zeros((5, 3, 5), np.uint8)
    F[1:4, 1, 1:4] = 177  # 麻繩編織墊體
    F[1:4, 1, 2] = 136    # 中腰箍
    F[2, 1, 4] = 68       # 繫舷吊繩扣
    models['fender'] = {'vox': F, 'pivot': [2.5, 1.5, 0.0]}

    # 3. 艏柱飾 stem-orn (5, 3, 6), pivot=(0.5, 1.5, 2.0) -> (0,1,2) 落於 pivot 格
    S = np.zeros((5, 3, 6), np.uint8)
    S[0, 1, 2] = 68       # 緊接艏柱頂底環
    S[0, 1, 3] = 160      # 突尼斯朱紅飾節
    S[0, 1, 4] = 208      # 鎏金赭黃艏角基底
    S[1, 1, 4] = 208      # 前伸角尖
    S[1, 1, 5] = 208
    models['stem-orn'] = {'vox': S, 'pivot': [0.5, 1.5, 2.0]}

    # 4. 艉鏡側飾 stern-orn (3, 9, 5), pivot=(1.5, 4.5, 0.0) -> 僅留兩側 y 避開中央舵位
    T = np.zeros((3, 9, 5), np.uint8)
    for y in (0, 1, 2, 6, 7, 8):
        T[1, y, 1:4] = 68
    for y in (1, 7):
        T[1, y, 2] = 208  # 兩側徽章金點
    T[1, 0, 2] = 160
    T[1, 8, 2] = 160
    models['stern-orn'] = {'vox': T, 'pivot': [1.5, 4.5, 0.0]}

    return models


def mount_specs(probe):
    dy = int(probe.get('shift_y', 0))
    return [
        {'name': '繫纜柱-艏',   'model': 'bitt',      'work': 'kiara-tunis-sandal-01m-bitt',      'at': [97.5, 50.5, 5.0]},
        {'name': '繫纜柱-艉P',  'model': 'bitt',      'work': 'kiara-tunis-sandal-01m-bitt',      'at': [23.5, 47.5, 5.0]},
        {'name': '繫纜柱-艉S',  'model': 'bitt',      'work': 'kiara-tunis-sandal-01m-bitt',      'at': [23.5, 53.5, 5.0]},
        {'name': '護舷-P1',     'model': 'fender',    'work': 'kiara-tunis-sandal-01m-fender',    'at': [52.5, 37.5 - dy, 4.0]},
        {'name': '護舷-S1',     'model': 'fender',    'work': 'kiara-tunis-sandal-01m-fender',    'at': [52.5, 63.5 + dy, 4.0]},
        {'name': '護舷-P2',     'model': 'fender',    'work': 'kiara-tunis-sandal-01m-fender',    'at': [68.5, 36.5 - dy, 4.0]},
        {'name': '護舷-S2',     'model': 'fender',    'work': 'kiara-tunis-sandal-01m-fender',    'at': [68.5, 64.5 + dy, 4.0]},
        {'name': '艏飾',        'model': 'stem-orn',  'work': 'kiara-tunis-sandal-01m-stem-orn',  'at': [113.5, 50.5, 14.0]},
        {'name': '艉飾',        'model': 'stern-orn', 'work': 'kiara-tunis-sandal-01m-stern-orn', 'at': [18.5, 50.5, 5.0]},
    ]


def place_to_world(G, pivot, at):
    dx = int(round(at[0] - pivot[0]))
    dy = int(round(at[1] - pivot[1]))
    dz = int(round(at[2] - pivot[2]))
    pts = np.argwhere(G > 0)
    return [(int(x + dx), int(y + dy), int(z + dz), int(G[x, y, z])) for x, y, z in pts]


def main():
    probe = {}
    for s in sys.argv[1:]:
        if s.startswith('--probe='):
            k, v = s[len('--probe='):].split('=')
            probe[k] = float(v)

    H = load_vox(os.path.join(HERE, 'masks', 'hull', 'hull.vox.txt'))
    D = load_vox(os.path.join(HERE, 'masks', 'deck', 'deck_main.vox.txt'))
    occ = (H > 0) | (D > 0)

    models = build_models()
    specs = mount_specs(probe)

    W_deco = np.zeros((SX, SY, SZ), np.uint8)
    per_model = []
    overlap_ship = 0
    overlap_self = 0
    rudder_blocked = 0
    attached_adj = []

    for sp in specs:
        m = models[sp['model']]
        wpts = place_to_world(m['vox'], m['pivot'], sp['at'])
        hits = 0
        self_hits = 0
        r_hits = 0
        adj = False
        for wx, wy, wz, wc in wpts:
            if not (0 <= wx < SX and 0 <= wy < SY and 0 <= wz < SZ):
                continue
            if occ[wx, wy, wz]:
                hits += 1
            if W_deco[wx, wy, wz] > 0:
                self_hits += 1
            if wx <= 18 and 49 <= wy <= 51 and wz <= 12:
                r_hits += 1
            for ddx, ddy, ddz in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
                nx, ny, nz = wx + ddx, wy + ddy, wz + ddz
                if 0 <= nx < SX and 0 <= ny < SY and 0 <= nz < SZ and occ[nx, ny, nz]:
                    adj = True
            W_deco[wx, wy, wz] = wc
        overlap_ship += hits
        overlap_self += self_hits
        rudder_blocked += r_hits
        attached_adj.append(adj)
        per_model.append({'name': sp['name'], 'cells': len(wpts), 'overlap': hits, 'adjacent': adj})

    R = {
        'model_count': len(specs),
        'total_deco_cells': int((W_deco > 0).sum()),
        'overlap_ship': int(overlap_ship),
        'overlap_self': int(overlap_self),
        'rudder_zone_blocked': int(rudder_blocked),
        'all_attached': all(attached_adj),
        'mirror_diff': int(((W_deco > 0) != (W_deco > 0)[:, ::-1, :]).sum()),
        'mirror_color_diff': int((W_deco != W_deco[:, ::-1, :]).sum()),
        'models': per_model,
    }

    if probe:
        print(json.dumps({'probe': probe, **{k: R[k] for k in ('total_deco_cells', 'overlap_ship', 'all_attached', 'mirror_diff')}}, ensure_ascii=False))
        return

    out_dir = os.path.join(HERE, 'masks', 'deco')
    os.makedirs(out_dir, exist_ok=True)
    for mname, m in models.items():
        pts = np.argwhere(m['vox'] > 0)
        with open(os.path.join(out_dir, f'{mname}.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
            f.write(f'# 突尼斯湖轉運艇 Sandal 裝飾件 {mname}（draft_deco.py）x,y,z,color\n')
            for x, y, z in pts:
                f.write(f'{x},{y},{z},{m["vox"][x, y, z]}\n')

    # 模型 META (deco=1) 清單
    with open(os.path.join(HERE, 'deco_models.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(
            [
                {
                    'name': sp['name'],
                    'work': sp['work'],
                    'at': sp['at'],
                    'pivot': models[sp['model']]['pivot'],
                    'meta': {'deco': 1},
                }
                for sp in specs
            ],
            f,
            indent=2,
            ensure_ascii=False,
        )

    with open(os.path.join(HERE, 'verify_deco.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, indent=1, ensure_ascii=False)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
