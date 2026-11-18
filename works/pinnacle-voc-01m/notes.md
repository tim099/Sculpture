# 金冠號 —— 荷蘭 VOC 170 呎鏡艉返航船（spiegelretourschip），1660 年代（0.1 m／格）—— 建造筆記

委託：TASK-1317（Tim 2026-11-17 開的 1666 亞洲船批 TASK-1311 子單⑥；2026-11-18 早上自由意志「處理待辦 GO」認領，Tim「先別開始造新船」暫停，同日下午 Tim「TASK-1317 金冠號 開工吧 GO」）：《Blocksail》1666 亞洲船⑥ 荷蘭 VOC 170 荷尺鏡艉返航巨艦。照造船規格雕刻、匯入 Blockside、接進 Blocksail 船型清單。
流程：照 `Ship_Steps` 步驟表（驗收標準就是步驟表），每一步只讀那一行寫的文件。

## 步驟 2 開工前（2026-11-18）

### 座標約定（照藍鯊號，產生程式也從它抄來）
- 空間 1000×320×640；X 船長（船頭 +X）、Y 船寬（中線 ＝ 第 160 格，鏡像 y ↔ 320 − y）、Z 高度（z 0 ＝ 龍骨底面）；P（左舷）＝ y < 160。
- 0.1 m／格（船殼、組裝件書卡都記了 `meters_per_voxel` 0.1）。1 阿姆斯特丹呎 ≈ 0.2831 m ＝ 2.831 格（沿用藍鯊號研究筆記 §1）。
- 框夠不夠：170 呎船殼 ≈ 48.1 m ＝ 481 格；加船首喙、艏斜桅與船尾陽台 ≈ 750 格 < 1000。最寬 ≈ 11.3 m ＝ 113 格 < 320（channels、帆桁轉 60° 也收得下）。主桅頂離龍骨底估 ≈ 55 m ＝ 550 格 < 640。
- 「在不在船裡」：|y − 160| ≤ 半寬（格心判斷）⇒ 兩舷逐格對稱。

### 作品
- 船殼 `pinnacle-voc-01m`「金冠號 船殼」：任務作品（委託 TASK-1317、10 token 已發），`tags=sub`。
- 組裝件 `pinnacle-voc-01m-assembly`「金冠號」：主作品（沒標 sub），parent 船殼；已關聯 `船殼` at 0,0,0。
- 子作品照藍鯊號的拆法（甲板每層一件、梯子、桅、帆桁、裝飾、彈藥庫、舵、錨架…），parent 船殼、`tags=sub`。

### 產生程式
- `design/` 整套從藍鯊號 `gura-pinas-01m/design/` 抄來（上游：收穫號 ← 三叉戟號）；`lines.py` 換成康塞普西翁號 `apex-two-galeon-01m/design/lines.py`（counter、top_curve、stern_tumble、beakhead 都是選用參數；不給的話跟藍鯊號那份逐格相同 —— 早上拿藍鯊號的 plan 當控制組量過）。
- `plan_pinas_ref.json` ＝ 藍鯊號的 plan（對照用）；本船的 `plan.json` 等步驟 3 研究回來照 170 呎重寫。

### 沿用的現有元件（`work sub=components`，2026-11-18 查）
- 砲：風暴角號 12 磅 `summit-stormkaap-01m-gun-12l`（下砲甲板）、6 磅 `summit-stormkaap-01m-gun-6l`（上甲板、船尾樓、追擊）、8 磅 `ridge-two-centurion-01m-gun-8l`；憲法號 18 磅 `basecamp-frigate-constitution-01m-gun-long18`（要的話下砲甲板中段）—— 砲種與門數等步驟 3 研究定案。
- 舵輪＋座 `basecamp-frigate-constitution-01m-wheel`（1660 年代大船多用 whipstaff ⇒ 步驟 11 依史料定案，可能要自己做操舵桿）、羅經櫃 `summit-night-falcon-01m-binnacle`、絞盤 `basecamp-ember-01m-capstan`、小艇 `basecamp-ember-01m-boat`、錨 `basecamp-frigate-constitution-01m-anchor`、火藥桶 `basecamp-frigate-constitution-01m-powder-barrel`、砲門蓋板 `basecamp-frigate-constitution-01m-portlid`、船尾燈 `gura-tridente-01m-lantern`。
- 自己做：船首像（荷蘭船慣例的紅獅子，本船金冠 ⇒ 戴冠的獅）、船尾鏡板（VOC 徽記＋金冠）、船名板、VOC 旗。

