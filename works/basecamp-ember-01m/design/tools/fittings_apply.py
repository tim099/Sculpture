# 餘燼號 階段十八 甲板屬具：照 verify_fittings.json／fittings_placement.json 下 CLI
#   parts：建子作品（0.02 m、parent 船殼、tags sub）＋ stampvox（重跑：子作品已在 ⇒ 不重建不重落）
#   models：甲板-spar 掛外部模型（overwrite=1）
# 用法：python -I fittings_apply.py <design 資料夾> parts|models
# ⚠ 寫入偶爾 IOException「無法移除要被取代的檔案」（TASK-0534）⇒ 只對那一句重試，最多 3 次
import sys, os, json, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
what = sys.argv[2]
HULL = 'basecamp-ember-01m'
V = json.load(open(os.path.join(D, 'verify_fittings.json'), encoding='utf-8'))
TITLE = {'binnacle': '餘燼號 羅經櫃（0.02 m／格）', 'capstan': '餘燼號 主絞盤（0.02 m／格）'}
ok = bad = retried = 0


def cli(args, quiet=False):
    global ok, bad, retried
    for k in range(4):
        r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode and '無法移除要被取代的檔案' in (r.stdout + r.stderr) and k < 3:
            retried += 1
            time.sleep(0.5)
            continue
        break
    if quiet:
        return r.returncode
    if r.returncode:
        bad += 1
        print('✗', ' '.join(args[:5]), (r.stdout + r.stderr)[-400:])
    else:
        ok += 1
        print('\n'.join(l for l in r.stdout.splitlines() if l.startswith('✓') or 'placed =' in l))
    return r.returncode


def num(v):
    return ('%.3f' % v).rstrip('0').rstrip('.') if isinstance(v, float) else '%d' % v


def xyz(v):
    return ','.join(num(float(c)) for c in v)


if what == 'parts':
    for k, p in V.items():
        w = '%s-%s' % (HULL, k)
        if cli(['op=work', 'sub=show', 'work=' + w], quiet=True) == 0:
            print('· %s 已在 ⇒ 不重建' % w)
            continue
        cli(['op=work', 'sub=create', 'persona=basecamp', 'id=' + w, 'title=' + TITLE[k], 'size=' + xyz(p['size']), 'parent_work=' + HULL, 'tags=sub'])
        cli(['op=work', 'sub=update', 'persona=basecamp', 'work=' + w, 'meters_per_voxel=0.02'])
        cli(['op=stampvox', 'persona=basecamp', 'work=' + w, 'voxels=' + os.path.join(D, p['file']).replace('\\', '/'), 'at=0,0,0',
             'expect_pixels=%d' % p['voxels']])
elif what == 'models':
    PL = json.load(open(os.path.join(D, 'fittings_placement.json'), encoding='utf-8'))
    for m in PL['models']:
        s = m['scale']
        cli(['op=work', 'sub=model', 'persona=basecamp', 'work=' + m['work'], 'name=' + m['name'], 'source_work=' + m['source_work'],
             'at=' + xyz(m['at']), 'pivot=' + xyz(m['pivot']), 'rotate=0,0,0', 'scale=' + xyz([s, s, s]), 'overwrite=1',
             'note=%s（階段十八；draft_fittings_place.py 搜到、0 碰撞）' % m['label']])
print('ok %d / bad %d / 重試 %d' % (ok, bad, retried))
