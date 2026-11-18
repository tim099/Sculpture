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

- **補：艙底梯**（2026-11-18 下午，Tim「目前沒有通往底艙的梯子」）：draft_decks 搬康塞普西翁號（TASK-1028）的 `lo: hold` 那兩段（梯腳踩艙底 ＝ 梯腳那一柱內板頂；梯井 `well_a／well_b` 只開上半段）；plan `decks_build.ladders` 加 `hold`（中線、梯腳 x 396、往船尾爬 11 階、頭 x 368 站上 koebrug；理由在 `hold_src`）⇒ 新子作品 `-ladders-orlop`（326 格，關聯 `甲板-orlop/梯子` kind=ladders、固定點 hold.foot／lo／hi／head）、koebrug 刻梯井（delta_apply：刻 242、貼 90）。讀數：設計那一側重疊 0、梯子點問題 0、其他五層甲板清單沒變；`check_decks.py` 12 件缺 0／多 0／色差 0、問題 0；梯子點 40／40、跟設計差 0、頭頂 14 格問題 0；組裝件 1 元件、空腔 0、link_overlap 0。

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

## 步驟 8 索具、帆、旗（2026-11-18）
設計 plan.json `rigging`；產生 `design/draft_rigging.py`（照藍鯊號，改：channel 的高度可以指定照哪一欄的舷頂 `channels.z_at`、船尾旗的字吃 `flags.text`、ensign 標 `nation`）⇒ `masks/rigging/channels.vox.txt`、`rigging_plan.json`、`textures/ensign.png`、`verify_rigging.json`；套用 `design/tools/rigging_apply.py`（3 分鐘）。
- **channels**（`-channels`，關聯 `支索板`，兩舷一件）2,540 格：每舷 shrouds 前 7、主 8、後 5（＋中桅 backstay 前、主各 1；藍鯊號 W 的 6／7／4 各加一根，⚠ VOC 規格沒寫）、間距 6。
  - 主桅後傾 4° ⇒ 桅頂在 x ≈ 396；shrouds 從 x 398 往後排到 350、落在 halfdek 的舷牆外 ⇒ channel 高度照 x 380 的舷頂（z_at）；後桅從 x 262 往後、照 hut 舷頂（x 250）。照桅位那一欄的舷頂 ⇒ channel 在船腰高度、支索穿過高的船樓舷牆（藍鯊號主桅那一排撞過的坑）。前桅整排在 bak 上（609–567）。
- 固定點 149、繩 125（shrouds 40、中桅 shrouds 18、futtock 18、上桅 shrouds 8、backstays 4、stays 8、艏斜桅 4、帆自己的繩 25）；ratlines 用橫繩組 12 組（每根桅 lower／topmast × 兩舷），下桅 6 組 `climb=1` 繩梯（落腳點站得住：climb_bad 0）。
- 帆 12：前／主 course、topsail、topgallant（bramzeil）、後中桅帆 kruiszeil、後桅三角帆 bezaan（clew 在 hut 上方、sheet 綁 hut 兩舷舷頂、tack 綁 halfdek）、斜桅帆 blinde、斜桅頂帆 bovenblinde、船尾旗（荷蘭三色、白帶 **VOC**，掛在三角帆桁後端，meta `kind=flag, flag=ensign, nation=dutch`）、主桅頂橘色長旗（pennant）。
- **帆裝三段**（照帆的 meta 算：topsail 1、topgallant／gaff 2、course 3；斜桅帆、斜桅頂帆 set 3、三角帆 set 2）：

  | 段 | 張哪幾面 |
  |---|---|
  | 1 收帆 | fore-topsail、main-topsail、mizzen-topsail |
  | 2 戰鬥帆 | ＋ fore-topgallant、main-topgallant、mizzen-lateen |
  | 3 滿帆 | ＋ fore-course、main-course、spritsail、sprit-topsail |

  收帆、戰鬥帆都至少一面、三段分得出來。
