# 利劍號 步驟 11 落格（TASK-0022）：舵、舵柄子作品（建、stampvox、固定點）、吊錨木貼進甲板-main、船尾平台刻舵頭孔、錨鏈孔固定點、舵／舵柄／錨的外部模型（helm_placement.json）。
#   出處：tools/build_gear.py（同一套 cli、建子作品、stampvox 帶 expect_pixels）；落格計畫 Paperclip 工作目錄 .work/FAR-92/sayf/step11/helm_build_plan.md。
#   用法：python -I -X utf8 tools/build_helm.py   · 只認 exit 0；子作品已經有了就不重建、不重貼；吊錨木與平台刻格先看 events 有沒有這一刀（有就跳過）；固定點、模型帶 overwrite ⇒ 重跑安全。
import json, os, re, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import wio
HULL = 'claude-xebec-01m'
P = 'persona=Claude-Ojousama'
NOTE = '步驟 11（TASK-0022；design/draft_helm.py）'
WORKS = os.path.dirname(os.path.dirname(HERE))
HP = json.load(open(os.path.join(HERE, 'helm_placement.json'), encoding='utf-8'))


def num(v):
    return ('%.7f' % v).rstrip('0').rstrip('.')


def xyz(v):
    return ','.join(num(float(c)) for c in (v if isinstance(v, (list, tuple)) else [v, v, v]))


def cli(*args, ok=(0,)):
    r = subprocess.run([wio.SENATE, 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:160]), flush=True)
    if r.returncode not in ok:
        print(out[-1500:])
        sys.exit(1)
    return out


def mask(name):
    return os.path.join(HERE, 'masks', name + '.vox.txt')


def count(path):
    return sum(1 for l in open(path, encoding='utf-8') if l.strip() and not l.startswith('#'))


def cut(op, work, path):
    n = count(path)
    out = cli('op=' + op, P, 'work=' + work, 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % n, 'share=0')
    m = re.search(r'(?:placed|carved)\D{0,12}(\d[\d,]*)', out)
    got = int(m.group(1).replace(',', '')) if m else None
    if got != n:
        print(out[-1500:])
        raise SystemExit('✗ %s %s: %s != %d' % (op, work, got, n))
    print('· %s %s %s: %d' % (op, work, os.path.basename(path), got))


def done_before(work, path):
    """這份清單已經在那件作品的 events 裡（重跑不重落）。"""
    ev = os.path.join(WORKS, work, 'events')
    base = os.path.basename(path)
    return os.path.isdir(ev) and any(base in open(os.path.join(d, f), encoding='utf-8', errors='replace').read()
                                     for d, _, fs in os.walk(ev) for f in fs if f.endswith('.json'))


# ── 舵、舵柄子作品 ──
for key in ('rudder', 'tiller'):
    R = HP[key]
    if not os.path.exists(os.path.join(WORKS, R['work'], 'work.json')):
        cli('op=work', 'sub=create', P, 'work=' + R['work'], 'title=' + R['title'], 'parent_work=' + HULL, 'size=540,261,110', 'tags=sub')
        cli('op=work', 'sub=update', P, 'work=' + R['work'], 'meters_per_voxel=0.1')
        cut('stampvox', R['work'], mask(R['list']))
    else:
        print('· %s 已經有了（不重建、不重貼）' % R['work'])
    for nm, at in R['anchors'].items():
        cli('op=work', 'sub=anchor', P, 'work=' + R['work'], 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=%s：%s' % (NOTE, nm))

# ── 吊錨木（貼進甲板-main）、船尾平台刻舵頭孔 ──
C = HP['cathead']
if done_before(C['work'], mask(C['list'])):
    print('· 吊錨木已經落過')
else:
    cut('stampvox', C['work'], mask(C['list']))
K = HP['carve']
if done_before(K['work'], mask(K['list'])):
    print('· 平台刻格已經刻過')
else:
    cut('carvevox', K['work'], mask(K['list']))

# ── 錨鏈孔固定點（船殼）──
for nm, at in HP['hull_anchors']['points'].items():
    cli('op=work', 'sub=anchor', P, 'work=' + HP['hull_anchors']['work'], 'name=' + nm, 'at=%d,%d,%d' % tuple(at), 'overwrite=1', 'note=%s：錨鏈孔 %s' % (NOTE, nm))

# ── 模型 ──
n = 0
for key in ('rudder', 'tiller'):
    R = HP[key]
    cli('op=work', 'sub=model', P, 'work=' + R['host'], 'name=' + R['model'], 'source_work=' + R['work'], 'at=' + xyz(R['at']), 'pivot=' + xyz(R['pivot']),
        'rotate=0,0,0', 'scale=' + xyz(R['scale']), 'mirror=none', 'overwrite=1', 'meta=' + json.dumps(R['meta'], ensure_ascii=False, separators=(',', ':')),
        'note=%s：%s' % (NOTE, R['model']))
    n += 1
for A in HP['anchors']:
    cli('op=work', 'sub=model', P, 'work=' + A['host_work'], 'name=' + A['name'], 'source_work=' + A['work'], 'at=' + xyz(A['at']), 'pivot=' + xyz(A['pivot']),
        'rotate=' + xyz(A['rotate']), 'scale=' + xyz(A['scale']), 'mirror=' + (A['mirror'] or 'none'), 'overwrite=1',
        'meta=' + json.dumps(A['meta'], ensure_ascii=False, separators=(',', ':')), 'note=%s：%s' % (NOTE, A['name']))
    n += 1
print('✓ 模型 %d 個（設計 %d）' % (n, 2 + len(HP['anchors'])))
