"""Record the tested import handoff; authored work notes are written via CLI."""
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from build_structure import cli, BASE

OUT = ROOT / 'delivery'
PREVIEW = Path('D:/Unity/Valhalla/scratchpad/sirius-tidegrave/task0603/manual-preview')
report = (PREVIEW / 'reports/shipcheck_tidegrave.md').read_text('utf8')
assert '**✗ 0　⚠ 2**' in report
shutil.copy2(PREVIEW / 'reports/shipcheck_tidegrave.md', OUT / 'shipcheck_tidegrave.md')
shutil.copy2(PREVIEW / 'MANIFEST.json', OUT / 'game_integration/preview_manifest.json')
shutil.copy2(Path('D:/Unity/Valhalla/ChatTavern/baton/letters/Sirius/cmd/sculpture_view.md'), OUT / 'view_import_20261015.md')
manifest = json.loads((OUT / 'import_manifest.json').read_text('utf8'))
summary = f'''# 2026-10-15 潮墓號：遊戲匯入交付

Tim要求完成造船至可加入遊戲，並通知ame。作者側已補左右共用bower錨、短索與hawse，
錨後移2m避開艏砲班的模型外框。原船體1034323格/d931433f、十帆及固定帆點保留。
最終502繩/10帆/168模型，broken全0；結構1元件/0空腔/鏡像0/關聯重疊裁切0。

交付 {manifest['delivery']}
SHA256 {manifest['sha256']}
0.1m格，水線52，54砲、6甲板、7梯、兩庫各24桶/2400lb。
重匯兩次除exported_at外內容相同；VXK/CLI逐格逐色0差，一格負向可失敗。
這不是所有歷史階段的乾淨初建重跑聲明。

隔離最新遊戲：0 errors / 2 warnings、54砲全滿編、352船員、左右錨/ring/hawse。
配套game_integration/23_powder.patch修艏艉砲送藥手誤生在甲板外的砲口X；舷砲不變。
suggested_ship.json提供geo。未改ame正式遊戲工作樹，需ame覆核採用、匯入及重建。
兩警告保留：陸戰隊11/12，chase-2送藥路徑尋路格不連通（現走直線）。

ame已接手帆物理並提交ebd55ff；TASK-0603/0546按Tim選擇維持手動動態驗收，
不把匯入成功當作穿帆全過。已知自由布接觸與凍結證據保留在design/task0603。
最新圖Rev08、overlays/import_bow_20261015.png；正式匯入說明design/delivery/IMPORT.md。
'''
(OUT / 'author_progress.md').write_text(summary, 'utf8')
todo = '''# 遊戲接入與手動驗收

- ame按delivery/IMPORT.md與import_manifest.json匯入tidegrave，覆核隔離版23_powder補丁與geo配置。
- 正式匯入後重跑verify/shipcheck，處理陸戰隊11/12及chase-2取用點的路徑警告。
- Tim手動驗收帆碰撞；TASK-0603與0546最後一格不冒簽，依具體失敗續修。
- 歷史初建腳本不可在成船盲跑；目前只保證凍結匯出與逐格回讀，不宣稱乾淨重造全過。
'''
(OUT / 'author_todo.md').write_text(todo, 'utf8')
for work in (BASE, BASE + '-assembly'):
    notes = ROOT.parent.parent / work / 'notes.md'
    old = notes.read_text('utf8') if notes.exists() else ''
    latest = OUT / ('notes_' + ('assembly' if work.endswith('-assembly') else 'hull') + '.md')
    latest.write_text(summary + '\n---\n\n' + old, 'utf8')
    # Long fields use --arg-file rather than shell interpolation.
    import subprocess
    args = ['D:/Unity/Senate/publish/senate.exe', 'cmd', 'sculpture', '--arg', 'op=work',
            '--arg', 'sub=update', '--arg', 'persona=Sirius', '--arg', 'work=' + work,
            '--arg-file', 'notes=' + str(latest), '--arg-file', 'todo=' + str(OUT / 'author_todo.md')]
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)
checkpoint = ROOT / 'CHECKPOINT.md'
checkpoint.write_text(summary + '\n---\n\n' + checkpoint.read_text('utf8'), 'utf8')
journal = ROOT.parent / 'journal'
journal.mkdir(exist_ok=True)
(journal / '20261015_game_import.md').write_text(summary, 'utf8')
print(summary)
