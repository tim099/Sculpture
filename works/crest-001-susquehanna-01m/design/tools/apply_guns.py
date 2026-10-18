# 蘇士奎哈納號（crest-001，TASK-0697）：本檔抄自光榮號 kaguya-gloire-01m/design/tools/apply_guns.py（kaguya）—— 下面註解裡的「蘇士奎哈納號」原文是光榮號，改過的地方另外註明
# 蘇士奎哈納號 階段八落格（TASK-0613）—— 抄自三叉戟號 gura-tridente-01m/design/tools/apply_guns.py（gura）；改：persona、註記。
# 原檔說明：階段八落格（TASK-0561）：照 verify_guns.json —— 墊木（stampvox，每刀讀回 placed）、138 門外部模型（掛在所在甲板的子作品；借來的砲子作品，匯入自動 credit）
#   用法：python -I -X utf8 tools/apply_guns.py <design> <步驟> [模型名 regex]
#   步驟：pads（只跑一次；甲板子作品已有那幾格就擋）｜models（overwrite=1，以 verify 為準）｜meta（只改 meta：砲種代碼跟 ame 對過之後改 plan → 重跑 draft → 這一步）
#   · 參考風暴角號 apply_guns.py（summit）；IOException 自動重試；⛔ 失敗那一行整段印出來
import json, os, re, subprocess, sys, tempfile

sys.stdout.reconfigure(encoding='utf-8')
D, step = os.path.abspath(sys.argv[1]), sys.argv[2]
flt = re.compile(sys.argv[3] if len(sys.argv) > 3 else '.')
VF = os.environ.get('GUNS_VERIFY', 'verify_guns.json')   # 蘇士奎哈納號加的：迴旋砲用 verify_pivots.json
V = json.load(open(os.path.join(D, VF), encoding='utf-8'))
ok = bad = retries = 0


def cli(args):
    global ok, bad, retries
    for _ in range(5):
        r = subprocess.run(['senate', 'cmd', 'sculpture'] + sum([['--arg', a] for a in args], []), capture_output=True, text=True, encoding='utf-8', errors='replace')
        out = r.stdout + r.stderr
        if r.returncode == 0 or 'IOException' not in out:
            break
        retries += 1
    if r.returncode:
        bad += 1
        print('✗ rc=%d' % r.returncode, ' '.join(args[:6]))
        print(out[-1200:])
        raise SystemExit(1)
    ok += 1
    return out


xyz = lambda v: ','.join('%g' % c for c in v)
if step == 'pads':
    for hw, P in sorted(V['pads'].items()):
        f = os.path.join(D, P['file']).replace('\\', '/')
        out = cli(['op=stampvox', 'persona=crest-001', 'work=' + hw, 'voxels=' + f, 'at=0,0,0', 'expect_pixels=%d' % P['voxels'], 'draft=0', 'share=0'])
        m = re.search(r'🔢 placed = (\d+)', out)
        if not m or int(m.group(1)) != P['voxels']:
            raise SystemExit('✗ %s placed %s ≠ %d' % (hw, m and m.group(1), P['voxels']))
        print('墊木', hw, P['voxels'])
elif step == 'models':
    n = 0
    for r in V['rows']:
        if not flt.search(r['host_link'] + '/' + r['model']):
            continue
        T = V.get('types', {}).get(r['type'])
        cli(['op=work', 'sub=model', 'persona=crest-001', 'work=' + r['host_work'], 'name=' + r['model'], 'source_work=' + r['work'],
             'at=' + xyz(r['at']), 'pivot=' + xyz(r['pivot']), 'rotate=' + xyz(r['rotate']), 'scale=%g' % r['scale'], 'mirror=' + r['mirror'], 'overwrite=1',
             'meta=' + json.dumps(r['meta'], ensure_ascii=False, sort_keys=True),
             'note=蘇士奎哈納號 %s（階段八 %s：沿用現有砲、退到零碰撞；pivot ＝ 砲架底層最前緣、軸線中間、甲板面）' % (r['type'], os.path.basename(VF))])
        n += 1
        if n % 20 == 0:
            print('  模型 %d' % n, flush=True)
    print('模型', n)
elif step == 'meta':
    by = {}
    for r in V['rows']:
        if flt.search(r['host_link'] + '/' + r['model']):
            by.setdefault(r['host_work'], []).append(r)
    for hw, rs in sorted(by.items()):
        with tempfile.TemporaryDirectory() as d:
            f = os.path.join(d, 'meta.tsv')
            with open(f, 'w', encoding='utf-8', newline='\n') as fh:
                fh.write('# 蘇士奎哈納號 砲（造船規格 §9 kind=gun）\n')
                for r in rs:
                    fh.write('model\t%s\t%s\n' % (r['model'], json.dumps(r['meta'], ensure_ascii=False, separators=(',', ':'))))
            cli(['op=work', 'sub=meta', 'persona=crest-001', 'work=' + hw, 'file=' + f.replace('\\', '/')])
        print('meta', hw, len(rs))
else:
    raise SystemExit('步驟？ pads|models|meta')
print(step, 'ok', ok, 'bad', bad, 'IOException 重試', retries)
