# 凍結重跑

整個資料夾可複製到另一個位置。核心後驗只需 Python＋numpy、Node；不需要 Senate CLI、作品事件、作者程式或遊戲工作目錄。

`snapshots/final_heads.vxk` 為最終輸入原件，SHA256 `76d945aca4f55556f5b952b7a5a3b4183cbe00a6f1b9d44f7359a56fd3bc5036`。`frozen_yards.json` 保存十桁的實心 cubes、pivot、at、r0、meta，每件附來源事件 SHA256、placement models.json SHA256；這是當時直接重播的結果，不會再讀未來的同名事件。`frozen_game/` 保存完整當時 10_ship.js／21_gunnery.js／30_rig_physics.js，`provenance.json` 帶原始絕對路徑、bytes、SHA256、實際函式索引與 brace 常數。

在本資料夾開 PowerShell：

```powershell
$env:VERIFY_FROZEN='1'
$env:VERIFY_VXK=(Resolve-Path ./snapshots/final_heads.vxk).Path
python ./check.py
node ./bind.js
python ./cloth.py
```

順序為 body/十桁索具取樣、真遊戲綁端、完整靜態布面與 sheet/robband。`bind.js` 讀剛產生的 header.json，並從 frozen_game 執行 meshOcc/yardNear；check.py 在 frozen 模式完全跳過活作品 models/events。brace 角度範圍按凍結原始 30_rig_physics.js 的常數使用，check.py 內明寫的 `.70/1.40` 對應該快照，不隨未來遊戲變更。

也可重跑增量表與舊索具負向對照：

```powershell
python ./final_audit.py
python ./negative_cloth.py
```

注意：該命令在 VERIFY_VXK=final_heads 下，輸出 final_audit.json 的 source 會是 final_heads，delta 基準仍是當時 after_robbands_header.json。封存原本的 final_audit.json/heads_audit.json 有各自明確 source；如需保留原檔，先複製整個資料夾再重跑。負向對照改讀 snapshots/old_source_after.vxk。

`heads.py`、`freeze.py` 是建置封存當時用的輔助程式，未列入可攜重跑入口；尤其 freeze.py 是**重新凍結活來源**，不應在重跑證據時執行。`MANIFEST.json` 遞迴列出封存所有檔案 bytes／SHA256。腳本會把結果寫回腳本所在資料夾。

上述重跑仍只有 REPORT.md 清楚列出的範圍，不能升格成全船所有繩與自由布的連續動態驗收。
