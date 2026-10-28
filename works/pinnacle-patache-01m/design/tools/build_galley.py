# 直接出處：apex-two-galeon-01m/design/tools/build_galley.py（康塞普西翁號，TASK-0969）—— 作品 id、persona、尺寸、單號、船名換成聖羅曼號（TASK-0970）；下面那行是康塞普西翁號那時寫的出處
# 直接出處：gura-pinas-01m/design/tools/build_galley.py（藍鯊號，TASK-0967）—— 作品 id、persona、尺寸、單號、船名換成聖羅曼號（TASK-0970）；下面那行是藍鯊號那時寫的出處
# 聖羅曼號 廚房爐灶落格（TASK-0970）：子作品 -galley（0.05 m，貼 masks/galley/galley.vox.txt）、掛成上甲板子作品的外部模型（kind=galley）、
#   船艏樓甲板開煙囪洞（carvevox 帶現在的顏色守門）。
#   用法：python -I -X utf8 tools/build_galley.py <design>
#   · 子作品已存在 ⇒ 不重建、不重貼；模型 overwrite=1；洞已經刻過 ⇒ 跳過（讀回格子數）
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'pinnacle-patache-01m'
WORKS = os.path.dirname(os.path.dirname(os.path.abspath(design)))
PL = json.load(open(os.path.join(design, 'galley_placement.json'), encoding='utf-8'))
sys.path.insert(0, os.path.join(design, 'tools'))
from wio import export_list


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        raise SystemExit('✗ %s：%s' % (' '.join(args[:4]), out[-600:]))
    return out


w = PL['work']
path = os.path.abspath(os.path.join(design, 'masks', 'galley', 'galley.vox.txt')).replace('\\', '/')
n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
if not os.path.exists(os.path.join(WORKS, w, 'work.json')):
    cli('op=work', 'sub=create', 'persona=pinnacle', 'work=' + w, 'title=聖羅曼號 陳設・廚房爐灶（kombuis：鉛盤上砌黃磚、鐵板上一口銅鍋、磚煙囪穿過船艏樓甲板；0.05 m，外部模型的來源，kind=galley）',
        'parent_work=' + HULL, 'size=%d,%d,%d' % tuple(PL['size']), 'tags=sub')
    cli('op=work', 'sub=update', 'persona=pinnacle', 'work=' + w, 'meters_per_voxel=0.05')
    out = cli('op=stampvox', 'persona=pinnacle', 'work=' + w, 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    if not m or int(m.group(1).replace(',', '')) != n:
        raise SystemExit('✗ placed ≠ %d：%s' % (n, out[-800:]))
    print('✓ 建立 %s（%d 格）' % (w, n), flush=True)
xyz = lambda v: ','.join('%g' % c for c in v)
cli('op=work', 'sub=model', 'persona=pinnacle', 'work=' + PL['deck_work'], 'name=' + PL['name'], 'source_work=' + w, 'at=' + xyz(PL['at']), 'pivot=' + xyz(PL['pivot']),
    'rotate=0,0,0', 'scale=' + xyz([PL['scale']] * 3), 'overwrite=1', 'meta=' + json.dumps(PL['meta'], ensure_ascii=False, separators=(',', ':')),
    'note=步驟 10 廚房（TASK-0970；draft_galley.py）：爐口朝船尾、廚師站船尾那一面')
print('✓ 模型 %s/%s' % (PL['deck_work'], PL['name']), flush=True)
hole = os.path.abspath(os.path.join(design, 'masks', 'galley', 'deck_hole.vox.txt')).replace('\\', '/')
H = [tuple(map(int, l.split(','))) for l in open(hole, encoding='utf-8') if l.strip() and not l.startswith('#')]
D = {tuple(r[:3]) for r in export_list('pinnacle-patache-01m-deck-castillo', None).tolist()}
left = [h for h in H if h[:3] in D]
if left:
    out = cli('op=carvevox', 'persona=pinnacle', 'work=pinnacle-patache-01m-deck-castillo', 'voxels=' + hole, 'at=0,0,0', 'expect_pixels=%d' % len(H), 'share=0')
    print('✓ 船艏樓甲板刻煙囪洞 %d 格：%s' % (len(left), out.strip().splitlines()[-1][:200]))
else:
    print('· 煙囪洞已經刻過（%d 格都不在甲板上）' % len(H))
