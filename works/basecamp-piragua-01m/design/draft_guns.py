# 杉心號 步驟 9（TASK-1152）：船頭一門迴旋砲（共用件 apex-one-reale-01m-gun-pierrier＋拆好的座 -mount）＋砲柱 ⇒
#   masks/deck/gun_post.vox.txt、guns_placement.json、guns_meta.tsv、verify_guns.json
#   用法：python -I -X utf8 draft_guns.py [--probe=dz=-4]   （probe ⇒ 整門上下移，量碰撞；⛔ 不寫檔）
#   · 迴旋砲的座標（Ship_Guns §4.1）：y ＝ 砲口方向、z 0 ＝ 叉架底；0.05 m ⇒ scale 0.5 是原尺寸（拉貝爾號那批 0.39 是縮過的）。
#   · 船頭要朝前開 ⇒ rotate 0,0,−90（+y → +x）；叉架底擱在船頭平台上的砲柱頂（plan.json guns.post）。
#   · 零碰撞（Ship_Guns §4.2）：模型每一格的格心＋八個角都不在組裝件的實心裡（船殼、甲板-main、砲柱、桅）；砲口在船殼外（線形實心外）。
#   · 共用件拆過座 ⇒ 自己補雙生 `<名>座`（kind=gunmount、mount_of ＝ 砲的 id；Ship_Guns §4.2.1）。
import sys, os, json, math, subprocess, tempfile
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lines as HL

sys.stdout.reconfigure(encoding='utf-8')
SX, SY, SZ = 140, 101, 100
GUN, MOUNT = 'apex-one-reale-01m-gun-pierrier', 'apex-one-reale-01m-gun-pierrier-mount'


def V(d):
    return d['v'] if isinstance(d, dict) and 'v' in d else d


def load_list(f):
    return np.loadtxt(f, delimiter=',', comments='#', dtype=np.int32, ndmin=2, encoding='utf-8')


