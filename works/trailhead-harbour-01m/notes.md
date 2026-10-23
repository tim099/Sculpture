# 港口配套第二批（共用 common）—— trailhead

委託：Tim 2026-10-23（TASK-0843）「幫忙加上一些城鎮公共建築吧(加勒比海地區的風格)」「另外可以先加上港口建築 例如起重機等」；
Tim 選：起重機照舊用起重架（sheers）、這一批做起重架與船棚、加進生成器的開場擺放。

## 作品怎麼拆
- 任務作品 `trailhead-harbour-01m`（只是根，一格都不雕）。
- 成品 `-sheers`（起重架，10 × 10 m，框 100×100×130）＝ 關聯 `-sheers-body`；`-boat-shed`（船棚，8 × 14 m，框 80×140×70）＝ `-boat-shed-body`＋`-boat-shed-roof`。
- 成品 meta：`kind=building`、`use`、`style=common`、`lot`、`base=4`、`variant=a`（build.py 寫）。

## 產生程式（`design/`）
- `quay.py`：兩件的形制；import `ame-carib-civic-01m/design/harbour.py`（再往下是 civic.py ⇒ summit-carib-01m 的 carib.py、kit.py）。
- `build.py`、`apply.py`：抄自 ame 那份，根換成本作品、persona 換成 trailhead。
- 跑：`python -I -X utf8 -B build.py .` ⇒ `apply.py . create|stamp|anchors|links|models|check`。

## 讀數（2026-10-23）
- 起重架 8,521 格、元件 2（起重架本體＋地上的繩盤）、浮空 0；船棚 39,548 格（棚架 17,428、屋頂 22,120）、元件 4、浮空 0。
- 引擎 check：5 件缺 0 多 0 色差 0、link_overlap 0、link_clipped 0。
- Blocksail：`common-sheers`、`common-boat-shed`（tools/townmodels.py）。

## 坑
- 斜的繩只有角碰角 ⇒ 一格一格算成浮空：`rope_line` 換格時一次只動一軸（六連通）。
- 貨網上層畫成棋盤格 ⇒ 20 個單格浮空 ⇒ 只留網底與網邊。
- 龍骨墊木放在兩條滑道中間 ⇒ 懸空 ⇒ 改成橫跨兩條滑道。
- 沒有牆的建築沒放燈籠 ⇒ townmodels 會在門口自動補燈、懸在半空 ⇒ 起重架自己掛一盞在穩索樁上。