- 讀數：`tools/check_stage7.py`：channels 結果帳 0 差；CLI 繩 397（含展開的橫繩）、ropes_broken 0、帆 12、sails_broken 0；meta 帆 12／12、帆自己的繩 25／25、sail 標錯 0；帆桁 meta 的 sail 都是某一面帆的名字。**反向對照**：`draft_rigging.py --probe=nometa=main-topgallant.sheet-S`、`check_stage7.py --drop=fore-topgallant.sheet-P` ⇒ 都只報那一條。產生程式重跑兩次逐位元組相同。
- 過程圖：`overlays/step8_full.png`。

## 步驟 9 砲、砲具與砲索（2026-11-18）
設計 plan.json `guns_build`、`gunfittings_build`；產生 `design/draft_guns.py`（照抄藍鯊號，沒改程式；4 分鐘）⇒ `guns_placement.json`、`verify_guns.json`；落格 `design/tools/build_guns.py`（名字表加 24／18 磅）。
- **38 門 ＝ VD p.508 1671 表**（全部外部模型、沿用現有的砲、掛在所在甲板的子作品；P 舷 mirror=y；meta kind=gun、gun、deck、side、port）：
  - overloop 每舷 10 門：從船尾往前 8 磅（camer）、18 磅 ×3、24 磅 ×2（主桅兩旁）、18 磅 ×4。
  - verdeck 每舷 8 門：8 磅 ×6、bak 底下 4 磅 ×2；鏡板（kajuit）2 門 8 磅（camer）。
  - 24 磅 ＝ 憲法號 `-gun-24`（0.1 m、scale 1）、18 磅 ＝ 憲法號 `-gun-long18`（scale 0.5）、8 磅 ＝ `ridge-two-centurion-01m-gun-8l`（0.5）、4 磅 ＝ `pinnacle-patache-01m-gun-4l`（0.5）—— 擺法（pivot）照康塞普西翁號／餘燼號／藍鯊號用過的那一份；砲種代碼都在遊戲砲種表。
- 讀數（`tools/check_stage8.py`，從作品讀；Blockside 路徑改指 `Blocksail/external/Blockside` —— Valhalla 底下已經沒有）：模型 38 ＝ 設計、CLI ok 38；參數 ≠ 設計 0；外框（gunsim vs CLI）最大差 0.05；碰撞 0 門；砲口不在船殼外 0 門（伸出 1.0–8.5；最船尾 camer 那兩門船殼收得窄、只伸出 1.0–1.25）；meta 不合 0；設計那一側砲撞砲 0、兩舷不對稱 0。**反向對照**：`--push=砲M-S04:3`（往外推）⇒ 碰撞只報那一門 5,275 樣本；`--push=U-chase-stern-P:-6`（往裡拉）⇒ 只報那一門、伸出 −0.0。
- **砲具與砲索**（Ship_Guns §4.4，照藍鯊號補做的那一套）：`draft_gunfittings.py` ⇒ `tools/build_gunfittings.py`；子作品 `-gunfittings`（關聯 `砲具`，meta `kind=gunfittings` —— 遊戲那側才改得了格子）190 格（船牆的環 152、甲板環 38）、固定點 114；繩 190 ＝ 38 門 × 5（breeching ×2、side tackle ×2、train tackle）。`tools/check_stage12.py`：結果帳 0 差、固定點不在實心上 0、砲索 CLI 不是 ok 的 0、每門五條缺 0、端點對不上 0；設計那一側浮空 0、鏡像差 0。⚠ 沒做 shot garland 與 rammer／sponge。
- 組裝件 1 元件、空腔 0。

