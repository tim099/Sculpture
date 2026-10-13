# 餘燼號 階段十五 舵（plan.json rudder_build）—— 憲法號 -rudder 的位置照抄（z 2–84 全在插層 z 109 以下、船尾不在拉長那一段 ⇒ 換算是恆等）
#   但水線抬到 71 ⇒ 不直接關聯（憲法號那件 z 63–70 是黑）：新子作品 assemble 憲法號的舵，再把 z 63–70 的黑（36）換成銅（168）；pintle 帶（136）不動。
#   ⇒ masks/rudder/waterline.vox.txt（stampvox overwrite、at 0,0,0）、verify_rudder.json
# 用法：python -I draft_rudder.py <design 資料夾>
import sys, os, json, hashlib, collections

D = os.path.abspath(sys.argv[1])
sys.path.insert(0, D)
from draft_ladders import existing_links, export_hidden   # noqa: E402


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    P = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))['rudder_build']
    r = export_hidden(P['source'], [])
    assert len(r) == P['source_voxels'], ('憲法號的舵對不上', len(r))
    a = export_hidden(P['assembly'], [P['link']] if P['link'] in set(existing_links(P['assembly'])) else [])   # 藏起本階段的關聯（套用後重跑才一樣）
    A = {(int(x), int(y), int(z)) for x, y, z, c in a if x < 160 and z < 90}
    ov = sum(1 for x, y, z, c in r if (int(x), int(y), int(z)) in A)
    rows = sorted((int(x), int(y), int(z), P['to_color']) for x, y, z, c in r if P['z'][0] <= z <= P['z'][1] and c == P['from_color'])
    p = os.path.join(D, 'masks', 'rudder', 'waterline.vox.txt')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8', newline='\n').write('# rudder waterline —— 舵 z %d–%d 黑 → 銅（stampvox overwrite、at 0,0,0；%d 格）\n' % (P['z'][0], P['z'][1], len(rows))
                                                     + '\n'.join('%d,%d,%d,%d' % t for t in rows) + '\n')
    keys = {t[:3] for t in rows}
    v = {'source_voxels': int(len(r)), 'overlap_with_assembly': ov, 'recolor': len(rows),
         'z_band_colors_before': dict(collections.Counter(int(c) for x, y, z, c in r if P['z'][0] <= z <= P['z'][1])),
         'mirror_missing': sum(1 for (x, y, z) in keys if (x, 320 - y, z) not in keys),
         'expect_assembly_after': int(len(a)) + int(len(r)),
         'file': {'cells': len(rows), 'sha256': hashlib.sha256(open(p, 'rb').read()).hexdigest()}}
    json.dump(v, open(os.path.join(D, 'verify_rudder.json'), 'w', encoding='utf-8', newline='\n'), ensure_ascii=False, indent=1)
    print(json.dumps(v, ensure_ascii=False))


if __name__ == '__main__':
    main()
