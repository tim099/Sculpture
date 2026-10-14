# 空艙房（造船規格 §9.2）：子作品 -cabin（不雕格子，只放固定點）掛在 甲板-上 底下（關聯 `艙房`，meta kind=rooms）⇒ 遊戲名 甲板-上/艙房/<房名>
# 用法：python -I -X utf8 -B apply_rooms.py <步驟>
#   步驟：create（已有就略過）｜link（overwrite=1）｜anchors（overwrite=1）
#   · ⛔ 失敗那一行整段印出來
# 為什麼只有這三間（2026-10-14 晚量：組裝件 .vxk checksum dd4b2eab，rooms.py 的 floor_z／max_rect 同一把尺，扣掉模型外框）：
#   被艙壁圍起來的只有三處：後甲板底下（上甲板地板 x 160–232，艙壁 x 233）、艉樓底下（後甲板地板 x 104–163）、艏樓底下（上甲板地板 x 470–520）。
#   地板跟著舷弧一階一格：後甲板底下 z 87 x 160–167／86 168–177／85 178–187／84 188–199／83 200–212／82 213–228／81 229–232 —— 遊戲要平地板 ⇒ 一階一間。
#   z 85–87 那幾階被後桅（x 176–180）切到 ≤ 0.8 m 寬；z 82 那階兩舷是砲 S1／P1（x 219–228）、中線是上後甲板的梯子（x 216–225 頭頂不到 1.4 m）⇒ 剩 0.6 m。
#   艉樓底下每階 0.8–0.9 m、艏樓底下 0.8 m（砲與梯子之間）⇒ 都不標。
#   門：1 號四面都是一格的台階或船殼 ⇒ 遊戲的門算法（往外 8 格同一層地板）找不到 ⇒ 補 .door（往前、往艙壁那扇門的方向，下一階站得住的那一格）。
#   2、3 號遊戲自己找得到門（中線 x 200–203 那條同一階的 0.4 m 通道，牆上 4 格）⇒ ⛔ 不補 .door：
#   照 36_rooms.js 逐行移植的排床（scratchpad room_layout.py；先對過夜隼號 2 號 ame 報的兩個已知答案）量：補了往前的門 ⇒ 兩條走道把 2×5 格切開、放不下病床；不補 ⇒ 各 1 張。
#   1 號：門在長邊中線 ⇒ 自動擺出 床 1、手術台 1、藥箱 1（門挪到一端只剩 床 1、藥箱 1）。
import sys, subprocess

sys.stdout.reconfigure(encoding='utf-8')
step = sys.argv[1]
PRE = 'summit-stormkaap-01m'
CABIN = PRE + '-cabin'
DECK = PRE + '-deck-upper'
AT = (186, 95, 80)                      # 子作品框在組裝件的位置（＝ 甲板-上 的座標：甲板-上 在組裝件 0,0,0）
SIZE = (30, 72, 20)                     # 框住三間＋門口：x 186–215、y 95–166、z 80–99
ROOMS = [                               # 組裝件座標，含兩端；z ＝ 甲板面上第一層空氣 … 後甲板橫樑底下那一格
    {'name': '1', 'min': (188, 98, 84), 'max': (199, 162, 97), 'door': (200, 130, 83),
     'note': '後甲板底下 z 84 那一階（後桅前、全寬）1.2×6.5×1.4 m；門在前面中線（下一階）'},
    {'name': '2', 'min': (200, 97, 83), 'max': (212, 123, 96),
     'note': '後甲板底下 z 83 那一階的左舷半邊 1.3×2.7×1.4 m；門由遊戲從中線那條通道找'},
    {'name': '3', 'min': (200, 137, 83), 'max': (212, 163, 96),
     'note': '後甲板底下 z 83 那一階的右舷半邊 1.3×2.7×1.4 m；門由遊戲從中線那條通道找'},
]
UNDOOR = ['2.door', '3.door']           # 第一版補過、後來量了會擋床 ⇒ 拿掉（undoor 步驟）
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


xyz = lambda v: ','.join('%d' % c for c in v)
if step == 'create':
    rc, _ = cli(['op=work', 'sub=show', 'work=' + CABIN], quiet_fail=True)
    if rc == 0: print('已有', CABIN)
    else: cli(['op=work', 'sub=create', 'persona=summit', 'id=' + CABIN, 'title=風暴角號｜艙房（給遊戲的空艙房框，不雕格子）', 'size=' + xyz(SIZE),
               'parent_work=' + PRE, 'tags=sub']); print('建立', CABIN)
    cli(['op=work', 'sub=update', 'persona=summit', 'work=' + CABIN, 'meters_per_voxel=0.1'])
elif step == 'link':
    cli(['op=work', 'sub=link', 'persona=summit', 'work=' + DECK, 'name=艙房', 'source_work=' + CABIN, 'at=' + xyz(AT), 'overwrite=1',
         'meta={"kind":"rooms"}', 'note=空艙房（造船規格 §9.2）'])
elif step == 'anchors':
    for r in ROOMS:
        for k in [k for k in ('min', 'max', 'door') if k in r]:
            loc = tuple(r[k][i] - AT[i] for i in range(3))
            assert all(0 <= loc[i] < SIZE[i] for i in range(3)), (r['name'], k, loc)
            cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + CABIN, 'name=%s.%s' % (r['name'], k), 'at=' + xyz(loc), 'overwrite=1',
                 'note=%s（TASK-0547）' % r['note']])
    print('anchors', sum(len([k for k in ('min', 'max', 'door') if k in r]) for r in ROOMS))
elif step == 'undoor':
    for nm in UNDOOR:
        cli(['op=work', 'sub=unanchor', 'persona=summit', 'work=' + CABIN, 'name=' + nm])
else:
    raise SystemExit('步驟？ create|link|anchors|undoor')
print(step, 'ok', ok, 'bad', bad)