## 步驟 10 彈藥庫與甲板物件（2026-11-18）
設計 plan.json `gear_build`；產生 `design/draft_gear.py`（照抄藍鯊號，沒改程式）；落格 `design/tools/build_gear.py`。
- **彈藥庫**（`-magazine`，關聯 `彈藥庫`，meta `kind=magazine、pos=aft、powder_lb=6400`）8,349 格：koebrug 船尾 x 222–270（後艙口 300–312 之後）、門開在船頭那道艙壁、對著 koebrug 梯子（腳 x 340）；頂在 overloop 的樑底下（z 64）；銅皮 168、橡木框 136、松木地板 177。固定點 `blast` (249,160,53)、`door` (270,160,42)。火藥桶 **64 桶**（憲法號 `-powder-barrel` scale 0.2；⚠ VOC 1660 年代的軍需清單沒找到 ⇒ 藍鯊號 W p.282 的 32 桶 × 2，設計決定）全在底層（底層放得下 98）。
- **小艇架**（`-boat-skids`，關聯 `小艇架`）636 格：船腰三座橫架 x 470、505、530（閃開主艙口、往 verdeck 的前梯井、前艙口）、橫樑 z 91。
- 模型（沿用現有元件）：主絞盤（餘燼號）overloop 中線 x 428（主桅與主艙口之間；VOC 的 spil 在下層砲甲板）、羅經櫃（夜隼號）verdeck x 325（halfdek 底下的 stierplecht，舵手盯著羅盤操 kolderstok —— 研究筆記 §8）、小艇（餘燼號 cutter 9 m）擱在小艇架上 x 505、z 93。
- **廚房爐灶**（Ship_Fittings §9.13）：沿用藍鯊號的 kombuis `gura-pinas-01m-galley`（`draft_galley.py` 產的模型格子跟它逐格相同 ⇒ 引用、不另做）：verdeck 子作品的模型 `爐灶`（scale 0.5、at 599.5,160.5,82、kind=galley），bak 底下中線，煙囪從 bak 甲板橫樑 592–593／608–609 之間穿出 ⇒ 甲板-castillo 刻 9 格（`masks/galley/deck_hole.vox.txt`；`check_decks.py` 扣掉這個洞）。
  - 🩸 第一版擺在 x 581.5：本船 bak 底下淨高 17（藍鯊號 18）⇒ 爐身頂撞到 bak 甲板與橫樑，「洞」算成 18 格、又留一格煙道正中間浮空的甲板（組裝件 2 個元件）。補回 18 格、挪到 verdeck 平的那一段（x 589–612 都是 81）、洞只算煙囪 3×3（煙道中心也刻：四鄰都在洞裡的甲板格一起刻）⇒ 1 元件。
- **艙壁門**（Ship_Fittings §9.7）：`draft_doors.py` 照 plan 的四道 break ⇒ 8 扇（halfdek、hut、bak 後緣 rotate 180、bak 前隔板），門板沿用藍鯊號 `gura-pinas-01m-door`（格子逐格相同；`tools/build_doors.py` 改成引用、不建），meta kind=door open=side；撞實心 0、背後都是艙壁、腳下實心。⚠ hut 那道的門洞只有 11 格高（hut 底下淨高小），門板 16 格照樣蓋得住。
- 讀數（`tools/check_stage9.py`，從作品讀）：彈藥庫、小艇架結果帳缺 0／多 0／色差 0；模型 67 ＝ 設計、CLI ok 67；powder_lb 6,400 ＝ 64 × 100；blast 空氣、door 空氣且腳下實心；參數 ≠ 設計 0、撞實心 0、腳下 12 格內沒有實心 0、模型彼此重疊 0；新格落在實心上 0、封閉空腔 0、浮空 0、鏡像差 0。`check_decks.py` 11 件問題 0（bak 甲板扣掉煙囪洞）。組裝件 1 元件、空腔 0、link_overlap 0、models_broken 0（畫 125 個）。**反向對照**：`draft_gear.py --probe=nokind=小艇` ⇒ 只報小艇。

