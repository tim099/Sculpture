"""Freeze the two-warning handoff; work notes are updated through sculpture CLI."""
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'delivery'
PREVIEW = Path('D:/Unity/Valhalla/scratchpad/sirius-tidegrave/task0603/manual-preview')
SCRATCH = PREVIEW.parent
BASE = 'sirius-tidegrave-01m'
report = (PREVIEW / 'reports/shipcheck_tidegrave.md').read_text('utf8')
assert '**✗ 0　⚠ 0**' in report and '54／54' in report
debug = json.loads((SCRATCH / 'remaining_warnings/accepted_debug.json').read_text('utf8'))
assert not debug['issues']
assert sum(c['role'] == 3 for c in debug['debug']['crew']) == 12
production = Path('D:/Unity/Valhalla/Blockside/src/js/23_powder.js').read_text('utf8')
candidate = (PREVIEW / 'src/js/23_powder.js').read_text('utf8')
def walker(text):
    return text[text.index('function monkeyTo('):text.index('\nfunction stepMonkey(')]
assert walker(production) == walker(candidate), 'Intentional walking shortcuts must stay unchanged'
assert 'R.debug =' not in (PREVIEW / 'index.html').read_text('utf8')

geo = json.loads((ROOT / 'service_access_20261016/geometry_report.json').read_text('utf8'))
asset = OUT / 'tidegrave_import_20261016.vxk'
assert hashlib.sha256(asset.read_bytes()).hexdigest() == geo['sha256']
archive = OUT / 'import_manifest_20261015.json'
if not archive.exists():
    shutil.copy2(OUT / 'import_manifest.json', archive)
manifest = dict(geo, observedAtUtc=datetime.now(timezone.utc).isoformat(),
                work=BASE + '-assembly', delivery=str(asset), parts=17,
                errors=0, warnings=0, marines=12, powderReachable=54, guns=54,
                actorWalkingUnchanged=True,
                status='Author candidate verified. Formal game import owned by ame; cloth dynamic acceptance remains manual.')
(OUT / 'import_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), 'utf8')
shutil.copy2(PREVIEW / 'reports/shipcheck_tidegrave.md', OUT / 'shipcheck_tidegrave.md')
shutil.copy2(PREVIEW / 'MANIFEST.json', OUT / 'game_integration/preview_manifest.json')
shutil.copy2(Path('D:/Unity/Valhalla/ChatTavern/baton/letters/Sirius/cmd/sculpture_stats.md'),
             OUT / 'stats_import_20261016.md')
evidence = dict(info=debug['info'], errors=0, warnings=0, marines=12,
                crewConfig=debug['debug']['crewConfig'], actorWalkingUnchanged=True)
(OUT / 'game_integration/acceptance_20261016.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2), 'utf8')

summary = '''# 2026-10-16 潮墓號：兩項匯入警告已清除

隔離最新遊戲正式 shipcheck：0 errors / 0 warnings，陸戰隊12/12、353船員、54砲全滿編、
送藥取用點到砲尾54/54連通。build與verify通過。正式Blockside仍由ame接入。

對稱艏砲側通道X574..581、Y94..103及137..146、淨空Z117..134；補地板Z115..116。
經sculpture CLI移除1152格、補176格，成船1033347格/checksum55c4e759。
CLI/VXK逐格逐色差0、水線以下不變，原502繩/10帆/168模型/25mesh及固定帆點逐值不變。
交付delivery/tidegrave_import_20261016.vxk，
SHA256 850566c50d4b7b022f3124ec88e36a6154b672ad7201ef44ce9602da1a43322b。

配套game_integration/23_powder.patch修艏艉砲送藥手出生與交藥點至砲尾後方；
suggested_ship.json設marines=12、marineGap=30並保留geo。補丁只套隔離版。
Tim明確說穿過前桅、跨過艙口不用處理，部分細節故意節省效能；保留原monkeyTo，
不提交額外逐格導航或人體碰撞限制。此處連通驗收依現行遊戲標準，未擴大成逐步碰撞驗收。

TASK-0603/0546帆碰撞仍依Tim先前選擇手動驗收；本次不代簽完整動態PASS。
最新交付取代20261015版本；歷史初建腳本不可在成船盲跑。
'''
todo = '''# 正式遊戲接入

- ame採用delivery/IMPORT.md、20261016 VXK、23_powder.patch與suggested_ship.json，正式匯入並重建驗證。
- 保留Tim指定的走路效能取捨；不修穿過前桅或跨艙口。
- Tim手動驗收帆碰撞，TASK-0603/0546不因匯入檢查通過而代簽。
'''
(OUT / 'author_progress.md').write_text(summary, 'utf8')
(OUT / 'author_todo.md').write_text(todo, 'utf8')
for work, label in ((BASE, 'hull'), (BASE + '-assembly', 'assembly')):
    notes = ROOT.parent.parent / work / 'notes.md'
    old = notes.read_text('utf8')
    if '# 2026-10-16 潮墓號：兩項匯入警告已清除' not in old:
        latest = OUT / ('notes_' + label + '.md')
        latest.write_text(summary + '\n---\n\n' + old, 'utf8')
        subprocess.run(['D:/Unity/Senate/publish/senate.exe', 'cmd', 'sculpture',
                        '--arg', 'op=work', '--arg', 'sub=update', '--arg', 'persona=Sirius',
                        '--arg', 'work=' + work, '--arg-file', 'notes=' + str(latest),
                        '--arg-file', 'todo=' + str(OUT / 'author_todo.md')], check=True)
checkpoint = ROOT / 'CHECKPOINT.md'
if summary.splitlines()[0] not in checkpoint.read_text('utf8'):
    checkpoint.write_text(summary + '\n---\n\n' + checkpoint.read_text('utf8'), 'utf8')
(ROOT.parent / 'journal/20261016_service_access.md').write_text(summary, 'utf8')
plan_text = (ROOT / 'plan.json').read_text('utf8')
plan = json.loads(plan_text)
service = dict(portals={'x':[574,581], 'y':[[94,103],[137,146]], 'z':[117,134]},
    floor_z=[115,116], removed=1152, added=176, evidence='service_access_20261016/geometry_report.json',
    actor_walking='Original game shortcuts retained per Tim; foremast and hatch crossing out of scope.')
if 'service_access_20261016' not in plan:
    plan_text = re.sub(r'"revision":\s*8', '"revision": 9', plan_text, count=1)
    pos = plan_text.rfind('}')
    plan_text = plan_text[:pos].rstrip() + ',\n  "service_access_20261016": ' + json.dumps(service, ensure_ascii=False) + '\n}\n'
    json.loads(plan_text)
    (ROOT / 'plan.json').write_text(plan_text, 'utf8')
print(summary)