def export(work):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'w.txt').replace('\\', '/')
        r = subprocess.run(['senate', 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=' + work, '--arg', 'out=' + out],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode or not os.path.exists(out):
            raise SystemExit('匯出失敗 ' + work + (r.stdout + r.stderr)[-500:])
        return load_list(out)


def anchors(work):
    p = os.path.join(HERE, '..', '..', work, 'anchors.json')
    return {a['name']: a['at'] for a in json.load(open(p, encoding='utf-8'))['anchors']}


def solids(plan, post):
    occ = np.zeros((SX, SY, SZ), bool)
    for f in (('hull', 'hull'), ('deck', 'deck_main'), ('masts', 'mast')):
        a = load_list(os.path.join(HERE, 'masks', f[0], f[1] + '.vox.txt'))
        occ[a[:, 0], a[:, 1], a[:, 2]] = True
    hole = load_list(os.path.join(HERE, 'masks', 'masts', 'thwart_hole.vox.txt'))
    for x, y, z, c in hole:
        occ[x, y, z] = True                                     # 桅孔刻掉的那格現在是桅（mast.vox 已含）
    for k in post:
        occ[k] = True
    return occ


def place(pts, at, pivot, scale, rot_deg):
    """模型格（來源座標）⇒ 船上的點：先減 pivot、縮放、繞 z 轉、再加 at。"""
    t = math.radians(rot_deg)
    c, s = math.cos(t), math.sin(t)
    q = (pts - np.array(pivot)) * scale
    return np.stack([q[:, 0] * c - q[:, 1] * s, q[:, 0] * s + q[:, 1] * c, q[:, 2]], axis=1) + np.array(at)


def main():
    probe = {}
    for a in sys.argv[1:]:
        if a.startswith('--probe='):
            k, v = a[len('--probe='):].split('=')
            probe[k] = float(v)
    plan = HL.load_plan(HERE)
    L = HL.Lines(plan)
    G = V(plan['guns'])
    YC = plan['space']['yc']
    px, pz0, pz1 = G['post']['x'], G['post']['z0'], G['post']['z1']
    post = [(px, YC, z) for z in range(pz0, pz1 + 1)]
    occ = solids(plan, post)
    A = anchors(GUN)
    pivot = [A['pivot'][0] + 0.5, A['pivot'][1] + 0.5, 0.0]
    at = [px + 0.5, YC + 0.5, pz1 + 1 + probe.get('dz', 0)]
    hits, pts_all = {}, {}
    for w in (GUN, MOUNT):
        cells = export(w)[:, :3].astype(float)
        n = 0
        for off in [(0.5, 0.5, 0.5)] + [(dx, dy, dz) for dx in (0, 1) for dy in (0, 1) for dz in (0, 1)]:
            p = place(cells + np.array(off), at, pivot, G['scale'], G['rotate_z'])
            k = np.floor(p).astype(int)
            ok = (k[:, 0] >= 0) & (k[:, 0] < SX) & (k[:, 1] >= 0) & (k[:, 1] < SY) & (k[:, 2] >= 0) & (k[:, 2] < SZ)
            n += int(occ[k[ok, 0], k[ok, 1], k[ok, 2]].sum())
        hits[w] = n
        pts_all[w] = place(cells + 0.5, at, pivot, G['scale'], G['rotate_z'])
    mz = place(np.array([[A['muzzle'][0] + 0.5, A['muzzle'][1] + 0.5, A['muzzle'][2] + 0.5]]), at, pivot, G['scale'], G['rotate_z'])[0]
    br = place(np.array([[A['breech'][0] + 0.5, A['breech'][1] + 0.5, A['breech'][2] + 0.5]]), at, pivot, G['scale'], G['rotate_z'])[0]
    muzzle_in_hull = bool(L.hb(mz[0], mz[2]) >= abs(mz[1] - (YC + 0.5)))
    R = {'at': at, 'muzzle': [round(float(v), 2) for v in mz], 'breech': [round(float(v), 2) for v in br],
         'axis': [round(float(v), 3) for v in (mz - br) / np.linalg.norm(mz - br)], 'hits': hits, 'muzzle_inside_hull_lines': muzzle_in_hull,
         'bore_above_stand_m': round(float(mz[2] - V(plan['layout']['thwarts'])['top_z']) * 0.1, 2),
         'bore_above_bow_gunwale_m': round(float(mz[2] - L.zs(mz[0])) * 0.1, 2), 'post_cells': len(post)}
    if probe:
        print(json.dumps({'probe': probe, 'hits': hits, 'muzzle_inside_hull_lines': muzzle_in_hull}, ensure_ascii=False))
        return
    col = G['post']['color']
    with open(os.path.join(HERE, 'masks', 'deck', 'gun_post.vox.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('# 杉心號 迴旋砲的砲柱（draft_guns.py）x,y,z,color —— 落在甲板-main，at 0,0,0\n')
        f.write(''.join('%d,%d,%d,%d\n' % (x, y, z, col) for x, y, z in post))
    meta_g = {'kind': 'gun', 'gun': 'pierrier', 'deck': 'main', 'id': 'gun-1', 'mount': 'turret', 'arc': G['arc'], 'rate': 45, 'port': 'bow'}
    meta_m = {'kind': 'gunmount', 'id': 'gunmount-1', 'mount_of': 'gun-1'}
    pl = [{'name': '迴旋砲-F01', 'work': GUN, 'at': at, 'pivot': pivot, 'scale': G['scale'], 'rotate': [0, 0, G['rotate_z']], 'meta': meta_g},
          {'name': '迴旋砲-F01座', 'work': MOUNT, 'at': at, 'pivot': pivot, 'scale': G['scale'], 'rotate': [0, 0, G['rotate_z']], 'meta': meta_m}]
    with open(os.path.join(HERE, 'guns_placement.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump({'host': 'basecamp-piragua-01m-deck-main', 'models': pl}, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE, 'guns_meta.tsv'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(''.join('model\t%s\t%s\n' % (m['name'], json.dumps(m['meta'], ensure_ascii=False)) for m in pl))
    with open(os.path.join(HERE, 'verify_guns.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(R, f, ensure_ascii=False, indent=1)
    print(json.dumps(R, ensure_ascii=False))


if __name__ == '__main__':
    main()