## 步驟 3 找資料與新圖紙（2026-11-18）
查證：研究代理讀 Van Dam《Beschryvinge》、Witsen 1671、DAS ⇒ `references/research_voc_2026-11-18.md`（pinnacle 讀過全文）。最重要的兩頁（都對過頁面圖）：**VD p.470** 1660-04-15 Heeren XVII 替三艘返航船定的 charter「170×38×13，koebrugh 5，verdeck 7¼，deurgaande overloop」；**VD p.485** Zeeland 船廠 1660 Walcheren 170×38×13、koebrug 5¼ ⇒ 本船照這份規格。DAS：Walcheren 1661 建、840 ton、1666 出航 288 人。Walcheren 的船尾畫（RMG PAH1782，Van de Velde 父）館藏說明：鏡板上是 **Zeeland 紋章**（戴冠盾、兩個持杖人像），counter 兩面盾 Zeeland／Walcheren ⇒ 步驟 6 的船尾紋章照這個，不畫 VOC 字母組（圖本身步驟 6 再看）。

設計 `design/plan.json`（每個數字的 src：VD／W 原書、或設計決定）；程式改動：
- `layout.py`：甲板 row 可以標 `sheer: true` ⇒ 船樓跟著甲板舷弧（藍鯊號的船樓是平的；本船舷弧往船尾 18 格，平的 halfdek 在船尾那端離 verdeck 只剩 7 格）。
- `draft_lines.py`：原書對照的長度吃 `witsen.length_ft`、首尾柱高可以從龍骨頂量（`heights_from`）、體積沒有原書數字就只讀出來。
- `draft_layout.py`：圖紙標題、galjoen 示意高度、24 磅的顏色。
- `lines.py` 用 `top_curve`（舷頂 smoothstep 落差＋跟甲板一起的舷弧 rise）；**沒有 counter、沒有 beakhead 艙壁**（設計決定：荷蘭鏡艉船是平的 spiegel、heck-balk 以下圓的 billen 收到艉柱 —— 線形的 transom_ratio 已經做出來；船頭是圓船首＋galjoen 平台，步驟 6 做）。

| 項目 | 本船（格 ＝ 0.1 m） | 原書 |
|---|---|---|
| 首柱到艉柱（首尾柱頂 z 91） | 481.2 | 170 呎 ＝ 481.3（VD p.470） |
| 龍骨 | 407.6 | 144 呎 ＝ 407.7（170 − 22 − 4，設計決定） |
| 首柱前傾／艉柱後傾 | 62.3／11.3 | 22 呎（Vrede，W p.111）／4 呎 |
| 最寬（hals x 509、z 54） | 109 | 38 呎外板內 107.6 ＋ 外板（全寬只能是奇數） |
| 舭部寬（龍骨頂上 4.85 呎） | 99 | Grebber 170 呎 × 38 ÷ 42.46 ＝ 99.6（W p.114） |
| 艉橫樑那一層（z 91）的寬 | 71 | heck-balk ⅔ 船寬 ＝ 71.7（W p.66） |
| 設計水線 z 48 的排水量 | 1,595 t | 沒有原書數字（DAS 840 ton 是載貨；Batavia 複製船 ≈ 1,200 t 是小一號的船） |

