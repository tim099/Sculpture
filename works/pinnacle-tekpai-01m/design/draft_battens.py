# 台灣帆竹筏 tekpai —— 硬骨帆的實體竹篾桿（TASK-1320；Tim 2026-11-18「讓硬骨類似帆桁(有實體 帆會有一段黏在上面)」「用妳的台灣帆竹筏來做」）
#   一件竹篾元件 pinnacle-tekpai-01m-batten（5×45×5、0.1 m；一格粗的竹子、竹節、y 2..42 ＝ 4.1 m），
#   在主桅子作品掛 4 根外部模型（meta kind=yard、yard=batten、batten=m（從上往下數）、sail=main）——
#   位置照帆的配方：帆角 ＝ 上帆桁 earing（±18 格）、下帆桁 earing（±19 格），竹篾 m 在 v ＝ m／5 那一列
#   ⇒ 轉軸 z ＝ 68.5 − 44 × m／5、跟兩根帆桁同一條桅軸（84, 50.5）、同樣轉 −18°；桿的中心線正好壓在那一列布上。
#   用法：python -I -X utf8 draft_battens.py            （只寫清單、印讀數）
#         python -I -X utf8 draft_battens.py --apply    （建元件、落格、固定點、掛 4 根模型）
import json, os, subprocess, sys, hashlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'masks_masts')
HULL = 'pinnacle-tekpai-01m'
WORK = HULL + '-batten'
HOST = HULL + '-mast-main'
N = 4                                   # 帆的 meta battens（rig_meta.tsv：main battens 4）
Z_TOP, Z_FOOT = 68.5, 24.5              # 上帆桁、下帆桁的轉軸高度（draft_masts.py yards_cfg）
HALF_TOP, HALF_FOOT = 18, 19            # 帆角離轉軸幾格（上帆桁 earing 4／40、下帆桁 3／41，轉軸 22）
Y0, Y1 = 2, 42                          # 桿長 4.1 m：最寬那一列半寬 18.8 ⇒ 兩頭各伸出帆邊 1.2 格以上


def build():
    B = np.zeros((5, 45, 5), dtype=np.uint8)
    for y in range(Y0, Y1 + 1):
        B[2, y, 2] = 104 if y in (Y0, Y1, 10, 22, 34) else 177      # 竹（177）＋竹節（104，同帆桁的配色）
    anchors = [('pivot', '2,22,2'), ('arm-P', '2,%d,2' % Y0), ('arm-S', '2,%d,2' % Y1)]
    return B, anchors


def write(arr, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    xs, ys, zs = np.nonzero(arr)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# tekpai batten voxels (x,y,z,color) —— draft_battens.py\n')
        for x, y, z in zip(xs, ys, zs):
            f.write('%d,%d,%d,%d\n' % (x, y, z, arr[x, y, z]))
    return len(xs), hashlib.sha256(open(path, 'rb').read()).hexdigest()


def cli(args):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8')
    if r.returncode != 0:
        raise SystemExit('✗ %s\n%s%s' % (' '.join(args), r.stdout[-1500:], r.stderr[-800:]))
    return r.stdout


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    B, anchors = build()
    path = os.path.join(OUT, 'batten.vox.txt')
    n, sha = write(B, path)
    rows = []
    for m in range(1, N + 1):
        v = m / (N + 1.0)
        z = Z_TOP + (Z_FOOT - Z_TOP) * v
        half = HALF_TOP + (HALF_FOOT - HALF_TOP) * v
        rows.append({'name': 'batten-%d' % m, 'batten': m, 'at': [84.0, 50.5, round(z, 3)], 'row_half': round(half, 3),
                     'overhang': [round(22 - Y0 - half, 3), round(Y1 - 22 - half, 3)]})
    print(json.dumps({'voxels': n, 'sha256': sha, 'anchors': anchors, 'rows': rows}, ensure_ascii=False, indent=1))
    if '--apply' not in sys.argv:
        return
    cli(['op=work', 'sub=create', 'persona=pinnacle', 'work=' + WORK, 'title=台灣帆竹筏 竹篾桿（硬骨帆的實體竹篾；一格粗、4.1 m、0.1 m）',
         'parent_work=' + HULL, 'size=5,45,5', 'tags=sub'])
    cli(['op=work', 'sub=update', 'persona=pinnacle', 'work=' + WORK, 'meters_per_voxel=0.1'])
    out = cli(['op=stampvox', 'persona=pinnacle', 'work=' + WORK, 'voxels=' + path.replace('\\', '/'), 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0'])
    print('✓ stampvox', WORK, n)
    for an, at in anchors:
        cli(['op=work', 'sub=anchor', 'persona=pinnacle', 'work=' + WORK, 'name=' + an, 'at=' + at, 'note=draft_battens.py（TASK-1320）'])
    print('✓ anchors', len(anchors))
    for r in rows:
        meta = {'kind': 'yard', 'mast': 'main', 'yard': 'batten', 'batten': r['batten'], 'sail': 'main', 'length_ft': 13.5, 'diameter_in': 4,
                'pivot_anchor': 'pivot', 'turn_axis': 'z', 'rotate_z_deg': -18}
        cli(['op=work', 'sub=model', 'persona=pinnacle', 'work=' + HOST, 'name=' + r['name'], 'source_work=' + WORK,
             'pivot=2.5,22.5,2.5', 'at=%g,%g,%g' % tuple(r['at']), 'rotate=0,0,-18', 'scale=1',
             'meta=' + json.dumps(meta, ensure_ascii=False, separators=(',', ':')), 'note=硬骨帆竹篾 %d（TASK-1320）' % r['batten']])
        print('✓ model', r['name'], r['at'])


if __name__ == '__main__':
    main()
