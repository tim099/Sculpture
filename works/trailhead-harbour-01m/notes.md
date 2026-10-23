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

## 第四批（TASK-0853，2026-10-23）
Tim「那繼續加建築吧 GO」⇒ 盤點六座城還沒有模型的地塊 ⇒ 碉堡（四角稜堡 carib 毛石、en 磚）、英國砲台。產生程式 `design/forts.py`。
- 讀數：fort 759,007（堡與操場 746,971、屋頂 10,288）；fort-en 764,143；battery-en 72,226。浮空 0、部件撞格 0；引擎 check 9 件缺 0 多 0 色差 0。
- Blocksail：`carib-fort`、`en-fort`、`en-battery`；遊戲裡皇家港 en-fort 1、en-battery 3。
- 沒做共用版：加拉塔 1453 的 Kastellion 也是 fort，退路會拿到稜堡（年代不對）。

### 坑（第四批）
- 門洞的鋪地從牆外 2 格起鋪 ⇒ door 那一格被鋪地佔掉、door_ok false ⇒ 鋪地從牆外那一線起。
- 土台實心 ⇒ 一座 1.4 M 格 ⇒ `civic.hollow` 只留外面 6 格的殼（約 75 萬格）。

## 海戰 meta（2026-10-23，Tim「堡壘之後打算做入海戰」「堡壘用的炮可以跟船互通」）
- 堡壘一律拆層：站人放砲那一層 kind=deck、火藥庫 kind=magazine（固定點 blast、door；裡面憲法號的火藥桶 kind=powder）、砲用船上同一件元件 kind=gun gun=<代碼> 掛在甲板那一層；牆身那一條照舊 kind=building。Blocksail BUILDING_SPEC §5.3。
- build.py 多了 layer_meta、layer_anchors、layer_models、mpv（apply.py 照 mpv 設 meters_per_voxel）。第四批的碉堡、砲台照這一套重做了一次。

## 第五批（TASK-0861，2026-10-23）
- 加拉塔堡 kastellion（genoa，0.2 m）461,619 格；修院 convent（carib）44,858 格。產生程式 design/castle.py。
- 生命之泉修道院不做（kaguya 在做 kaguya-cpl-pege-1453）。

### 坑（第五批）
- 城門鐵柵的底那一道橫條照拱頂一格一格跟著降 ⇒ 拱邊的兩格斷開浮空 ⇒ 只留直條（頂端插在拱裡）。
- 小堂山牆上的十字照固定高度放 ⇒ 屋脊比它低、浮空 56 格 ⇒ 照屋頂高度場放。
- put_part 只挖 body／gallery ⇒ 火藥庫拆成自己一層後門洞要自己挖。
