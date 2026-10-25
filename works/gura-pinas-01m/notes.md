# 藍鯊號（De Blauwe Haai）—— 荷蘭 pinas（pinasschip），1660 年代（0.1 m／格）—— 建造筆記

委託：TASK-0967（Tim 2026-10-26「967 造船 GO」；母單 TASK-0964 的 8 種候選之一）：《Blocksail》1666 加勒比船型 —— 荷蘭平底船 pinas，武裝商船（荷蘭西印度公司、荷蘭私掠）。照造船規格雕刻、匯入 Blockside、接進 Blocksail 船型清單。
流程：第一艘照 `Ship_Steps` 步驟表走的船（Tim 2026-10-26 要求造船文件拆成按步驟讀；Senate ce0aaed）—— 步驟表貼在 TASK-0967 的驗收標準，每一步只讀那一行寫的文件。

## 座標約定（照收穫號，產生程式也從它抄來）
- 空間 800×320×640；X 船長（船頭 +X）、Y 船寬（中線 ＝ 第 160 格，鏡像 y ↔ 320 − y）、Z 高度（z 0 ＝ 龍骨底面）；P ＝ y < 160。
- 0.1 m／格（船殼、組裝件書卡都記了）。1 阿姆斯特丹呎 ≈ 0.2831 m ＝ 2.831 格（研究結果回來再核）。
- 「在不在船裡」：|y − 160| ≤ 半寬（格心判斷）⇒ 兩舷逐格對稱。

## 作品
- 船殼 `gura-pinas-01m`「藍鯊號 船殼」：任務作品（委託 TASK-0967、10 token 已發），`tags=sub`。
- 組裝件 `gura-pinas-01m-assembly`「藍鯊號」：主作品（沒標 sub），parent 船殼。
- 子作品照收穫號的拆法（甲板每層一件、梯子、桅、帆桁、裝飾、彈藥庫、舵、錨架…），parent 船殼、`tags=sub`。

## 產生程式
- `design/` 整套從收穫號 `calli-cosecha-01m/design/` 抄來（它的線形又出自三叉戟號 `hull_lines.py`）：37 個 .py 的作品 id、persona、船名已換成本船（檔頭寫了出處）；`plan.json` 照 pinas 重寫（收穫號那份留成 `plan_cosecha_ref.json` 對照）。

## 沿用的現有元件（`work sub=components`，2026-10-26 查）
- 砲：風暴角號 12 磅 `summit-stormkaap-01m-gun-12l`、6 磅 `-gun-6l`（6 磅那件也被縮放當 8 磅用過）；憲法號 18 磅 `basecamp-frigate-constitution-01m-gun-long18`。
- 舵輪＋座 `basecamp-frigate-constitution-01m-wheel`／`-wheel-stand`、羅經櫃 `summit-night-falcon-01m-binnacle`、絞盤 `basecamp-ember-01m-capstan`、小艇 `basecamp-ember-01m-boat`、錨 `basecamp-frigate-constitution-01m-anchor`、火藥桶 `basecamp-frigate-constitution-01m-powder-barrel`、船尾燈 `gura-tridente-01m-lantern`、砲門蓋板 `basecamp-frigate-constitution-01m-portlid`。
- 自己做：船首像（荷蘭船慣例的紅獅子）、船尾鏡板（荷蘭船船尾畫船名那隻動物 ⇒ 藍鯊）、船名板。

## 步驟 3 找資料與新圖紙（2026-10-26）
查證：研究代理讀 Witsen 1671 原書掃描（archive.org aeloudeenhedenda00wits，p.72、77–79、93、282 對過頁面圖）⇒ `references/research_pinas_2026-10-26.md`（gura 讀過全文）。母單 TASK-0964 的〔估〕「20–40 門、60–150 人、噸位查不到」⇒ 原書：**24 門（12 磅 10、8 磅 8、6 磅 2、4 磅 4）、100 人、航程就是去 Curaçao**；吃水 10 呎時 Witsen 自己算的排水 26 278 立方呎 ≈ 596 m³（≈ 605 t）。

設計 `design/plan.json`（每個數字的 src：W 原書／設計決定）；程式：`lines.py`（照抄收穫號）、`layout.py`（改：舷弧端點吃 plan、砲門可以照位置清單、每個砲門的砲種、上桅）、`draft_lines.py`（讀數換成 Witsen 對照）、`draft_layout.py`、`tools/tune_lines.py`（掃線形參數對 Witsen 的體積）。