## 步驟 11 舵、操舵桿、錨（2026-11-18）
設計 plan.json `rudder_anchor_build`、`whipstaff`；產生 `design/draft_rudder_anchor.py`（照抄藍鯊號，沒改程式）、新寫 `design/draft_whipstaff.py`；落格 `design/tools/build_rudder_anchor.py`、操舵桿用 CLI 直接建。
- **舵**（`-rudder` 2,879 格，組裝件的外部模型 `舵`）：沿艉柱後緣（斜 7.1°）從龍骨底到 z 85（heck-balk z 91 底下）；3 格厚、前緣兩側削 1 格；水線下焦油深褐、上船殼褐、每 15 格一道鐵箍。meta `kind=rudder`、鉸鏈 (200, 160.5, 0)、軸 (−0.1234, 0, 0.9924)、max_deg 35、turn_axis=hinge、**spin**（rudder、±35、lag 0.3）。固定點 `stock-top` (186,160,85) 離船殼 3 格。
- **操舵桿 kolderstok**（不是舵輪）：研究筆記 §8 —— Witsen 全書只寫 kolderstok（W p.88、p.92：長 9 呎、粗 4 duim），1660 年代的荷蘭大船沒有舵輪 ⇒ 遊戲的操舵鏈有「舵柄（獨立模型）kind=tiller」那一列（Ship_Helm）⇒ 新做 `-whipstaff`（0.1 m，59 格：1 格粗的桿 z 79–103、verdeck 甲板面上一圈 rolle、頂上 3×3 握把、底下接舵柄的鐵眼），掛成 verdeck 子作品的模型 `操舵桿`（at 260.5,160.5,91、kind=tiller、spin rudder ±25°、轉軸 spin_pivot 在 rolle、spin_axis 沿船長方向）；verdeck 刻 1 格讓桿穿過（`masks/whipstaff/deck_hole.vox.txt`；`check_decks.py` 扣掉）。位置：halfdek 底下的 stierplecht、hut 前緣 262 之後、後桅 280 之前；羅經櫃從步驟 10 的 x 325 挪到它旁邊 x 270（VD p.508「by de compassen」）。⚠ 底下的舵柄 roerpen（從舵頭穿進砲手長艙）沒做；⚠ 擺角 ±25° 是挑的。藍鯊號、收穫號當時照遊戲放舵輪 —— 本船改用 tiller，遊戲的操舵鏈照樣成立（打掉操舵桿 ＝ 舵輪沒了）。
- **錨**：共用錨元件 ×2（scale 0.85、kind=anchor、anchor=bower）吊在船頭舷外 x 619.2、ring z 121、錨臂順著船殼切線（rz ±83）、離船殼 6 格（試了 x 618–626 × z 118–124）；錨架 `-anchor-gear`（billboard 托板，關聯 `錨架`）736 格；錨鏈孔固定點 hawse-S／P (658, ±25, 97)（只登記、沒有開孔）。
- 讀數（`tools/check_stage95.py`，從作品讀）：舵、錨架結果帳 0 差；舵模型 CLI ok、stock-top 8 格內有船殼（曼哈頓 3）、舵跟組裝件重疊 0、轉 ±35° 掃進實心 0；錨 2 隻 CLI ok、撞實心 0、腳是錨架、來源有 ring；hawse 在船殼上、在那一舷；問題 0。操舵桿：撞實心 0、鏡像差 0。遊戲讀的那一份（組裝件 `export format=parts`）：舵、操舵桿都有 spin。`check_decks.py` 問題 0；組裝件 1 元件、空腔 0、models_broken 0（畫 129 個）。**反向對照**：`check_stage95.py --drop=錨-P` ⇒ 只報 P 舷沒有錨。
- 過程圖：`overlays/step11_helm.png`（藏船殼與後甲板以上，看 stierplecht 的操舵桿與羅經櫃）。

