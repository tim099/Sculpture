# 階段十一：照 verify_flags.json 下 CLI —— 旗桿（格）、旗的固定點、旗（帆＋貼圖）、meta
# 用法：python -I -X utf8 -B apply_flags.py <design 資料夾> <步驟>
#   步驟：stamp（每刀讀回 placed；只跑一次）｜anchors（overwrite=1）｜sails（overwrite=1）｜meta（flags_meta.tsv 批次）
#   · ⛔ 失敗那一行整段印出來
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
V = json.load(open(os.path.join(D, 'verify_flags.json'), encoding='utf-8'))
ASM = 'summit-stormkaap-01m-assembly'
ok = bad = 0


def cli(args):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        bad += 1
        print('✗ rc=%d' % r.returncode, ' '.join(args[:5])); print((r.stdout + r.stderr)[-900:])
    else:
        ok += 1
    return r.stdout


xyz = lambda v: ','.join('%d' % c for c in v)
fwd = lambda p: os.path.join(D, p).replace(chr(92), '/')
if step == 'stamp':
    for k, o in sorted(V['stamp'].items()):
        out = cli(['op=stampvox', 'persona=summit', 'work=' + o['work'], 'voxels=' + fwd(o['file']), 'at=0,0,0', 'expect_pixels=%d' % o['voxels'], 'draft=0'])
        m = re.search(r'🔢 placed = (\d+)', out)
        print(o['name'], o['work'], 'voxels', o['voxels'], 'placed', m.group(1) if m else '?')
elif step == 'anchors':
    for k, L in sorted(V['anchors'].items()):
        for a in L:
            cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + a['work'], 'name=' + a['name'], 'at=' + xyz(a['at']), 'overwrite=1',
                 'note=%s（階段十一 verify_flags.json）' % a['kind']])
    print('anchors', sum(len(L) for L in V['anchors'].values()))
elif step == 'sails':
    for s in V['sails']:
        cli(['op=work', 'sub=sail', 'persona=summit', 'work=' + ASM, 'name=' + s['name'], 'corners=' + '|'.join(s['corners']),
             'corner_names=' + '|'.join(s['corner_names']), 'bind=' + s['bind'], 'free=' + s['free'], 'fullness=%g' % s['fullness'],
             'res=%d' % s['res'], 'color=' + s['color'], 'texture=' + fwd(s['texture']), 'overwrite=1', 'note=' + s['note'] + '（階段十一）'])
        print('sail', s['name'])
elif step == 'meta':
    out = cli(['op=work', 'sub=meta', 'persona=summit', 'work=' + ASM, 'file=' + fwd('flags_meta.tsv')])
    print(chr(10).join(l for l in out.splitlines() if l.startswith('🔢') or l.startswith('✓'))[-600:])
else:
    raise SystemExit('步驟？ stamp|anchors|sails|meta')
print(step, 'ok', ok, 'bad', bad)
