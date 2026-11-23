# 海鷗號 步驟 11 落格（TASK-0024）：舵、舵柄各一件子作品（整船的框，stampvox 讀回）＋固定點、組裝件裡的模型（at ＝ pivot ＝ 鉸鏈點）、
#   四爪錨模型（甲板-main）、船殼的錨鏈孔固定點 hawse-P。
#   出處：照星辰號 claude-baghlah-01m/design/tools/build_helm.py 的順序（子作品 → 固定點 → 模型）；呼叫方式照本船 tools/build_masts.py。
#   用法：python -I -X utf8 tools/build_helm.py   · 只認 exit 0；已經存在的子作品不重建、不重貼。
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKS = os.path.dirname(os.path.dirname(HERE))
SENATE = os.environ.get('SENATE', '/paperclip/instances/default/projects/482d2c24-3be9-40fc-8ec9-1a7a02dd4f3f/1ea1d409-d2dd-45dc-b44e-35e83e49b833/_default/.work/senate/bin/senate')
P = 'persona=Claude-Ojousama'
HULL = 'claude-felucca-01m'
ASM = HULL + '-assembly'
NOTE = '步驟 11（TASK-0024；design/draft_helm.py）'
HP = json.load(open(os.path.join(HERE, 'helm_placement.json'), encoding='utf-8'))


def cli(*args, ok=(0,)):
    r = subprocess.run([SENATE, 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:170]), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return out


for key, fn in (('rudder', 'rudder'), ('tiller', 'tiller')):
    h = HP[key]
    if not os.path.exists(os.path.join(WORKS, h['work'], 'work.json')):
        cli('op=work', 'sub=create', P, 'id=' + h['work'], 'title=' + h['title'], 'parent_work=' + HULL, 'size=170,161,50')
        cli('op=work', 'sub=update', P, 'work=' + h['work'], 'meters_per_voxel=0.1', 'tags=sub')
        f = os.path.join(HERE, 'masks', 'helm', fn + '.vox.txt')
        n = sum(1 for l in open(f, encoding='utf-8') if l.strip() and not l.startswith('#'))
        out = cli('op=stampvox', P, 'work=' + h['work'], 'voxels=' + f, 'at=0,0,0', 'expect_pixels=%d' % n)
        m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
        if not m or int(m.group(1).replace(',', '')) != n:
            sys.exit('✗ placed != %d' % n)
    for an, at in h['anchors'].items():
        cli('op=work', 'sub=anchor', P, 'work=' + h['work'], 'name=' + an, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=' + NOTE)
    cli('op=work', 'sub=model', P, 'work=' + ASM, 'name=' + h['model'], 'source_work=' + h['work'], 'at=%g,%g,%g' % tuple(h['at']),
        'pivot=%g,%g,%g' % tuple(h['pivot']), 'scale=1', 'rotate=0,0,0', 'meta=' + json.dumps(h['meta'], ensure_ascii=False, separators=(',', ':')),
        'overwrite=1', 'note=' + NOTE)
a = HP['anchor']
cli('op=work', 'sub=model', P, 'work=' + a['host'], 'name=' + a['name'], 'source_work=' + a['work'], 'at=%g,%g,%g' % tuple(a['at']),
    'pivot=%g,%g,%g' % tuple(a['pivot']), 'scale=%g' % a['scale'], 'rotate=0,0,0', 'meta=' + json.dumps(a['meta'], ensure_ascii=False, separators=(',', ':')),
    'overwrite=1', 'note=' + NOTE + '：四爪錨（Schellinks 1664 畫在左舷）')
for an, at in HP['hull_anchors'].items():
    cli('op=work', 'sub=anchor', P, 'work=' + HULL, 'name=' + an, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=' + NOTE + '：錨鏈孔（錨纜過舷頂的地方）')
