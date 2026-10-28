# 藍鯊號 艙壁門落格（TASK-0967）：門板子作品 -door（0.05 m，貼 masks/doors/door.vox.txt、固定點 hinge-a／hinge-b）、6 扇掛成船樓甲板子作品的外部模型（kind=door）
#   用法：python -I -X utf8 tools/build_doors.py <design>
#   · 子作品已存在 ⇒ 不重建、不重貼；固定點、模型 overwrite=1
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
HULL = 'gura-pinas-01m'
WORKS = os.environ.get('SCULPT_WORKS') or os.path.dirname(os.path.dirname(os.path.abspath(design)))   # worktree 只放 design/ ⇒ 作品資料讀共用的那一份
PL = json.load(open(os.path.join(design, 'doors_placement.json'), encoding='utf-8'))


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        raise SystemExit('✗ %s：%s' % (' '.join(args[:4]), out[-600:]))
    return out


w = PL['work']
path = os.path.abspath(os.path.join(design, 'masks', 'doors', 'door.vox.txt')).replace('\\', '/')
n = sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))
if not os.path.exists(os.path.join(WORKS, w, 'work.json')):
    cli('op=work', 'sub=create', 'persona=gura', 'work=' + w, 'title=藍鯊號 艙壁門（直條木板、兩道鐵鉸鏈帶；左右開、鉸鏈直立；0.05 m，通用部件，kind=door）',
        'parent_work=' + HULL, 'size=%d,%d,%d' % tuple(PL['size']), 'tags=sub')
    cli('op=work', 'sub=update', 'persona=gura', 'work=' + w, 'meters_per_voxel=0.05')
    out = cli('op=stampvox', 'persona=gura', 'work=' + w, 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    if not m or int(m.group(1).replace(',', '')) != n:
        raise SystemExit('✗ placed ≠ %d：%s' % (n, out[-800:]))
    print('✓ 建立 %s（%d 格）' % (w, n), flush=True)
for an, at in PL['anchors'].items():
    cli('op=work', 'sub=anchor', 'persona=gura', 'work=' + w, 'name=' + an, 'at=%d,%d,%d' % tuple(at), 'overwrite=1',
        'note=門的鉸鏈軸（hinge-a 在上、hinge-b 在下 ⇒ 軸朝下 ⇒ 往模型 +x 開；draft_doors.py）')
xyz = lambda v: ','.join('%g' % c for c in v)
for r in PL['rows']:
    cli('op=work', 'sub=model', 'persona=gura', 'work=' + r['host'], 'name=' + r['name'], 'source_work=' + w, 'at=' + xyz(r['at']), 'pivot=' + xyz(PL['pivot']),
        'rotate=0,0,%g' % r['rotate'], 'scale=' + xyz([PL['scale']] * 3), 'overwrite=1', 'meta=' + json.dumps(r['meta'], ensure_ascii=False, separators=(',', ':')),
        'note=步驟 10 門（TASK-0967；draft_doors.py）：%s %s 舷的門洞、往外開' % (r['break'], r['side']))
print('✓ 門 %d 扇' % len(PL['rows']))