- 線形參數掃過：bilge_pow 1.8／2.4／3.0／3.6 ⇒ 舭部 93／99／103／105（取 2.4）；transom_ratio 0.72／0.75／0.78 ⇒ 艉橫樑 69／71／75（取 0.75）。其他線形係數沿用藍鯊號（那一組對過 Witsen pinas 的體積）。
- 甲板（hals 的甲板面，從龍骨底量）：koebrug 40、overloop 58、verdeck 79、halfdek 97（到 x 400）、hut 115（到 x 262）、bak 96（x 560–650）；舷弧往船尾 18、往船頭 6（W p.97）；船樓都跟著舷弧。⚠ koebrug 照規格是 42.5、overloop 57.3 ⇒ 遊戲站人要甲板間 18 格 ⇒ koebrug 降 2、overloop 升 1（設計決定）。
- 砲門：overloop 每舷 10（8×7、檻 7；W p.113）、verdeck 每舷 8（7×6、檻 6）、鏡板 2 ⇒ **38 門 ＝ VD p.508 1671 表**（24 磅 4、18 磅 14、8 磅 16、4 磅 4）；主桅兩旁空一格；verdeck 的位置避開三根桅的 channels（步驟 8 再核）。
- 桅：前桅 x 612、主桅 412、後桅 280；長度照 W p.128（160×40 實測）與 VD p.501 × 0.96；主桅頂離水線 43.2 m、前桅 38.2、後桅 29.5；艏斜桅 18.1 m、伸出首柱 ≈ 126 格。帆：前、主桅 course／topsail／topgallant，後桅 lateen（bezaan）＋ kruis 方帆，艏斜桅 blinde ＋ bovenblinde。
- 讀數：船殼牆 543,320 格、1 元件、空腔 0、鏡像差 0；產生程式（draft_lines、draft_layout）重跑兩次逐位元組相同。**反向對照**：`draft_lines.py --probe=half_beam=3` ⇒ 全寬 109 → 115、各站最寬 54 → 57；`draft_layout.py --probe=port=main:5:+3` ⇒ 只有第 4–5、5–6 兩段間距變（26 → 29、60 → 57）。
- 圖紙：`sheet01_lines_v1.png`、`sheet02_layout_v1.png`。

## 步驟 4 船殼落格、砲門、塗裝、船尾窗（2026-11-18）
- 標記 `船殼:begin`（upto=start）→ `tools/stamp_lists.py pinnacle-voc-01m 0 masks/hull/hull_01..03.vox.txt`（250,000 ＋ 250,000 ＋ 43,320，每刀 placed ＝ 清單）→ `船殼:end` → `砲門:begin` → carvevox `masks/ports/carve.vox.txt`（帶刻之前的顏色守門，8,544）→ stampvox overwrite=1 `masks/ports/paint.vox.txt`（38,534）→ `砲門:end`。
- `draft_ports.py` 改：舷牆色帶（lozenge rows）可以給 `dz0`／`dz1` ⇒ 跟著那一層甲板的舷弧（本船船尾翹 18 格，藍鯊號的固定 z 色帶會斜著切過船樓）。
- 塗裝（plan.paint，設計決定 —— 研究筆記 §5，⚠ 沒有原文）：船殼焦油褐 136、腰板黑 36 六道（W p.113：下層砲門下 3 道各 4 格、間隔 5；砲門帶上一道 3；verdeck ＋ 1 一道 3；raa-hout 2）、上層舷牆暗綠 45（verdeck ＋ 4..12、halfdek／hut ＋ 2..10、bak ＋ 2..9）上下金邊、砲門外一圈紅 224、舷頂金；鏡板：kajuit 兩個砲門（8 磅 in de camer）＋三扇窗、halfdek 那一層五扇窗（玻璃 87 那一格先刻掉，步驟 6 做玻璃子作品，清單 masks/glass/stern_glass.vox.txt 240 格）。
- ⚠ 鏡板砲門放 verdeck 那一層：overloop 在船尾 z 75、艉橫樑 z 91 ⇒ overloop 高度的砲門會落在 heck-balk 下面圓的 billen 上（藍鯊號同一個問題）。
- 讀數（作品一律從 CLI 匯出讀）：
  - `tools/check_hull.py mark=船殼:end`：結果帳 作品 543,320 ＝ 設計，缺 0、多 0、色差 0；線形對照 337 點差 0；**反向對照** probe_x=400（那一站 +3）⇒ 只報那一站 22 點、最大差 3。
  - `tools/check_stage3.py mark=砲門:end`：結果帳（船殼 − 刻 ＋ 換色）534,776，缺 0、多 0、色差 0；36 個舷側砲門開口裡實心 0、鏡板 2 個刻穿；**正向對照**（同一把尺量 `船殼:end`）⇒ 36 個全報、鏡板各 49。
  - 引擎 `stats structure=1 mirror=y:160`：1 元件、封閉空腔 0、鏡像差 0。
