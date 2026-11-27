# 利劍號 步驟 10 落格（TASK-0022）：彈藥庫子作品（建、stampvox、固定點 blast／door、組裝件關聯 `彈藥庫` 帶 meta）＋ 甲板物件與火藥桶的外部模型（gear_placement.json）。
#   出處：tools/build_decks.py（建子作品、stampvox 帶 expect_pixels、placed 要等於清單）＋ tools/build_guns.py（模型 overwrite=1）；
#         落格計畫 Paperclip 工作目錄 .work/FAR-92/sayf/step10/gear_build_plan.md。
#   用法：python -I -X utf8 tools/build_gear.py   · 只認 exit 0；彈藥庫子作品已經有了就不重建、不重貼（讀回格數）；固定點、關聯、模型都帶 overwrite ⇒ 重跑安全。
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import wio
HULL = 'claude-xebec-01m'
ASM = HULL + '-assembly'
P = 'persona=Claude-Ojousama'
NOTE = '步驟 10（TASK-0022；design/draft_gear.py）'
WORKS = os.path.dirname(os.path.dirname(HERE))
GP = json.load(open(os.path.join(HERE, 'gear_placement.json'), encoding='utf-8'))
MG = GP['magazine']
MASK = os.path.join(HERE, 'masks', 'gear', 'magazine.vox.txt')


def num(v):
    return ('%.7f' % v).rstrip('0').rstrip('.')


def xyz(v):
    return ','.join(num(float(c)) for c in v)


def cli(*args, ok=(0,)):
    r = subprocess.run([wio.SENATE, 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:160]), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return out


# ── 彈藥庫子作品 ──
w = MG['work']
if not os.path.exists(os.path.join(WORKS, w, 'work.json')):
    cli('op=work', 'sub=create', P, 'work=' + w, 'title=' + MG['title'], 'parent_work=' + HULL, 'size=540,261,110', 'tags=sub')
    cli('op=work', 'sub=update', P, 'work=' + w, 'meters_per_voxel=0.1')
    n = sum(1 for l in open(MASK, encoding='utf-8') if l.strip() and not l.startswith('#'))
    out = cli('op=stampvox', P, 'work=' + w, 'voxels=' + MASK, 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'placed\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ placed %s != %d' % (got, n))
    print('· stampvox magazine.vox.txt placed %d' % got)
else:
    print('· %s 已經有了（不重建、不重貼）' % w)
for nm, at in MG['anchors'].items():
    cli('op=work', 'sub=anchor', P, 'work=' + w, 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=%s：彈藥庫的固定點 %s' % (NOTE, nm))
cli('op=work', 'sub=link', P, 'work=' + ASM, 'name=' + MG['link'], 'source_work=' + w, 'at=0,0,0',
    'meta=' + json.dumps(MG['meta'], ensure_ascii=False, separators=(',', ':')), 'note=' + NOTE, ok=(0, 2))

# ── 模型 ──
host = dict(GP['deck_works'], magazine=w)
n = 0
for r in GP['models']:
    cli('op=work', 'sub=model', P, 'work=' + host[r['host']], 'name=' + r['name'], 'source_work=' + r['work'], 'at=' + xyz(r['at']),
        'pivot=' + xyz(r['pivot']), 'rotate=0,0,' + num(float(r['rotate'])), 'scale=' + xyz(r['scale']), 'mirror=none', 'overwrite=1',
        'meta=' + json.dumps(r['meta'], ensure_ascii=False, separators=(',', ':')), 'note=%s：%s' % (NOTE, r['name']))
    n += 1
print('✓ 模型 %d 個（設計 %d）' % (n, len(GP['models'])))
