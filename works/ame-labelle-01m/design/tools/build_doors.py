# 出處：calli-cosecha-01m/design/tools/build_doors.py（收穫號 TASK-1027；源頭康塞普西翁號）—— 拉貝爾號 TASK-1045：persona、單號
# 收穫號 門落格：4 扇掛成甲板子作品的外部模型（kind=door）；門板引用藍鯊號 gura-pinas-01m-door（別人的元件 ⇒ 不建、不貼、不動它的固定點）
#   用法：python -I -X utf8 tools/build_doors.py <design>
#   · 模型 overwrite=1（重跑會照 doors_placement.json 搬）
import json, os, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
design = sys.argv[1]
PL = json.load(open(os.path.join(design, 'doors_placement.json'), encoding='utf-8'))


def cli(*args, ok=(0,)):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [a for kv in args for a in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    if r.returncode not in ok:
        raise SystemExit('✗ %s：%s' % (' '.join(args[:4]), out[-600:]))
    return out


w = PL['work']
xyz = lambda v: ','.join('%g' % c for c in v)
for r in PL['rows']:
    cli('op=work', 'sub=model', 'persona=ame', 'work=' + r['host'], 'name=' + r['name'], 'source_work=' + w, 'at=' + xyz(r['at']), 'pivot=' + xyz(PL['pivot']),
        'rotate=0,0,%g' % r['rotate'], 'scale=' + xyz([PL['scale'], PL['scale'], r.get('scale_z', PL['scale'])]), 'overwrite=1', 'meta=' + json.dumps(r['meta'], ensure_ascii=False, separators=(',', ':')),
        'note=TASK-1045 門（draft_doors.py）：%s %s 舷的門洞、往外開' % (r['break'], r['side']))
print('✓ 門 %d 扇' % len(PL['rows']))