| 項目 | 本船（格 ＝ 0.1 m） | Witsen 1671（1 呎 ＝ 2.831 格） |
|---|---|---|
| 首柱到艉柱（首柱頂高） | 379.3 | 134 呎 ＝ 379.4 |
| 龍骨 | 294.4 | 104 呎 ＝ 294.4 |
| 首柱前傾／艉柱後傾 | 73.5／11.3 | 26 呎 ＝ 73.6／4 呎 ＝ 11.3 |
| 最寬（hals、z 40，含外板） | 85 | 29'3" 肋材外緣 ＋ 外板 ≈ 85 |
| 舭部（kimmen）寬，龍骨頂上 4'5" | 77 | 27 呎 ＝ 76.4 |
| 艉橫樑那一層（z 70）的寬 | 55 | heek-balk 19'6" ＝ 55.2 |
| 吃水 10 呎（從龍骨頂量）的水下體積 | 592.7 m³ | 26 278 立方呎 ＝ 596.2 m³ |
| 設計水線 z 33 的排水量（× 1.025） | 599 t | ≈ 605 t |

- 🩸 **第二證人第一次就說話了**：照收穫號的參數、吃水從龍骨底量 ⇒ 415 m³（差三成）。tools/tune_lines.py 掃 32 組線形，**到 596 m³ 的吃水全都落在龍骨頂往上 9.6–11.0 呎** ⇒ Witsen 的吃水是從龍骨頂量的；從龍骨底量的話，船中剖面怎麼調都裝不到（上限 ≈ 540 m³）。水線改到 z 33、挑讓舭部寬也對上的那一組（s_aft 0.3、s_fwd 0.72、aft_pow 3、bilge_pow 1.8）。
- 艉橫樑：收穫號的鏡板從 z_wt − 6 開始張、＋6 才全寬 ⇒ z_wt 取 64，z 70（W 的艉柱頂）全寬 55。
- 甲板：下甲板 overloop z 42（艙深 13 呎）、上甲板 verdek 60（甲板間取 18 格 ＝ 6'4"，W 的樑高 5'9½"–6'6" 之間；遊戲頭頂要 14 格）、後甲板 halfdek 84（到 x 300）、船尾樓 hut 101（到 x 207）、船艏樓 bak 82（從 x 436；W 5½ 呎 ⇒ 遊戲要 17）、火藥艙平台 24（x 215–300）；舷弧最低在 hals x 412、往船尾 6、往船頭 4。程式沿用收穫號的代號：main ＝ overloop、puente ＝ verdek、alcazar ＝ halfdek、toldilla ＝ hut、castillo ＝ bak。
- 砲門照 W 的間距（離 hek-stut 13 呎起，10、9、10、10½、11½、12½、12 呎；bak 裡離首柱 6½、17、31 呎）：下甲板每舷 8、bak 每舷 3、船尾鏡板 2 ⇒ 24。⚠ W 最船尾那一個（離 hek-stut 2½ 呎）在本船線形裡落在艉橫樑下往裡收的弧面（半寬 4 格）⇒ 不開，那兩門放到鏡板（W 寫了鏡板上有砲門）。砲種照「最重的放中段」：下甲板從船尾 8、8、12、12、12、12、12、8；bak 4、4、8（從船頭往後是 8 在後）；鏡板 6 磅 drake。
- 桅：前桅 x 492（前緣離首柱 1/9 船長）、主桅 x 333（船中往後 5½ 呎）、後桅 x 235（離船尾 1/5，⚠ 分數字小）；長度、桅頂、帆桁全照 W p.93；桅樓半徑 前 13、主 14（W 9、10 呎）、後 11（W 4½ 呎 ⇒ 遊戲要站人，設計決定）。主桅頂離水線 37.5 m。
- 讀數：船殼牆 336,354 格、1 元件、空腔 0、鏡像差 0；產生程式重跑 6 個輸出檔逐位元組相同。**反向對照**：`draft_layout.py --probe=port=main:5:+3` ⇒ 只有第 4–5、5–6 兩段間距變（23 → 26、25 → 22）。

