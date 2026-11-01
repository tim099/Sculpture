小飯館（TASK-1144）—— 加勒比海那一套第一款 `trailhead-cookshop-01m-carib-cookshop`（Blocksail BUILDING_SPEC §6.37、PRODUCTION §13.9）。

- 產生程式在 design/：cookshop.py（成品）、build.py、apply.py、diag.py（抄自 crest-chocolate-01m）。改了 cookshop.py ⇒ `python -I -X utf8 -B build.py .` ⇒ `apply.py . create|stamp|anchors|links|models|check`。
- 工具鏈：cookshop.py ⇒ restaurant（trailhead-harbour-01m）⇒ workshops ⇒ quay ⇒ ame-carib-civic-01m 的 harbour／civic ⇒ summit-carib-01m（調色盤、Model、牆、屋頂、部件）；魚的兩色借 town3.py（魚市）、磚色借 apex-one-industry-01m 的 industry.py。
- 設計重點：跟餐廳分開 —— 小一號（屋 7.2 × 4.4 m）、沒有前廊；正面一個 3.6 m 寬的窗口、櫃台伸出牆外、撐起來的木板遮陽 ⇒ 臨街賣熟食（bodegón／cook-shop）。後院圓頂磚爐（烤魚派）、burén（烤木薯餅）、殺魚桌、曬魚架。
- 讀數：框外 0、部件撞格 0、浮空 0、door_ok（第一版就過）；apply check 4 件缺 0 多 0 色差 0、link_overlap 0、link_clipped 0、空腔 0；組好 49,038 格。
- 工作點 7（a1／a2 窗口櫃台後、b 做派長桌、c 炭盆前、d 烤爐前、e burén 旁、f 殺魚桌）；遊戲照 Blocksail world/townkit/_people.js 的 work 找人（梅琳、安娜）。
