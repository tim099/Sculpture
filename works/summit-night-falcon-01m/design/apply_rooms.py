# 空艙房（TASK-0573；造船規格 §9.2）：子作品 -cabin（不雕格子，只放固定點）掛在 甲板-主 底下（關聯 `艙房`，meta kind=rooms）⇒ 遊戲名 甲板-主/艙房/<房名>
# 用法：python -I -X utf8 -B apply_rooms.py <步驟>
#   步驟：create（已有就略過）｜link（overwrite=1）｜anchors（overwrite=1）
#   · ⛔ 失敗那一行整段印出來
# 為什麼只有兩間（2026-10-14 量，falcon.vxk 13T22:42，rooms.py 的 floor_z 同一把尺）：
#   艙房地板沿舷弧一階一階（z 28 x 65–69／27 x 70–77／26 x 78–87／25 x 88–98／24 x 99–113／23 x 114–137），遊戲要平地板；
#   扣掉砲 S1／P1（x 92–99）、S2／P2（x 114–121）、舵柄（x ≤ 81、y 78–83；轉 ±35° 掃過船尾那幾階）、companion 梯子與梯腳（x 110–121、y 76–84）、lazarette 艙口（x 84–86）之後，
#   放得下病床（4×2 個 0.5 m 格）的只有 z 23（x 122–137）與 z 24（x 100–110）兩階；z 25–27 最大 0.8–1.1 m 寬、在砲 1 號之間或舵柄底下，不標。
#   砲是模型、不是格子 ⇒ 遊戲排床看不到它們 ⇒ 框躲開砲的外框（S1／P1 到 x 99.2、S2／P2 從 x 113.8）。
#   遊戲的門自己從四面牆算（.door 只帶著不用）⇒ x 122 那一面（往梯腳）整面是門、靠門那一欄是走道；X 16 格 ⇒ 3 欄、後兩欄順著 y 放得下病床。
import sys, subprocess

sys.stdout.reconfigure(encoding='utf-8')
step = sys.argv[1]
PRE = 'summit-night-falcon-01m'
CABIN = PRE + '-cabin'
DECK = PRE + '-deck-main'
AT = (60, 44, 18)                       # 子作品框在組裝件的位置（＝ 甲板-主 的座標：甲板-主 在組裝件 0,0,0）
SIZE = (80, 74, 24)                     # 框住整間艙房：x 60–139、y 44–117、z 18–41
ROOMS = [                               # 組裝件座標，含兩端；z ＝ 甲板面上第一層空氣 … 後甲板橫樑底下那一格
    {'name': '1', 'min': (122, 56, 23), 'max': (137, 104, 36), 'note': '艙房最前那一階（斷口艙壁後、梯腳前）1.6×4.9×1.4 m'},
    # z 24 那一階：前後兩頭各差一階（x 99 高一格、x 114 起低一格）⇒ 遊戲的門算法找不到門（它要往外 8 格同一層地板）⇒ 補 .door（往梯腳那一側、z 24 站得住的那一格）
    {'name': '2', 'min': (100, 61, 24), 'max': (110, 99, 37), 'door': (111, 80, 24), 'note': '艙房 z 24 那一階（砲 1 號與 companion 梯子之間）1.1×3.9×1.4 m'},
]
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
    else: cli(['op=work', 'sub=create', 'persona=summit', 'id=' + CABIN, 'title=夜隼號｜艙房（給遊戲的空艙房框，不雕格子）', 'size=' + xyz(SIZE),
               'parent_work=' + PRE, 'tags=sub']); print('建立', CABIN)
    cli(['op=work', 'sub=update', 'persona=summit', 'work=' + CABIN, 'meters_per_voxel=0.1'])
elif step == 'link':
    cli(['op=work', 'sub=link', 'persona=summit', 'work=' + DECK, 'name=艙房', 'source_work=' + CABIN, 'at=' + xyz(AT), 'overwrite=1',
         'meta={"kind":"rooms"}', 'note=空艙房（TASK-0573；造船規格 §9.2）'])
elif step == 'anchors':
    for r in ROOMS:
        for k in [k for k in ('min', 'max', 'door') if k in r]:
            loc = tuple(r[k][i] - AT[i] for i in range(3))
            assert all(0 <= loc[i] < SIZE[i] for i in range(3)), (r['name'], k, loc)
            cli(['op=work', 'sub=anchor', 'persona=summit', 'work=' + CABIN, 'name=%s.%s' % (r['name'], k), 'at=' + xyz(loc), 'overwrite=1',
                 'note=%s（TASK-0573）' % r['note']])
    print('anchors', sum(len([k for k in ('min', 'max', 'door') if k in r]) for r in ROOMS))
else:
    raise SystemExit('步驟？ create|link|anchors')
print(step, 'ok', ok, 'bad', bad)