## 步驟 13 材質（2026-11-18）
Ship_Materials §9.5：關聯的 material 管防禦與重量；外部模型的 material 只管反光。
- **船殼與木頭部件**：全船木頭 ⇒ 不標（遊戲預設橡木 oak）。金飾（galjoen、獅子、hackebort、側廊的金邊）是貼金的木頭 ⇒ 照木頭、不標金屬（設計決定）。
- **窗玻璃**：關聯 `船尾窗玻璃` material=glass（步驟 6）。
- **砲管**（模型 meta，只管反光）：青銅 24 磅 ×4 `material=bronze`（VD p.508「metale」）、鐵 18／8／4 磅 ×34 `material=iron`（⚠ VD 1671 表的 2 門青銅 8 磅「by de compassen」沒分出來，8 磅一律鐵）；錨 ×2 `material=iron`（錨在 `-anchor-gear` 子作品裡 ⇒ meta 寫在那件）。用 `work sub=meta file=` 批次標，讀回 `export format=parts`：gun 24l bronze 4、18l iron 14、8l iron 16、4l iron 4、anchor iron 2。
- `bronze` 只在遊戲那份材質表（TASK-1294 建築用）⇒ 照規格補進雕刻那份 `Sculpture/materials.json`（metal 1、rough 0.45、smooth，跟遊戲那份同值）。

## 步驟 12 砲門蓋板（2026-11-18）
工具 `design/tools/portlids.py`（照抄藍鯊號；`CLOSE_ADJ` 清空 —— 藍鯊號那兩片是照它自己的匯入檢查調的）⇒ `portlids_placement.json`、`verify_portlids.json`、蓋板子作品 `-portlid`（10×9×2：外面船殼褐 136、裡面紅 224、鉸鏈板 73；照最大的開口每邊大 1 格）。
- 先照步驟 14 匯入＋`admin.py ids`（砲的物件 id）⇒ 回來做蓋板 ⇒ 再 reimport＋ids（蓋板 portlid-1～38）。
- **38 片 ＝ 每個砲門一片**：overloop 20、verdeck 16、鏡板 2（藍鯊號補做時加的 `to_aft`：砲口朝 −x 的鏡板砲門照樣量）；P 舷 rotate 180 − rz、⛔ 不用 mirror=y；meta kind=portlid、lid_of ＝ 砲的物件 id（照模型 meta 對）、close_deg 68.7–111.3、house 4–10。
- 讀數（`portlids.py check`）：開著撞船 0、撞砲 0；關著落進船殼最多 1.36%（> 5% 的 0 片）、收砲後關上撞砲 0；砲門全蓋滿（沒蓋到 0）；鉸鏈中心在鉸鏈下 3.55–4.02；掛上去 cells 180 結果帳 0 差、models_bad 0、鉸鏈最大差 0。**反向對照**：house 0（砲不收）⇒ 38 片全撞砲；mirror=y ⇒ 18 片往上開。