## 步驟 4 船殼落格、砲門、塗裝、船尾窗（2026-10-26）
- 標記 `船殼:begin`（upto=start）→ `tools/stamp_lists.py gura-pinas-01m 0 masks/hull/hull_01..02.vox.txt`（250,000 ＋ 86,354，每刀 placed ＝ 清單）→ `船殼:end` → `砲門:begin` → carvevox `masks/ports/carve.vox.txt`（帶刻之前的顏色守門，4,841）→ stampvox overwrite=1 `masks/ports/paint.vox.txt`（24,693）→ `砲門:end`。
- `draft_ports.py` 改：船尾面門檻（收穫號寫死 x < 170）與窗量甲板高的 x（寫死 130）改吃 plan.stern；腰板可以不描金（edge false）；舷牆一整片上色（lozenge radius −1、每列 bg）；只換水線上的外板色（收穫號 ＝ 黑 36、本船 ＝ 褐 136）。
- 塗裝：腰板黑 36 三道（W：uitwatering 下 1'8"、再上 2'5"、raa-hout）、上層舷牆藍 6 四段（上甲板 64–73、後甲板 87–94、船尾樓 104–109、船艏樓 85–91）上下金邊、舷頂金、砲門外一圈紅 224；鏡板：上甲板兩個砲門（金框）、kajuit 三扇窗、hut 五扇窗（玻璃 87）。
- 讀數（作品一律從 CLI 匯出讀）：
  - `tools/check_hull.py`：結果帳 作品 336,354 ＝ 設計，缺 0、多 0、色差 0；線形對照 293 點差 0；**反向對照** probe_x=300（那一站 +3）⇒ 只報那一站 18 點、最大差 3。
  - `tools/check_stage3.py`：結果帳（船殼 − 刻 ＋ 換色）331,513，缺 0、多 0、色差 0；22 個舷側砲門開口裡實心 0、鏡板 2 個砲門刻穿；**正向對照**（同一把尺量 `船殼:end`）⇒ 22 個全報、鏡板各 49。
  - 🩸 鏡板砲門那把尺抄來時寫死收穫號的船尾 x 80–170、< 150 ⇒ 量本船（船尾 x ≈ 158）刻之前也報 0（瞎的）；改照線形的船尾面 ＋ 牆厚 ⇒ 刻之前 49、刻之後 0。
  - 引擎 `stats structure=1 mirror=y:160`：1 元件、封閉空腔 0、鏡像差 0。
- 組裝件 `gura-pinas-01m-assembly`：關聯 `船殼` at 0,0,0、meta `kind=ship, waterline_z=33`。
- 過程圖：`overlays/step4_hull_{bowq,sternq,side}.png`。

## 步驟 5 甲板、梯子、艙房（2026-10-26）
設計 plan.json `decks_build`；產生 `design/draft_decks.py`（照抄收穫號，沒改程式）⇒ `masks/decks/<層>.vox.txt`、`masks/ladders/<上面那層>.vox.txt`、`ladder_points.json`、`verify_decks.json`、`sheet04_decks_v1.png`；落格 `design/tools/build_decks.py`。
- 甲板 6 層（子作品 `-deck-{orlop,main,puente,alcazar,toldilla,castillo}`、組裝件關聯 `甲板-<層>`）；艙口三個（後 244–254、主 350–368、前 410–420，閃開後桅 235、主桅 333、前桅 492）；break 三道（後甲板前緣 x 300、船尾樓前緣 207、船艏樓後緣 436：艙壁兩扇門＋7 格胸牆，梯子頭留口）；桅孔照傾斜軸線。
- 梯子 9 座（子作品 `-ladders-<上面那層>`，掛在它上面那一層的甲板裡、關聯 `梯子` meta `kind=ladders`，固定點 `<梯名>.foot／lo／hi／head`）：底艙→下甲板（左舷 dy −14）、下甲板→上甲板 後（x 287）前（x 385）、上甲板→後甲板兩舷、後甲板→船尾樓兩舷、上甲板→船艏樓兩舷。每一層都有梯子通到。
- 🩸 第一版 6 個梯子點有問題，都是排位置撞了：底艙梯子的井開在下甲板、正好是往上甲板那座梯子的腳（腳踩空）⇒ 底艙梯子挪到左舷；後甲板梯子最高一階落在 break 艙壁上 ⇒ 起點往前 4；船艏樓梯子最高一階落進船艏樓甲板 ⇒ 往後 3；往上甲板那座的腳跨在舷弧台階上（x 285 甲板 44、x 286 是 43）⇒ 起點 287。
- 甲板 meta：每層子作品 `export format=vxk links=none` ⇒ Blockside `src/decks.py` ⇒ `design/decks_meta.tsv`（name 換成 plan 的中文名）⇒ `work sub=meta`（6 條）：level 0 火藥艙平台、1 下甲板、2 上甲板、3 船艏樓、4 後甲板、5 船尾樓。
- 艙房：沒隔（同收穫號）；之後要配功能艙再加。
- 讀數：設計那一側：重疊 0、砲門往艙裡被擋 0、梯子點問題 0、封閉空腔 0、鏡像差 0（下甲板 634 ＝ 底艙梯子靠左舷的井，照實）；`tools/check_decks.py`（每件從匯出讀）：11 件 98,441 格，缺 0、多 0、色差 0、跟船殼／彼此重疊 0；梯子點（組裝件 parts，遊戲讀的那一份）36／36、跟設計差 0、空氣／腳下／頭頂 14 格問題 0；組裝件 1 元件、空腔 0。**反向對照**：`draft_decks.py --probe=drop_ladder=castillo-S` ⇒ 8 座、船艏樓只剩 castillo-P。
- 預覽 preset：`藏船殼`。過程圖 `overlays/step5_decks.png`。
