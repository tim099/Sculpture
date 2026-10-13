# 夜隼號現況重建（設計那一側）：照各階段的 verify_*.json 清單、照落子順序重播成世界座標的色陣列。
# 每一刀都驗：carvevox 那一格現在要是清單上的顏色、stampvox（非 overwrite）那一格原本要是空的 —— 對不上就丟例外（清單跟設計對不上，⛔ 不猜）。
# 用法：from nf_state import state_after; W = state_after(d, 'stage6')   # dict：作品鍵 → (NX, NY, NZ) int16
#   作品鍵：hull、main、quarter、head、stern_deco、gallery_S／_P、rudder、mast_fore、mast_main、bowsprit、channels_S／_P、fife、side_S／_P、fittings_S／_P（一舷＋鏡像的兩舷各一份）。
import os, json
import numpy as np

NX, NY, NZ = 384, 161, 320


def read_list(path):
    return np.loadtxt(path, delimiter=',', dtype=int, comments='#', ndmin=2)


STAGES = [
    ('stage2', 'verify_hull.json', {None: 'hull'}),
    ('stage3', 'verify_planking.json', {None: 'hull'}),
    ('stage4', 'verify_decks.json', {'hull': 'hull', 'main': 'main', 'quarter': 'quarter'}),
    ('stage5', 'verify_stern_head.json', {'hull': 'hull', 'stern_deco': 'stern_deco', 'quarter_gallery': 'gallery', 'head': 'head'}),
    ('stage6', 'verify_rudder_rails.json', {'hull': 'hull', 'quarter_gallery': 'gallery', 'head': 'head', 'rudder': 'rudder'}),
    ('stage7', 'verify_masts.json', {'hull': 'hull', 'mast_fore': 'mast_fore', 'mast_main': 'mast_main', 'bowsprit': 'bowsprit', 'channels': 'channels'}),
    ('stage9', 'verify_rigging.json', {'channels': 'channels'}),       # 階段八（帆桁）是外部模型，不動任何一件的格
    ('stage10', 'verify_belaying.json', {'fiferails': 'fife', 'belaying_side': 'side'}),
    ('stage12', 'verify_flag.json', {'mast_main': 'mast_main'}),          # 階段十一（帆）是布，不動格
    ('stage14', 'verify_gunfittings.json', {'fittings': 'fittings'}),   # 階段十三（砲）是外部模型，不動格；十四 砲具一舷＋鏡像
    ('stage15', 'verify_helm.json', {'hull': 'hull', 'rudder': 'rudder'}),   # gudgeon 從舵搬回船殼；舵改外部模型 ⇒ 之後不算組裝件的格（鍵改名 rudder_model）
    ('stage16', 'verify_steering.json', {'rudder': 'rudder_model', 'quarter': 'quarter', 'hull': 'hull', 'stern_deco': 'stern_deco'}),   # 舵柄（舵模型）、舵柄口、導索塊與繩孔
    ('stage18', 'verify_magazine.json', {'main': 'main', 'magazine': 'magazine'}),   # 階段十七（main staysail）是布，不動格；十八 彈藥庫（關聯 at frame_at）＋艙房地板的 lazarette 艙口
]


def _apply(tgt, o, d, origin=(0, 0, 0), mirror=False):
    a = read_list(os.path.join(d, o['file'])); p = a[:, :3] + np.asarray(origin)
    if mirror: p[:, 1] = 160 - p[:, 1]
    op = o.get('op', 'stampvox')
    if op == 'carvevox':
        if not (tgt[tuple(p.T)] == a[:, 3]).all(): raise ValueError('carve 守門對不上：' + o['file'])
        tgt[tuple(p.T)] = 0
    else:
        if not o.get('overwrite') and (tgt[tuple(p.T)] != 0).any(): raise ValueError('貼的格原本不是空的：' + o['file'])
        tgt[tuple(p.T)] = a[:, 3]


def state_after(d, upto):
    W = {k: np.zeros((NX, NY, NZ), np.int16) for k in ('hull', 'main', 'quarter', 'head', 'stern_deco', 'gallery_S', 'gallery_P', 'rudder',
                                                       'mast_fore', 'mast_main', 'bowsprit', 'channels_S', 'channels_P', 'fife', 'side_S', 'side_P', 'fittings_S', 'fittings_P', 'magazine')}
    for name, fn, keys in STAGES:
        V = json.load(open(os.path.join(d, fn), encoding='utf-8'))['stamp_order']
        groups = [(None, V)] if isinstance(V, list) else list(V.items())
        for sub, L in groups:
            key = keys[sub]
            for o in L:
                org = o.get('origin_world', (0, 0, 0))
                if key in ('gallery', 'channels', 'side', 'fittings'):        # 一舷＋鏡像關聯
                    _apply(W[key + '_S'], o, d, org); _apply(W[key + '_P'], o, d, org, mirror=True)
                else:
                    _apply(W[key], o, d, org)
        if name == 'stage15':
            W['rudder_model'] = W.pop('rudder')     # 舵從此是模型（組裝件 unlink 舵）；occupancy() 不算 *_model
        if name == upto: break
    return W


def occupancy(W):
    occ = np.zeros((NX, NY, NZ), bool)
    for k, v in W.items():
        if not k.endswith('_model'): occ |= v > 0
    return occ
