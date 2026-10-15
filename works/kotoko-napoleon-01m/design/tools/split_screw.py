# 拿破崙號 螺旋槳拆成外部模型（ame 2026-10-16 酒館 seq 25026，Tim：「可以通知kotoko拆出螺旋槳」；造船規格 §9 kind 表 propeller，同光榮號 kaguya-gloire-01m-screw）
#   階段五的 -screw（整船的框、世界座標，at 0,0,0 的關聯「螺旋槳」）⇒ 同一件子作品改當外部模型「螺旋槳」：at ＝ pivot ＝ hub 那一格的格心、scale 1。
#   固定點（子作品裡）：hub（轉軸中心：葉片中段、軸線上那一格）、shaft-fwd（螺旋槳的軸往前碰到螺旋槳柱的那一格船殼）。
#   meta：kind=propeller、axis ＝ (1, 0, 0)（右旋槳：從船尾往前看、前進時順時針 ⇒ 照右手定則繞 +x；本船沒查到，取最常見的）、blades、diameter_m。
#   讀數：組裝件少掉的格 ＝ 螺旋槳的格（逐格）；parts 的模型 meta、固定點；轉一圈（每 15°）螺旋槳每一格的格心落在船殼裡幾格；
#         軸（kind=shaft）的 aft 離 hub／shaft-fwd 多遠（遊戲：24 格以內才接得上）。
#   用法：python -I -X utf8 tools/split_screw.py <design> [plan|apply|check]
import json, math, os, subprocess, sys, tempfile
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')
D = os.path.abspath(sys.argv[1])
step = sys.argv[2] if len(sys.argv) > 2 else 'plan'
sys.path.insert(0, D)
import mio  # noqa: E402

W, NAME = 'kotoko-napoleon-01m-screw', '螺旋槳'
plan = json.load(open(os.path.join(D, 'plan.json'), encoding='utf-8'))
PR = plan['propeller']
HUB = [PR['x'], 200, PR['hub_z']]
META = {'kind': 'propeller', 'axis_x': 1, 'axis_y': 0, 'axis_z': 0, 'blades': PR['blades'], 'diameter_m': round(PR['diameter'] * 0.1, 2)}
PIV = [HUB[0] + 0.5, HUB[1] + 0.5, HUB[2] + 0.5]
import re  # noqa: E402


def cli(*a):
    r = subprocess.run(['senate', 'cmd', 'sculpture'] + [x for kv in a for x in ('--arg', kv)], capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        print((r.stdout + r.stderr)[-1200:])
        raise SystemExit('✗ ' + ' '.join(a[:4]))
    return r.stdout


def parts():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'p.json').replace(os.sep, '/')
        cli('op=export', 'format=parts', 'work=' + mio.ASM, 'out=' + out)
        return json.load(open(out, encoding='utf-8'))


C = mio.export_list(W, None)
xs = C[(C[:, 1] == 200) & (C[:, 2] == PR['hub_z'])][:, 0]
SFWD = [int(xs.max()) + 1, 200, PR['hub_z']]                            # 軸線上最前面那一格的下一格 ＝ 螺旋槳柱（船殼）
print('螺旋槳 %d 格；hub %s、shaft-fwd %s、pivot %s；meta %s' % (len(C), HUB, SFWD, PIV, META))
if step == 'plan':
    raise SystemExit(0)

if step == 'apply':
    before = mio.export_list(mio.ASM, 'all')
    cli('op=work', 'sub=anchor', 'persona=kotoko', 'work=' + W, 'name=hub', 'at=' + ','.join(map(str, HUB)), 'overwrite=1', 'note=轉軸中心（葉片中段、軸線上那一格）')
    cli('op=work', 'sub=anchor', 'persona=kotoko', 'work=' + W, 'name=shaft-fwd', 'at=' + ','.join(map(str, SFWD)), 'overwrite=1', 'note=螺旋槳的軸往前碰到螺旋槳柱（船殼）那一格')
    cli('op=work', 'sub=unlink', 'persona=kotoko', 'work=' + mio.ASM, 'name=' + NAME)
    cli('op=work', 'sub=model', 'persona=kotoko', 'work=' + mio.ASM, 'name=' + NAME, 'source_work=' + W, 'at=' + ','.join('%g' % v for v in PIV),
        'pivot=' + ','.join('%g' % v for v in PIV), 'rotate=0,0,0', 'scale=1', 'overwrite=1', 'meta=' + json.dumps(META, sort_keys=True),
        'note=螺旋槳（外部模型：遊戲照航速繞 axis 轉；at ＝ pivot ＝ hub 格心 ⇒ 子作品的世界座標原樣）')
    after = mio.export_list(mio.ASM, 'all')
    kb = set(map(tuple, before[:, :4].tolist())); ka = set(map(tuple, after[:, :4].tolist())); ks = set(map(tuple, C[:, :4].tolist()))
    print('組裝件 %d → %d：少掉的 ＝ 螺旋槳的格 %s（少 %d、多 %d）' % (len(before), len(after), (kb - ka) == ks, len(kb - ka), len(ka - kb)))

# check
P = parts()
m = next((x for x in P['models'] if x['path'] == NAME), None)
lk = next((l for l in P['links'] if l['path'] == NAME), None)
print('parts：模型 %s state %s、meta 相同 %s、hub %s、shaft-fwd %s；關聯「%s」還在 %s' % (
    NAME, m and m.get('state'), m and m.get('meta') == META, m and m['points'].get('hub'), m and m['points'].get('shaft-fwd'), NAME, lk is not None))
A = mio.export_list(mio.ASM, 'all')
A = A[A[:, 2] < 120]
occ = np.zeros((1200, 400, 120), bool)
occ[A[:, 0], A[:, 1], A[:, 2]] = True
Q = C[:, :3].astype(float) + 0.5 - np.array(PIV)
worst = 0
for deg in range(0, 360, 15):
    t = math.radians(deg)
    y = Q[:, 1] * math.cos(t) - Q[:, 2] * math.sin(t); z = Q[:, 1] * math.sin(t) + Q[:, 2] * math.cos(t)
    i = np.floor(np.stack([Q[:, 0], y, z], 1) + np.array(PIV)).astype(int)
    worst = max(worst, int(occ[i[:, 0], i[:, 1], i[:, 2]].sum()))
print('轉一圈（每 15°）：螺旋槳的格心落在船殼裡最多 %d 格' % worst)
sh = next((l for l in P['links'] if (l.get('meta') or {}).get('kind') == 'shaft'), None)
if sh:
    a = np.array(sh['points']['aft'])
    print('軸「%s」aft %s：離 hub %.1f 格、離 shaft-fwd %.1f 格（遊戲 24 格以內接得上）' % (
        sh['path'], sh['points']['aft'], float(np.linalg.norm(a - np.array(HUB) - 0.5)), float(np.linalg.norm(a - np.array(SFWD) - 0.5))))
mo = dict(re.findall(r'🔢 (\w+) = (\S+)', cli('op=work', 'sub=models', 'work=' + mio.ASM)))
print('引擎：模型 %s、models_broken %s' % (mo.get('model_count'), mo.get('models_broken')))
