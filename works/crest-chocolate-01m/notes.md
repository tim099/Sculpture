巧克力館（TASK-1143）—— 加勒比海那一套第一款 `crest-chocolate-01m-carib-chocolate-house`（Blocksail BUILDING_SPEC §6.36、PRODUCTION §13.11）。

- 產生程式在 design/：chocolate.py（成品）、build.py、apply.py、diag.py（抄自 ridge-two-inn-01m）。改了 chocolate.py ⇒ `python -I -X utf8 -B build.py .` ⇒ `apply.py . create|stamp|anchors|links|models|check`。
- 工具鏈：chocolate.py ⇒ restaurant（trailhead-harbour-01m）⇒ workshops ⇒ quay ⇒ ame-carib-civic-01m 的 harbour／civic ⇒ summit-carib-01m（調色盤、Model、牆、屋頂、部件）；銅色借 workshops2.py 的 COPPER。
- 讀數：框外 0、部件撞格 0、浮空 0（第一版石棍懸空一格 ⇒ 擱到石磨台第二級上）、door_ok；apply check 4 件缺 0 多 0 色差 0、link_overlap 0、link_clipped 0、空腔 0。
- 工作點 7（a 櫃台後、b 石磨台前、c／d 屋裡、f 前廊、g 灶前、e 曬豆架旁）；遊戲照 Blocksail world/townkit/_people.js 的 work 找人（安娜、梅琳）。
- ⚠ 作品資料夾先放了 design/ 再 create ⇒ 被當成「書卡遺失」擋下：先建作品、再放 design/。
