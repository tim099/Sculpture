# 餘燼號 水線抬高（plan.json waterline_raise；Tim 2026-10-13「船變高了 船底水線是否也要往上一點」）
#   船底的銅（168）就是外板最外面 1–2 格；z 62 以下是銅、63 以上是黑（36）—— 照憲法號 62.86 的水線。
#   抬高：z from..to−1 的「外板黑」換成銅 —— 外板黑 ＝ 貼著船外空氣的 36（每一層 z 的 6 鄰居裡有船外空氣；船外空氣 ＝ 外框外擴 1 格從角落 flood）
#   ＋ 跟它相鄰、同層、也是 36 的那一格（外板 2 格厚的地方）。knee 另外由 draft_head.py 照 head_build.knee_copper_below 重產。
#   ⇒ masks/paint/waterline.vox.txt（stampvox overwrite=1、at 0,0,0）、verify_waterline.json
# 用法：python -I draft_waterline.py <design 資料夾>
import sys, os, json, hashlib, collections
import numpy as np
from scipy import ndimage

D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from draft_ports import export_mark   # noqa: E402


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
    F = plan['waterline_raise']
    a = export_mark(F['hull'], F['world_mark'])
    assert len(a) == F['world_voxels'], ('船殼現況對不上', len(a))
    lo = a[:, :3].min(0) - 1
    shape = tuple(a[:, :3].max(0) - lo + 2)
    S = np.zeros(shape, bool)
    C = np.zeros(shape, np.uint8)
    S[tuple((a[:, :3] - lo).T)] = True
    C[tuple((a[:, :3] - lo).T)] = a[:, 3]
    lab, n = ndimage.label(~S)
    ext = lab == lab[0, 0, 0]
    z0, z1 = F['from_z'], F['to_z']
    black, cop = F['from_color'], F['to_color']
    st6 = ndimage.generate_binary_structure(3, 1)
    near_air = ndimage.binary_dilation(ext, st6) & S
    zs = np.arange(shape[2]) + lo[2]
    band = ((zs >= z0) & (zs < z1))[None, None, :]
    first = near_air & (C == black) & band
    st2 = np.zeros((3, 3, 3), bool)
    st2[1, 1, 1] = st2[0, 1, 1] = st2[2, 1, 1] = st2[1, 0, 1] = st2[1, 2, 1] = True     # 同一層的 4 鄰居
    second = ndimage.binary_dilation(first, st2) & (C == black) & band & ~first
    pick = first | second
    cells = np.argwhere(pick) + lo
    rows = sorted((int(x), int(y), int(z), cop) for x, y, z in cells)
    # 對照：z 62 那一層現在的銅有幾格（新塗的每一層應該差不多）
    per_z = collections.Counter(r[2] for r in rows)
    cop_now = collections.Counter(int(z) for x, y, z, c in a if c == cop and z >= z0 - 3)
    # 鏡像
    keys = {(r[0], r[1], r[2]) for r in rows}
    mir = sum(1 for (x, y, z) in keys if (x, 320 - y, z) not in keys)
    # 換完之後：每一欄 (x, y) 從外面看，z0..z1−1 的外表還剩幾格黑
    after = C.copy()
    after[tuple((cells - lo).T)] = cop
    left_black = int((near_air & (after == black) & band).sum())
    os.makedirs(os.path.join(D, 'masks', 'paint'), exist_ok=True)
    p = os.path.join(D, 'masks', 'paint', 'waterline.vox.txt')
    open(p, 'w', encoding='utf-8', newline='\n').write('# waterline —— 水線抬高：z %d–%d 外板黑 → 銅（stampvox overwrite=1、at 0,0,0；%d 格）\n' % (z0, z1 - 1, len(rows))
                                                     + '\n'.join('%d,%d,%d,%d' % r for r in rows) + '\n')
    v = {'world': int(len(a)), 'cells': len(rows), 'first': int(first.sum()), 'second': int(second.sum()), 'per_z': dict(sorted(per_z.items())),
         'copper_now_per_z': dict(sorted(cop_now.items())), 'mirror_missing': mir, 'surface_black_left_in_band': left_black,
         'x': [min(r[0] for r in rows), max(r[0] for r in rows)],
         'file': {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}}
    json.dump(v, open(os.path.join(D, 'verify_waterline.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(v, ensure_ascii=False))


if __name__ == '__main__':
    main()