- 組裝件 `pinnacle-voc-01m-assembly`：關聯 `船殼` at 0,0,0、meta `kind=ship, waterline_z=48`。
- 過程圖：`overlays/step4_hull_{bowq,sternq,side}.png`；圖紙 `design/sheet03_ports_paint_v1.png`。
- 🩸 **步驟 5 開工時才發現：船尾 hut 那一段被切平在 z 129**。`draft_lines.hull_volume` 的高度上限是抄來的「`top` 折線最高 ＋ 2」（127 ＋ 2），本船的舷頂吃 `top_curve` 的 rise、船尾翹到 145 ⇒ 落格的船殼少了船尾頂那一截（draft_decks 鋪 hut 甲板時 z 133 超出陣列才炸出來；步驟 4 的結果帳是「作品＝清單」，清單本身就是切平的 ⇒ 照樣全綠）。修：上限改照 `L.top_max`（吃 top_curve）；`tools/hull_expected.py` 吃 `masks/hull/hull_*.vox.txt` 全部（藍鯊號寫死 01、02）、可帶 `--hull=` 拿舊清單組控制組。
  - 控制組：舊清單組的帳 vs 作品 ⇒ 多 0、少 0、換色 0；新清單（船殼 554,544、塗裝 40,084、刻不變）⇒ `delta_apply`：貼 11,224、換色 207（標記 `船尾舷頂`）；之後 多 0／少 0／換色 0、`check_stage3` 結果帳 546,000 缺 0 多 0 色差 0、36 個砲門實心 0、鏡板 2 個刻穿；引擎 1 元件、空腔 0、鏡像差 0。

## 步驟 5 甲板、梯子、艙房（2026-11-18）
設計 plan.json `decks_build`；產生 `design/draft_decks.py`（照抄藍鯊號，沒改程式）⇒ `masks/decks/<層>.vox.txt`、`masks/ladders/<上面那層>.vox.txt`、`ladder_points.json`、`verify_decks.json`、`sheet04_decks_v1.png`；落格 `design/tools/build_decks.py`。
- 甲板 6 層（子作品 `-deck-{orlop,main,puente,alcazar,toldilla,castillo}`、組裝件關聯 `甲板-<層>`）：koebrug 全長、overloop、verdeck、halfdek（到 x 400）、hut（到 262）、bak（560–650）；艙口三個（後 300–312、主 440–462、前 540–552，閃開後桅 280、主桅 412、前桅 612；都通到 koebrug）；break 四道（halfdek 前緣 x 400、hut 前緣 262、bak 後緣 560、bak 前隔板 650：艙壁兩扇門＋7 格胸牆，前隔板暗綠底金框）；桅孔照傾斜軸線。
- 梯子 9 座（子作品 `-ladders-<上面那層>`，關聯 `梯子` meta `kind=ladders`，固定點 `<梯名>.foot／lo／hi／head`）：koebrug→overloop（左舷 dy −14、x 340）、overloop→verdeck 後（x 345）前（x 480）、verdeck→halfdek 兩舷（x 420，頭 397）、halfdek→hut 兩舷（x 283，頭 259）、verdeck→bak 兩舷（x 543，頭 563）。每一層都有梯子通到（verify_decks.reach）。
- 甲板 meta：每層子作品 `export format=vxk links=none` ⇒ Blockside `src/decks.py` ⇒ `design/decks_meta.tsv`（name 換成 plan 的中文名）⇒ `work sub=meta`（6 條）：level 0 koebrug、1 overloop、2 verdeck、3 bak、4 halfdek、5 hut。
- 艙房：沒隔（同藍鯊號）；之後要配功能艙再加。
- 讀數：設計那一側：重疊 0、砲門往艙裡被擋 0、梯子點問題 0、封閉空腔 0、鏡像差 0（overloop 634 ＋ 梯子 488 ＝ koebrug 梯子靠左舷的井，照實）；`tools/check_decks.py`（每件從匯出讀）：11 件 203,992 格，缺 0、多 0、色差 0、跟船殼／彼此重疊 0；梯子點（組裝件 parts，遊戲讀的那一份）36／36、跟設計差 0、空氣／腳下／頭頂 14 格問題 0；組裝件 1 元件、空腔 0、link_overlap 0。**反向對照**：`draft_decks.py --probe=drop_ladder=castillo-S` ⇒ 8 座、bak 只剩 castillo-P（不寫檔）。
- 預覽 preset：`藏船殼`。過程圖 `overlays/step5_decks.png`。

