# 利劍號 步驟 13 落格（TASK-0022）：18 支槳的外部模型掛在船殼（oars_placement.json；元件 claude-galiot-01m-oar 原樣引用，不建子作品、不落格）。
#   出處：tools/build_helm.py 的 cli 與模型寫法；落格計畫 Paperclip 工作目錄 .work/FAR-92/sayf/step13/oars_build_plan.md。
#   用法：python -I -X utf8 tools/build_oars.py   · 只認 exit 0；模型帶 overwrite=1 ⇒ 重跑安全。
import json, os, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, 'tools'))
import wio
P = 'persona=Claude-Ojousama'
NOTE = '步驟 13（TASK-0022；design/draft_oars.py）'
OP = json.load(open(os.path.join(HERE, 'oars_placement.json'), encoding='utf-8'))


def num(v):
    return ('%.7f' % v).rstrip('0').rstrip('.')


def xyz(v):
    return ','.join(num(float(c)) for c in (v if isinstance(v, (list, tuple)) else [v, v, v]))


def cli(*args):
    r = subprocess.run([wio.SENATE, 'cmd', 'sculpture'] + [x for a in args for x in ('--arg', a)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    line = next((l for l in out.splitlines() if l.startswith('✓') or l.startswith('✗')), out.strip().splitlines()[-1] if out.strip() else '')
    print('  exit=%d %s' % (r.returncode, line[:160]), flush=True)
    if r.returncode != 0:
        print(out[-1500:])
        sys.exit(1)
    return out


n = 0
for r in OP['models']:
    m = r['meta']
    cli('op=work', 'sub=model', P, 'work=' + OP['host'], 'name=' + r['name'], 'source_work=' + r['work'], 'at=' + xyz(r['at']), 'pivot=' + xyz(r['pivot']),
        'rotate=' + xyz(r['rotate']), 'scale=' + xyz(r['scale']), 'mirror=' + (r['mirror'] or 'none'), 'overwrite=1',
        'meta=' + json.dumps(m, ensure_ascii=False, separators=(',', ':')),
        'note=%s：%s 舷槳（%d 人、掃 ±%d°、傾角補 %s°）' % (NOTE, m['side'], m['rowers'], m['stroke_deg'], num(abs(float(r['rotate'][0])))))
    n += 1
print('✓ 模型 %d 個（設計 %d）' % (n, len(OP['models'])))
