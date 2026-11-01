# 好旅號 TODO（TASK-1151；續作先讀 notes.md，再 `senate cmd task --arg op=check --arg persona=summit --arg index=1151` 看下一個沒勾的步驟）
- 下一步：步驟 14 匯進 Blockside（讀 Ship_Game §9／§9.4／§12、Ship_Render）。照信風號的做法（erina-tradewind-01m notes「步驟 14」）：
  1. Blockside 自己的 worktree（從 refs/heads/dev 開；`_cache` 先從共用的複製過去 —— 記憶 blockside-worktree-cache-before-dump）。
  2. `python -I src/admin.py import --work summit-boaviagem-01m-assembly --id boaviagem --name 好旅號` → `ids` → 看匯入檢查（shipcheck）✗ 0、樓梯自檢 ✗ 0 → 修 ⚠ → `reimport`。
  3. 🩸 import 會把整份 game.json 重 dump ⇒ 拿 HEAD 只插好旅號那一筆（記憶 blockside-import-reformats-config）；填 ships[boaviagem]（role merchant、geo、crew…，高度在 notes 最後一節）、idNext 補 gun／gunmount（砲的 id 是 draft_guns 先發的）。
  4. `admin.py build` 重建、srccheck；worktree 提交；合併回 dev 時才開 coding 場；推 dev 前在獨立的 call 列 `dev/dev..heads/dev`。
- 然後：步驟 15 交船（Ship_Game §10 檢查表）；接進 Blocksail FLEET.types（新 key、hull boaviagem、hullLoa 照實量；誰用、要不要 from／開場：Tim 定）；fleet_check 前後對照。
