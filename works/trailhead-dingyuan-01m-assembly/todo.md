# 定遠號 TODO

- [ ] Blockside 分支 `trailhead/dingyuan-guns`（211d32f 砲種表 305k／150k／h37、2fa7eb7 送藥手退路）合進 dev：2026-10-21 合併前讀 scp-coding skill 失敗（文件庫撞名 RENDER_PLAN／RENDER_PLAN_DETAIL／README），照規矩停在這裡。worktree 在 trailhead 的 scratchpad `bs_dingyuan`。dev 在那之後到 94df804 ⇒ 合之前在 worktree 合 dev、照合併後的來源重建 index.html。
- [ ] 要不要把定遠號匯進遊戲（Tim／ame 決定）：暫存匯入的差在 `references/blockside_import_2026-10-21.diff`（⚠ 裡面 game.json 有 import 重排的雜訊，只取定遠號那一行）、報告 `references/shipcheck_2026-10-21.md`（ships[] 那一行、ship_cards、vxk_lock、template）；匯入後跑 `admin.py ids --id dingyuan`、填 geo 與 cfg.base（notes「給遊戲那側」）。
- [ ] 艉、艏 15 cm 砲塔：取用點在砲塔圈裡、送藥手站在圈外 ⇒ 照直線送（⚠）。要乾淨：砲塔裡放備便彈藥箱（kind=magazine，哨兵號的做法）或遊戲那側讓送藥手從艙口梯上去。
- [ ] 艙房（kind=rooms）沒做：艉樓、艏樓裡只有前後壁。要醫療艙之類的再隔。
- [ ] 飛橋甲板只有中線與海圖室底下的撐柱（兩座主砲轉起來會掃到舷邊的柱）—— 看起來懸臂很長，可以加斜撐。
- [ ] 錨吊在船頭外板旁（史料：錨床在艏樓兩舷 79–83 m）—— 放在甲板上會擋主砲往前的砲線；之後可以做錨床。
