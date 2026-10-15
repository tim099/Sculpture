# TASK-0569 驗收第四格：三件放進一間空艙房，跟船體零碰撞（模型的格都不在船體的實心格裡）
#   照遊戲的擺法：模型外框最小角放在艙房地板那一層（z ＝ 艙房 min z，＝ 地板上第一格空氣）、scale 0.5；格 ＝ floor(at ＋ (v ＋ 0.5) × 0.5)。
#   反向對照：病床往船殼那面牆推進去 3 格 ⇒ 要撞到（尺有能力不一致）。
# 用法：python -I room_fit_check.py <組裝件 list> <masks 資料夾> <out json>
import sys, os, json
import numpy as np
sys.stdout.reconfigure(encoding='utf-8')
ship = np.loadtxt(sys.argv[1], delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
S = {(int(x), int(y), int(z)) for x, y, z, c in ship}
M = sys.argv[2]
# 憲法號 berth deck 右舷 7 號艙房：子作品 rooms-berth-side 的 7.min (97,1,1)／7.max (116,28,14)，關聯 甲板-berth/艙房 @173,180,60
ROOM = dict(name='甲板-berth/艙房/7', min=[270, 181, 61], max=[289, 208, 74])
LAYOUT = {'bed': [270, 182, 61], 'table': [271, 191 - 4, 61], 'medkit': [281, 203, 61]}   # table 的子作品 y 往 +y 讓了 8 格 ⇒ at.y 減 4（×0.5）


def cells(item, at):
    v = np.loadtxt(os.path.join(M, item + '.vox.txt'), delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')
    w = np.floor(np.array(at, float) + (v[:, :3] + 0.5) * 0.5).astype(int)
    return {tuple(p) for p in w}


out = {'room': ROOM, 'items': {}}
for it, at in LAYOUT.items():
    c = cells(it, at)
    lo = np.array(list(c)).min(0).tolist()
    hi = np.array(list(c)).max(0).tolist()
    inside = all(ROOM['min'][i] <= lo[i] and hi[i] <= ROOM['max'][i] for i in range(3))
    hit = sorted(p for p in c if p in S)
    out['items'][it] = dict(at=at, cells_01m=len(c), box=[lo, hi], inside_room=inside, hits=len(hit))
    print(it, 'cells', len(c), 'box', lo, hi, 'inside room', inside, 'hits', len(hit))
# 反向對照：病床往 -y 推 3 格（艙房 min y 181 外面是艙壁／船殼）
c = cells('bed', [270, 182 - 3, 61])
neg = sum(1 for p in c if p in S)
out['negative_control'] = dict(item='bed', shift_y=-3, hits=neg)
print('反向對照：病床往牆裡推 3 格 ⇒ hits', neg)
json.dump(out, open(sys.argv[3], 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