## 步驟 14 給遊戲的 meta 與匯入（2026-11-18）
組裝件 `-assembly` 船殼關聯 kind=ship、waterline_z 48；`work sub=ropecheck` 繩 587、1,174 端全綁好（沒有 bind／snap）；Blockside 自己的 worktree（分支 `pinnacle/1317-voc`，從 dev c24322f）`admin.py import --work pinnacle-voc-01m-assembly --id kroon --name 金冠號`（el `ship-kroon`）⇒ `ids`（155 件）⇒ 修梯子、錨 ⇒ `reimport` ⇒ 蓋板 ⇒ `reimport`＋`ids`（38 片蓋板）⇒ 填 game.json ⇒ `build`、`showlod`、`ancbake`、`shipcheck`。
- **第一次匯入檢查 ✗ 4**：halfdek、hut 的四座梯子「梯頂接不上甲板」（hi 到 head 之間 4–5 柱懸空，本船舷弧大、船樓甲板邊跟藍鯊號不同）＋ bak 兩座 ⚠ 3 柱 ⇒ 照修法挪梯腳、head 不動（alcazar 420 → 415、toldilla 283 → 278、castillo 543 → 546；alcazar 416 那一版梯腳落在舷弧台階上懸空 1 格 ⇒ 再挪 1）、梯子子作品走差量、24 個梯子點 overwrite ⇒ 樓梯自檢 ✗ 0。錨的鐵網格做不出平滑 ⇒ 錨模型 `render=voxel`。
- 給遊戲那側的高度（z 從龍骨底，格 ＝ 0.1 m）：水線 48；甲板 koebrug 40、overloop 58（船尾 76）、verdeck 79（船尾 97）、bak 96–101、halfdek 97（船尾 116）、hut 115（船尾 134）；下層砲軸 70–80、上層砲軸 88–105；桅樓平台 前 222、主 245、後 256；主桅頂 480（離水線 43.2 m）；船殼 x 184–669、喙尖 743、艏斜桅 ≈ 790 ⇒ game.json `geo`：`spar [80,135]`、`marines [60,190]`、`center 100`、`aim 75`、`aimZ [30,470]`、`deckAim [62,98]`、`rigAim [190,460]`；`role merchant`、`names ["金冠號"]`（geo 的鍵照 Blockside `js/05_hull.js` 的說明）。
- 讀數：vxk checksum **3945602128**、格 835,385、模型 167（vxk 檔頭；遊戲讀的模型 138 ＝ 去掉不算的）、繩 587；匯入檢查 **✗ 0、⚠ 5**（每一筆看過）：
  - 送藥手站得到 15／19、陸戰隊 7／12（geo.marines 照康塞普西翁號、藍鯊號推的範圍；遊戲那側可再調）；
  - overloop 往 verdeck 前梯（main-fwd）的梯腳前 1–2 格是遊戲自動擺的木工台（家具，繞得過去）；
  - ⑥ **艙底（koebrug 底下 x 217–655、354 m²）沒有梯子下得去** —— 本船的 draft_decks 是藍鯊號那一版，沒有康塞普西翁號的 `lo: hold` 梯井 ⇒ todo；
  - 爐灶沒有 smoke 固定點（沿用的 `gura-pinas-01m-galley` 沒登記；那件是 gura 的作品）⇒ 用餐時不冒煙。
  - 樓梯自檢 9 座 ✗ 0、⚠ 1；甲板連通 ✗ 0、⚠ 1（就是艙底）；超載極限：再多載 1,998 t（吃水再深 4.60 m）才從 verdeck 船殼的縫進水，比沉沒線（4.2 m）高。
  - 材質：全船橡木 584.5 t ＋ 玻璃 480 格；模型反光 bronze 4、iron 36（錨 render=voxel）；操舵「舵令 ⇒ 甲板-puente/操舵桿 ⇒ 舵 100%」；砲門蓋板 38 片、沒有蓋板的砲 0。
- 船卡：1,596 t、48.5 m、38 門（long4 4、long18 14、long8 16、long 4）、舷側齊射 228、帆 10、船員 231。
- **遊戲裡**（worktree 成品、`?debug=1&ship=kroon,pinas&mode=eve`）：開局 `__game.lostModels(0)` 空；帆的 meta 照遊戲的 sailSetLevel 算三段 ＝ 步驟 8 那張表（收帆 3 面 topsail、戰鬥帆 ＋ 兩面 topgallant＋bezaan、滿帆 10 面）；開戰後以戰鬥帆側順風 13.1 節；`__game.nation(0,'spain')` ok、own {dutch}、miss []；主控台 0 錯誤。圖 `overlays/step14_ingame.jpg`。

