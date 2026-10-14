# TASK-0576 落格：照 verify_implements.json —— 每層一件 rammer／sponge 子作品（整船框、0.1 m、parent 船殼、tags sub）→ stampvox（讀回 placed）→ 那一層甲板子作品裡的關聯
#   用法：python -I -X utf8 tools/apply_implements.py <design> [verify 檔名（預設 verify_implements.json；shot garland 用 verify_garlands.json）] [單號]
#   ⇒ 「整船框、at 0,0,0、每層一件、關聯在甲板裡」這一型的子作品都走這一支
import json, os, re, subprocess, sys, time

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
VF = sys.argv[2] if len(sys.argv) > 2 else 'verify_implements.json'
TASK = sys.argv[3] if len(sys.argv) > 3 else 'TASK-0576'
V = json.load(open(os.path.join(D, VF), encoding='utf-8'))
retried = 0


def run(*a):
    return subprocess.run(['senate', 'cmd', 'sculpture'] + [x for kv in a for x in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')


def cli(*a):
    global retried
    for k in range(5):
        r = run(*a)
        out = r.stdout + r.stderr
        if r.returncode and any(t in out for t in ('IOException', '無法移除要被取代的檔案', 'Unable to remove the file to be replaced')) and k < 4:
            retried += 1
            time.sleep(0.5)
            continue
        break
    if r.returncode:
        print(out[-1000:])
        raise SystemExit('✗ ' + ' '.join(a[:4]))
    return r.stdout


for w in V['works']:
    if run('op=work', 'sub=show', 'work=' + w['work']).returncode != 0:
        cli('op=work', 'sub=create', 'persona=gura', 'id=' + w['work'], 'title=' + w['title'], 'size=1100,400,800', 'parent_work=gura-tridente-01m', 'tags=sub')
        cli('op=work', 'sub=update', 'persona=gura', 'work=' + w['work'], 'meters_per_voxel=0.1')
    have = int(re.search(r'🔢 total_voxels = (\d+)', cli('op=stats', 'work=' + w['work'])).group(1))
    if have == 0:
        out = cli('op=stampvox', 'persona=gura', 'work=' + w['work'], 'voxels=' + os.path.join(D, w['file']).replace(os.sep, '/'), 'at=0,0,0',
                  'expect_pixels=%d' % w['voxels'], 'share=0')
        n = int(re.search(r'🔢 placed = (\d+)', out).group(1))
        if n != w['voxels']:
            raise SystemExit('✗ %s placed %d ≠ %d' % (w['work'], n, w['voxels']))
    elif have != w['voxels']:
        raise SystemExit('✗ %s 已有 %d 格 ≠ %d' % (w['work'], have, w['voxels']))
    cli('op=work', 'sub=link', 'persona=gura', 'work=' + w['host_work'], 'name=' + w['link'], 'source_work=' + w['work'], 'at=0,0,0', 'overwrite=1',
        'note=%s（%s）' % (w['title'], TASK))
    print('✓', w['work'], w['voxels'], '關聯', w['host_work'], w['link'])
print('IOException 重試', retried)
