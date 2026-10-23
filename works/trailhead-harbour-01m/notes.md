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

## 第三批（TASK-0847，2026-10-23）
Tim「繼續增加城鎮的共用建築吧 GO」⇒ 魚市、瞭望塔（common）、監獄、小教堂（carib）。產生程式 `design/town3.py`（import quay.py），build.py 的 MODULES 加了它。
- 讀數：魚市 38,100（棚架 12,900、屋頂 25,200）；瞭望塔 36,056（塔 30,688、遮陽頂 5,368）；監獄 136,540（屋與院 121,048、屋頂 13,224）；小教堂 35,874（牆 19,720、屋頂 16,154）。四件浮空 0、部件撞格 0；引擎 check 12 件缺 0 多 0 色差 0。
- Blocksail：`common-fish-market`、`common-watchtower`、`carib-jail`、`carib-chapel`。

### 坑（第三批）
- 瞭望塔的上下口在立梯子之後才挖 ⇒ 梯子在平台上面那一截（扶手）跟下面斷開、兩段各 8 格浮空 ⇒ 先挖洞再立梯子。
- 門框的部件腳落在地板那一層 ⇒ 部件撞格 10 ⇒ 擺完部件把 z 0 那一層讓給門框。
- 小教堂門前有十字 ⇒ townmodels 自動補的門口燈挑「往外空得最遠」的一邊、挑到屋裡 ⇒ 自己掛燈籠。