## 步驟 15 交船（2026-11-18）
照 Ship_Game §10 換一艘船時的檢查表逐條看過（遊戲那一份：`admin.py shipcheck --id kroon` ✗ 0 ⚠ 5，見步驟 14）：
- ✓ ropecheck 587 條、1,174 端 ok、沒有 bind／snap；組裝件名 ＝ 金冠號、船殼「金冠號 船殼」帶 sub；mpv 0.1 每件都記（子作品 0.1，沿用的元件照它自己的、模型明寫 scale）；開工前查過現有元件（步驟 2「沿用的現有元件」）。新做的：船首像、hackebort、Zeeland 紋章（個性裝飾）、後桅三角帆桁（藍鯊號那根長度不同）、**操舵桿 kolderstok**（現有元件只有舵輪；1660 年代荷蘭大船用操舵桿）、砲門蓋板（10×9，照本船最大的開口）。
- ✓ 爐灶 ＝ 廚房 `kind=galley`（不標 deco）、廚師站得住的面 4。
- ✓ 砲 38、帆桁 10、火藥桶 64、絞盤、羅經櫃、小艇、門 8、蓋板 38 都是外部模型帶 kind；舵 kind=rudder＋stock-top、開局 `lostModels(0)` 空；spin：舵 ±35°、操舵桿 ±25°；操舵鏈「舵令 ⇒ 甲板-puente/操舵桿 ⇒ 舵 100%」（kind=tiller，不是名字）。
- ✓ kind=ship waterline_z 48（高度寫在步驟 14）；甲板 6 層 kind=deck（level、name、floor、thick）、梯子 9 座 kind=ladders 四個固定點；樓梯自檢 ✗ 0（⚠ 艙底沒梯子、梯腳前有木工台 —— 看過）。
- ✓ ratlines 橫繩組 12 組、下桅 6 組繩梯；三角帆桁 yard=gaff＋rig=lateen＋fore；彈藥庫 64 桶、38／38 門送藥走得到；窗的玻璃獨立關聯 material=glass（480 格）。
- ✓ 繩與帆的端點綁 model:、ropes_broken／sails_broken／models_broken 0；帆 12／12、帆自己的繩 25／25 meta 齊、帆桁 sail ＝ 帆名、mast 有寫；帆裝三段表在步驟 8、遊戲裡照 meta 算過一次；桅的關聯 kind=mast（四條）。
- ✓ 組裝件 1 元件、空腔 0、link_overlap 0；一舷＋鏡像的部件兩舷對稱（hackebort 的紋章與字照實不對稱）；產生程式重跑逐位元組相同；vxk checksum 3945602128（Blockside 那份 _cache 跟它對過）。
- ✓ 每門砲退到零碰撞、砲口在船殼外；鏡板追擊砲照角度搜；舷側＋鏡板砲門都有蓋板（P 舷 rotate 180、不用 mirror）。
- ✓ 金屬：砲管 bronze／iron、錨 iron（模型只管反光）；全船木頭 ⇒ 不用跟遊戲那側說全船材質。
- 不適用：槳、撞角、蒸汽、鐵甲、迴旋砲／砲塔、砲身砲座拆件、空艙房（沒隔艙）。

### todo（沒做的，照實留著）
- ~~艙底（koebrug 底下 354 m²）沒有梯子~~ ⇒ 2026-11-18 下午補了（步驟 5「補：艙底梯」）。
- 爐灶沒有 smoke 固定點（元件是 gura 的 `gura-pinas-01m-galley`，要她補；或本船另做一件）。
- 操舵桿底下的舵柄 roerpen 沒做；錨鏈孔只登記固定點、沒開孔；shot garland、rammer／sponge 沒做。
- 鏡板中段（走廊頂到 hackebort 底）素面；Walcheren 船尾畫（RMG PAH1782）圖本身沒看，紋章與持杖人像只照館藏說明。
- 遊戲那側：陸戰隊 7／12、送藥手 15／19（geo／船員配置可再調）；Blocksail 船型清單（fleet.js 的 types、hullLoa、船員）還沒接 —— 等 Tim。