## 步驟 6 裝飾、窗的玻璃（2026-11-18）
- **船頭走道**（plan.ports.bow_gangway，同藍鯊號船頭 v2）：艏柱上緣中線刻一道 9 格寬的缺口（dy ≤ 4、z 86 起）⇒ bak 前隔板的門外（露天的 verdeck x 651–665）跨過艏柱直接走上 galjoen 平台。船殼走差量（`draft_ports.py` ⇒ `tools/hull_expected.py` ⇒ `delta_apply`，標記 `船頭走道`）：刻 603、換色 39（缺口邊描金）；船頭補實 0 格（x ≥ 666 船殼裡沒有空的格）。
- `draft_deco.py` 照藍鯊號（galjoen v2、獅子、船尾走廊、側廊 v2、hackebort），改：船頭／船尾的範圍（藍鯊號寫死 470／210／400 ⇒ 600／260／560）、走廊與側廊的「藍」換成上層舷牆的暗綠 45、獅子放大（plan.figurehead.k 1.25；es 的金柱高度跟著 k —— 第一次沒跟 ⇒ 金柱插進獅身 3 格、figurehead 與 galjoen 重疊 3）、紋章改吃 `hackebort.emblem`、字型加 G O D N K R、圖紙的範圍。
  - `-galjoen`「船首喙」22,635：平台頂 z 89（verdeck ＋ 4）往前升 10、喙尖 x 743；knee 從首柱 z 25 填到平台底（水線下同船底色）；兩道 cheek 夾暗綠金點 kam；每側 3 條 regelingen（平台上 1／4／7 起）、4 根 knies、mans hooft、cathead（bak 前角 z 108）、獅背上的 es。
  - `-figurehead`「船首像」1,636：**戴冠紅獅**（11 呎 ＝ 31 格，x 717–747，金鬃金冠）。
  - `-stern-deco`「船尾裝飾」12,049：船尾走廊（halfdek 那排窗下 z 118、伸出 6、扶手 7）＋兩舷側廊（x 189–216、z 100–132、銅頂 168；窗是真玻璃，後面刻穿到艙裡）。
  - `-hackebort`「hackebort」2,242：鏡板頂 z 146–166、奶油底金邊拱頂；**Zeeland 紋章（金底紅獅、藍白波紋）＋金冠**、暗綠名帶 GOUDEN KROON 金字（研究筆記 §5：Walcheren 船尾畫的 tafferel 是戴冠盾的 Zeeland 紋章；荷文船名是設計決定）⇒ 這一件鏡像差 180 照實報；拱頂正中一盞船尾燈（模型 `lantern`，三叉戟號船尾燈 scale 0.5、kind=light）。
