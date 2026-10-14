# 階段十五：照 verify_helm.json 下 CLI —— 舵輪兩件子作品（parent 船殼、sub、0.02 m）＋三個外部模型掛在 甲板-後（舵輪、舵輪座、羅經櫃）
# 從夜隼號 apply_helm.py 改：不碰舵（階段六已是模型）；羅經櫃引用夜隼號的 -binnacle。
# 用法：python -I -X utf8 -B apply_helm.py <design 資料夾> <步驟>
#   步驟：create（已存在 ⇒ 略過）｜stamp（每刀印 placed）｜anchors｜models（overwrite=1 ⇒ 重跑一樣）　· ⛔ 失敗整段印出來
import sys, os, json, re, subprocess

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
V = json.load(open(os.path.join(D, 'verify_helm.json'), encoding='utf-8'))
PRE = 'summit-stormkaap-01m'
ok = bad = 0


def cli(args, quiet_fail=False):
    global ok, bad
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        if not quiet_fail:
            bad += 1; print('✗ rc=%d' % r.returncode, ' '.join(args[:5])); print((r.stdout + r.stderr)[-900:])
    else:
        ok += 1
    return r.returncode, r.stdout


xyz = lambda v: ','.join('%g' % c for c in v)
parts = [V['wheel'], V['stand']]
if step == 'create':
    for p in parts:
        rc, _ = cli(['op=work', 'sub=show', 'work=' + p['work']], quiet_fail=True)
        if rc == 0:
            print('已有', p['work'])
        else:
            cli(['op=work', 'sub=create', 'persona=summit', 'id=' + p['work'], 'title=' + p['title'], 'size=' + xyz(V['size']), 'parent_work=' + PRE, 'tags=sub'])
            print('建立', p['work'])
        cli(['op=work', 'sub=update', 'persona=summit', 'work=' + p['work'], 'meters_per_voxel=%g' % V['mpv']])
elif step == 'stamp':
    for p in parts:
        path = os.path.join(D, p['file']).replace('\\', '/')
        rc, out = cli(['op=stampvox', 'persona=summit', 'work=' + p['work'], 'voxels=' + path, 'at=0,0,0', 'expect_pixels=%d' % p['cells'], 'draft=0'])
        m = re.search(r'placed[^0-9]{0,8}([0-9,]+)', out)
        print('stamp', p['work'], p['cells'], 'placed', m.group(1) if m else '?')
elif step == 'anchors':
    for p in parts:
        for nm, at in p['anchors'].items():
            cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + p['work'], 'name=' + nm, 'at=' + xyz(at), 'overwrite=1', 'note=階段十五 verify_helm.json'])
    print('anchors', sum(len(p['anchors']) for p in parts))
elif step == 'models':
    for m in V['models']:
        cli(['op=work', 'sub=model', 'persona=summit', 'work=' + V['host_work'], 'name=' + m['name'], 'source_work=' + m['work'], 'at=' + xyz(m['at']),
             'pivot=' + xyz(m['pivot']), 'rotate=0,0,0', 'scale=%g' % m['scale'], 'overwrite=1', 'meta=' + json.dumps(m['meta'], ensure_ascii=False, sort_keys=True),
             'note=階段十五（verify_helm.json）'])
        print('model', V['host_link'] + '/' + m['name'], xyz(m['at']))
else:
    raise SystemExit('步驟？ create|stamp|anchors|models')
print(step, 'ok', ok, 'bad', bad)
