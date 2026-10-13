# 階段十三：照 verify_guns.json 下 CLI —— 砲的固定點＋12 門外部模型
# 用法：python -I -X utf8 -B apply_guns.py <design 資料夾> <步驟> [模型名 regex]
#   步驟：anchors（-gun-4l 的固定點）｜models（主甲板子作品裡放模型；S 照原樣、P mirror=y）
#   · overwrite=1 ⇒ 重跑一樣（子作品建立與落格是手下的兩刀，見 notes.md 階段十三）
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
flt = re.compile(sys.argv[3] if len(sys.argv) > 3 else '.')
V = json.load(open(os.path.join(D, 'verify_guns.json'), encoding='utf-8'))
ok = bad = 0


def cli(args):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        bad += 1
        print('✗ rc=%d' % r.returncode, ' '.join(args[:5]), (r.stdout + r.stderr)[-600:])
    else:
        ok += 1
    return r.returncode, r.stdout


def xyz(v):
    return ','.join('%g' % c for c in v)


g = V['gun']
if step == 'anchors':
    for name, at in g['anchors'].items():
        cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + g['work'], 'name=' + name, 'at=' + xyz(at), 'overwrite=1',
             'note=4 磅長砲（階段十三，draft_guns.py）；子作品座標 x 寬、y 砲身（砲口 +y）、z 0 甲板面'])
    print('anchors', len(g['anchors']))
elif step == 'models':
    for r in V['rows']:
        if not flt.search(r['model']):
            continue
        cli(['op=work', 'sub=model', 'persona=summit', 'work=' + V['host'], 'name=' + r['model'], 'source_work=' + g['work'],
             'at=' + xyz(r['at']), 'pivot=' + xyz(g['pivot']), 'rotate=0,0,0', 'scale=%g' % V['scale'], 'mirror=' + r['mirror'], 'overwrite=1',
             'meta=' + json.dumps(r['meta'], ensure_ascii=False, sort_keys=True),
             'note=4 磅長砲（階段十三：退到零碰撞；pivot ＝ 砲架前緣中間、甲板面；P 舷 mirror=y）'])
        print('model', r['model'], xyz(r['at']), r['mirror'])
else:
    raise SystemExit('步驟？ anchors|models')
print(step, 'ok', ok, 'bad', bad)