- **窗的玻璃**：鏡板窗 240（draft_ports）＋側廊窗 240（draft_deco）⇒ 子作品 `-stern-glass`（480）、組裝件關聯 `船尾窗玻璃` meta `material=glass`；側廊窗後面的船殼刻 960（`tools/hull_expected.py` 的「側廊窗洞」，標記 `側廊窗洞`）；240 個窗洞全部通到艙裡。
- 能隱藏的裝飾（deco=1）：本步驟的件都是關聯（格子是船的一部分）、燈是 kind=light ⇒ 沒有要標 deco 的模型（同藍鯊號）。
- 讀數：`tools/check_stage5.py` 四件結果帳缺 0／多 0／色差 0；設計那一側跟船重疊 0、部件之間重疊 0、跳過 0、艏斜桅那條線被擋 0；船殼差量之後 多 0／少 0／換色 0；組裝件 1 元件、空腔 0、link_overlap 0、models_broken 0。**反向對照**：`draft_deco.py --probe=shift=figurehead:3` ⇒ 獅子鏡像差 0 → 1,530。產生程式重跑兩次逐位元組相同（落格之後組裝件多了玻璃 ⇒ verify 的「貼著船的格數」跟落格前那一次不同，清單本身不變 —— check_stage5 0 差）。
- 過程圖：`overlays/step6_{bow,stern}.png`；圖紙 `design/sheet05_deco_v1.png`。⚠ 鏡板中段（走廊頂到 hackebort 底，z 132–145）還是素面褐色 —— 先放著（同藍鯊號）。

## 步驟 7 桅與帆桁（2026-11-18）
設計 plan.json `rig_build`（長度與位置在 `masts`）；產生 `design/draft_masts.py`（照抄藍鯊號，只改圖紙的框）；落格 `design/tools/build_masts.py`。
- 桅（每根一件子作品，關聯 `前桅`／`主桅`／`後桅`／`艏斜桅`）：前桅 11,627、主桅 13,260（下桅＋桅樓＋中桅＋十字架＋上桅）、後桅 5,149（下桅＋桅樓＋kruissteng）、艏斜桅 5,481（含斜桅頂桅）。桅樓半徑 前 18、主 20、後 13（W p.94 規則）；桅腳半徑 3.5（甲板桅孔 4）。
- **桅的綁定**（Ship_Masts §5，TASK-1169）：四條關聯 meta `kind=mast`＋`mast=fore／main／mizzen／bowsprit`（藍鯊號造的時候還沒有這條規則，build_masts 沒標 ⇒ 用 `work sub=meta file=` 補）；帆桁 meta 的 mast 一字不差對到。
- 艏斜桅腳在 bak 甲板（x 622、z 102，30°）⇒ 從船頭舷牆上面過去，船殼開孔 0 格。
- 帆桁 10 根（外部模型，掛在各自的桅子作品）：方帆桁 9 根沿用憲法號的帆桁元件、只沿長度縮放（主帆桁 25.5 m ← fore-course、前 22.9 ← mizzen-crossjack、主中桅 13.6／前中桅 12.3 ← fore-topgallant、主上桅 7.9 ← fore-royal、前上桅 7.1 ← mizzen-royal、後中桅 7.9 ← fore-royal、斜桅帆桁 13.6 ← fore-topgallant、斜桅頂帆桁 6.0 ← mizzen-royal）；三角帆桁 1 根新做 `-yard-mizzen-lateen`（20.95 m、40°、吊點前端往後 40%；meta yard=gaff、rig=lateen）。方帆的下帆桁都是 course（沒有 boom）。
- 讀數：`tools/check_stage6.py` 桅 4 件＋三角帆桁結果帳缺 0／多 0／色差 0；船殼 544,437 ＝ 設計（孔 0）0 差；帆桁模型 10 根 meta 與來源固定點問題 0；帆桁穿船 10 根全 0；三角帆桁後端伸出船尾 0.86 m；models_broken 0（畫 11 個模型）；組裝件 1 元件、空腔 0、link_overlap 0。跳過的格：前桅腳插進船頭 deadwood 46、艏斜桅腳壓到 bak 甲板 29（同藍鯊號，桅坐在船上）。**反向對照**：`--probe=pivot=yard-main-course:-150`（放到船殼的高度）⇒ 只有那一根報 62 格。產生程式重跑兩次逐位元組相同。
- 過程圖：`overlays/step7_masts.png`、`design/sheet06_masts_v1.png`。
