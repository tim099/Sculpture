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

## 步驟 6 裝飾、窗的玻璃（2026-10-26）
- **窗的玻璃**（Ship_Materials「窗的玻璃」）：`draft_ports.py` 改成鏡板窗最外一格刻掉（凹進去）、第二格是玻璃（從船殼拿出來）、玻璃後面的牆刻穿（後面是艙裡的空氣）⇒ `masks/glass/stern_glass.vox.txt`。收穫號是把玻璃色漆在牆裡、後面還是實心。船殼走差量：先拿舊的砲門清單組帳 ⇒ 跟作品 0 差（帳組得對）、再拿新的 ⇒ `delta_apply` 刻 681（玻璃 225 ＋ 後面的牆 456），標記 `窗玻璃:begin／end`。子作品 `-stern-glass`（225 格）、組裝件關聯 `船尾窗玻璃` meta `material=glass`。
- `draft_deco.py` 重寫成荷蘭船的部件（框架照收穫號）：
  - `-galjoen`「船首喙」6,032：喙甲板頂 z 72、長 62（W uitlegger 22 呎）、head rail、cutwater 從首柱 z 20 掃到喙尖；艏斜桅那條線被擋 0。
  - `-figurehead`「船首像」855：**紅獅子**（W p.85：長 9 呎 ＝ 25 格、厚 19 duim、前端翹起 2'7"），紅身金鬃金冠，後腳、前腳站在喙甲板上。
  - `-stern-deco`「船尾裝飾」7,436：船尾走廊（hut 窗下、伸出 5）＋兩舷側廊（W：側廊常用銅皮蓋頂 ⇒ 銅頂 168；窗是畫上去的 87，後面是側廊的實心 —— ⚠ 只有鏡板的窗是真的玻璃）。
  - `-hackebort`「hackebort」1,400：鏡板頂上那塊板（順著鏡板往後倒、頂上拱形）；奶油底、藍鯊紋章（頭朝左舷）、藍帶金字 BLAUWE HAAI（W p.83：鏡板上「照慣例裝紋章」；荷蘭船照船名畫那隻動物）⇒ **這一件的鏡像差 130 照實報**（鯊魚與字）；拱頂正中間一盞船尾燈（模型 `lantern`，沿用三叉戟號船尾燈 scale 0.5、kind=light，腳下實心、頭上空）。
- 🩸 組起來 2 個元件：獅子尾巴往後挪一格的那一階只在斜角相接（收穫號船首像踩過的同一個坑）⇒ 那一階補一格、差量貼 1 格 ⇒ 1 元件。
- 讀數：`tools/check_stage5.py` 四件結果帳缺 0／多 0／色差 0；跟船重疊 0、部件之間重疊 0、跳過 0；組裝件 1 元件、空腔 0；models_broken 0。**反向對照**：`draft_deco.py --probe=shift=figurehead:3` ⇒ 獅子鏡像差 0 → 854。產生程式重跑逐位元組相同。
- 過程圖：`overlays/step6_{bow,stern}.png`。⚠ 鏡板中段（hut 窗上面到 hackebort 下面）還是素面褐色 —— 先放著。

## 步驟 7 桅與帆桁（2026-10-26）
設計 plan.json `rig_build`（長度與位置在 `masts`，照 W p.93）；產生 `design/draft_masts.py`（照抄收穫號，改：上桅 bramsteng 一段＋中桅頂的十字桅頂架、斜桅頂桅 blinde steng、帆桁吊點照掛在哪一段桅取半徑、船殼標記改吃 plan）；落格 `design/tools/build_masts.py`。
- 桅（每根一件子作品，關聯 `前桅`／`主桅`／`後桅`／`艏斜桅`）：前桅 8,720、主桅 10,170（下桅＋桅樓＋中桅＋十字架＋上桅）、後桅 3,918（下桅＋桅樓＋後中桅）、艏斜桅 3,676（含斜桅頂桅）。桅樓半徑 前 13、主 14、後 11。
- **艏斜桅的腳改到船艏樓甲板**（x 500、z 83，30°）：放上甲板會從船艏樓甲板穿過去；改了之後從船頭舷牆上面過去 ⇒ 船殼開孔 0 格（收穫號開了 180 格）。
- 帆桁 10 根（外部模型，掛在各自的桅子作品）：方帆桁 9 根沿用憲法號的帆桁元件、只沿長度縮放到 W 的長度（主帆桁 19.5 m、前 17.1、主中桅 10.2、前中桅 9.1、主上桅 6.2、前上桅 4.5、後中桅 5.4、斜桅帆桁 12.7、斜桅頂帆桁 5.7）；三角帆桁 1 根新做 `-yard-mizzen-lateen`（17.55 m、40°、吊點前端往後 40%；meta yard=gaff、rig=lateen）。
- 讀數：`tools/check_stage6.py` 桅 4 件＋三角帆桁結果帳缺 0／多 0／色差 0；船殼 ＝ 窗玻璃:end（孔 0）0 差；帆桁模型 10 根 meta 與來源固定點問題 0；帆桁穿船 10 根全 0；三角帆桁後端伸出船尾 0.11 m；models_broken 0；組裝件 1 元件、空腔 0。跳過的格：前桅腳插進船頭 deadwood 98（桅坐在船殼上，同收穫號）、艏斜桅腳壓到船艏樓甲板 14。**反向對照**：`--probe=pivot=yard-main-course:-150`（放到船殼的高度）⇒ 只有那一根報 36 格。產生程式重跑逐位元組相同。
- 過程圖：`overlays/step7_masts.png`、`design/sheet06_masts_v1.png`。

## 步驟 8 索具、帆、旗（2026-10-26）
設計 plan.json `rigging`；產生 `design/draft_rigging.py`（框架照收穫號，改成荷蘭 pinas 的帆裝）⇒ `masks/rigging/channels.vox.txt`、`rigging_plan.json`、`textures/ensign.png`、`verify_rigging.json`；套用 `design/tools/rigging_apply.py`（加一步「橫繩組」）。
- **channels**（`-channels`，關聯 `支索板`，兩舷一件）2,214 格：W 的支索台 putting 數 ⇒ 每舷 shrouds 主 7、前 6、後 4（＋中桅 backstay 前、主各 1）、間距 6。主桅那一排從桅前 12 格起往後排 —— 照收穫號從桅往後排的話後半段落在後甲板舷牆那一段（x < 300）、支索會穿過舷牆頂。
- 固定點 143（桅上 hound／stay-head／futtock／tm-hound／tm-stay-head／桅樓邊 rim／top-aft；上桅：十字桅頂架兩端 ct、tg-hound、tg-stay-head；艏斜桅 forestay-foot／cap-top／side／bob、斜桅頂桅頂 sprit-top；喙的 bobstay 腳；船殼舷頂的 belay；後甲板的三角帆 tack）。
- 繩 119：shrouds 34、中桅 shrouds 18、futtock 18、上桅 shrouds 8、backstays 4、stays 8（前上桅支索拉到斜桅頂桅頂、主上桅支索到前桅十字架後端、後中桅支索到主桅桅樓）、艏斜桅 4、帆自己的繩 25。
- **ratlines 用橫繩組**（Ship_Rigging §6／TASK-0678，收穫號那時還是一條一條的子繩）：12 組（每根桅 lower／topmast × 兩舷），下桅 6 組 `climb=1` 繩梯：foot ＝ 舷牆內側往裡 3 格的甲板（前 船艏樓、主 上甲板、後 後甲板）、head ＝ 桅樓靠這一舷的邊（半徑 − 3）；產生程式先量站不站得住（腳下實心、頭上 7 格空）。🩸 主桅那兩組的 foot 第一版從中線往外找舷牆內面 ⇒ 先撞到主桅本身 ⇒ 從離中線 8 格起找。
- 帆 12：前／主 course、topsail、topgallant（上桅帆 bramzeil）、後中桅帆 kruiszeil（sheet 綁後桅桅樓邊）、後桅三角帆 bezaan（clew 在船尾樓上方、sheet 綁船尾樓兩舷舷頂、tack 綁後甲板）、斜桅帆 blinde、斜桅頂帆 boven blinde（sheet 綁斜桅帆桁的 earing）、船尾旗（紅白藍、白帶 GWC —— 荷蘭西印度公司；掛在三角帆桁後端）、主桅頂橘色長旗。meta：帆 12、帆自己的繩 25；斜桅帆、斜桅頂帆 set 3、三角帆 set 2。
- 讀數：channels 結果帳 0 差；CLI 繩 327（含展開的橫繩）、ropes_broken 0、帆 12、sails_broken 0；meta 帆 12／12、帆自己的繩 25／25、sail 標錯 0；帆桁 meta 的 sail 都是某一面帆的名字；橫繩組 12 組全 ok、繩梯 6 組都有 🪜。**反向對照**：`draft_rigging.py --probe=nometa=main-topgallant.sheet-S`、`check_stage7.py --drop=fore-topgallant.sheet-P` ⇒ 都只報那一條。
- 過程圖：`overlays/step8_{full,sternq}.png`。

## 步驟 9 砲（2026-10-26）
設計 plan.json `guns_build`；產生 `design/draft_guns.py`（照抄收穫號，沒改程式）⇒ `guns_placement.json`、`verify_guns.json`；落格 `design/tools/build_guns.py`。
- **24 門 ＝ W p.282**（全部外部模型、沿用現有的砲、掛在所在甲板的子作品上；P 舷 mirror=y；meta kind=gun、gun、deck、side、port）：
  - 下甲板每舷 8 門：從船尾往前 8 磅、8 磅、12 磅 ×5、8 磅（W「最重的砲放在船身中段」）。
  - 上甲板船艏樓底下每舷 3 門：從船尾往前 8 磅、4 磅、4 磅。
  - 上甲板船尾鏡板 2 門：青銅 6 磅 drake。
  - 12 磅 ＝ 風暴角號 `-gun-12l` scale 0.5；8 磅 ＝ 同一件縮 0.45；4 磅 ＝ 風暴角號 `-gun-6l` 縮 0.42；6 磅 drake ＝ 同一件縮 0.40（Ship_Guns §2.2：只差口徑的照現有的縮放；長短照 W 的砲重比）。砲種代碼 12l／8l／6l／4l 都在遊戲砲種表。
- 🩸 鏡板那兩門第一版擺不進去（退 35.5 格、砲口在牆裡 27 格）：鏡板砲門中心在 ±22.5，貼著船尾兩舷的牆（鏡板半寬 27.5、牆 4）⇒ 砲門半寬 26 → 20、kajuit 的窗 12 → 10。船殼走差量（拿舊清單組帳 0 差 ⇒ 刻 416、補 626、換色 84，標記 `鏡板砲門內移`）、玻璃刻 20、補 20。
- 讀數（`tools/check_stage8.py`，從作品讀）：模型 24 ＝ 設計、CLI ok 24；參數 ≠ 設計 0；外框（gunsim vs CLI）最大差 0.05；碰撞 0 門；砲口不在船殼外 0 門（伸出 0.5–6.0）；meta 不合 0；兩舷不對稱 0、砲撞砲 0。
  - 🩸 砲口那把尺（收穫號的）在左舷鏡板砲上**量不到東西**：兩條側線（±6）一條穿過砲門開口、一條穿過窗（連續座標的鏡面在 160.5，左舷鏡過來差半格），一格船殼都沒碰到 ⇒ 舊版印「伸出 10 億」還算過關。改成每邊掃 ±6／7／8 三條、全部沒碰到就報「量不到」。
  - **反向對照**：`--push=U-chase-stern-P:-6`（往裡拉）⇒ 只報那一門、伸出 −3.0；`--push=砲M-S04:3`（往外推）⇒ 碰撞只報那一門 1,971 樣本。
- ⚠ 沒做砲具與砲索（環、breeching、tackle；收穫號階段十二那一套）—— 記在 todo。

## 步驟 10 彈藥庫與甲板物件（2026-10-26）
設計 plan.json `gear_build`；產生 `design/draft_gear.py`（照抄收穫號；改：小艇架的空腔檢查框收穫號寫死 z 80 起 ⇒ 照橫樑高度往下 20）；落格 `design/tools/build_gear.py`。
- **彈藥庫**（`-magazine`，關聯 `彈藥庫`，meta `kind=magazine、pos=aft、powder_lb=3200`）5,818 格：火藥艙平台 x 222–262、門開在船頭那道艙壁、對著底艙梯子（foot x 293）；銅皮 168、橡木框 136、松木地板 177。固定點 `blast` (242,160,33)、`door` (262,160,26)。後艙口穿過地板，彈藥庫自己鋪地板蓋掉（收穫號同樣）。
  火藥桶 **32 桶**（憲法號 `-powder-barrel` scale 0.2）：**W p.282 的軍需清單火藥 3,000 pond ≈ 3,260 英磅 ⇒ 100 磅一桶 ≈ 32**（收穫號是照砲數換算的）；全在底層（底層放得下 46）。
- **小艇架**（`-boat-skids`，關聯 `小艇架`）612 格：船腰三座橫架 x 345、385、407（閃開主艙口、往上甲板的梯子井、前艙口；405 那座擋到船艏樓梯子頭 ⇒ 407）、橫樑 z 71–72。
- 模型（沿用現有元件）：主絞盤（餘燼號）上甲板 x 316、羅經櫃（夜隼號）後甲板 x 282、小艇（餘燼號 cutter 9 m）擱在小艇架上 x 385、z 73。舵輪在步驟 11。
- 讀數（`tools/check_stage9.py`，從作品讀）：彈藥庫、小艇架結果帳缺 0／多 0／色差 0；模型 35 ＝ 設計、CLI ok 35；powder_lb 3,200 ＝ 32 × 100；blast 是空氣、door 是空氣而且腳下實心；參數 ≠ 設計 0、撞實心 0、腳下 12 格內沒有實心 0、模型彼此重疊 0；新格落在實心上 0、封閉空腔 0、浮空 0、鏡像差 0。**反向對照**：`draft_gear.py --probe=nokind=小艇` ⇒ 只報小艇。
- 沒做：門與艙蓋（kind=door；Ship_Fittings §9.7 —— 低乾舷船才要擋水，本船艙口都在上甲板以上）、廚房（kind=galley）—— 照實留著，記 todo。
- 順手：抄來的工具把關聯備註寫成收穫號的「階段四／九」⇒ 改成本船的步驟（只改備註）。

## 步驟 11 舵、舵輪、錨（2026-10-26）
設計 plan.json `rudder_anchor_build`；產生 `design/draft_rudder_anchor.py`（照抄收穫號；改：錨避開的砲改讀上甲板（本船船頭的砲在船艏樓底下）、量船殼切線的高度收穫號寫死 z 100 ⇒ plan z_ref 88、加舵輪與座、舵與舵輪的 spin）；落格 `design/tools/build_rudder_anchor.py`（加舵輪與座）。
- **舵**（`-rudder` 1,768 格，組裝件的外部模型 `舵`）：沿艉柱後緣（斜 9.2°）從龍骨底到 z 66（艉橫樑 z 70 底下）；3 格厚、前緣兩側削 1 格；水線下焦油深褐、上橡木褐、每 12 格一道鐵箍。meta `kind=rudder`、鉸鏈 (170, 160.5, 0)、軸 (−0.1595, 0, 0.9872)、max_deg 35、turn_axis=hinge、**spin**（rudder、±35、lag 0.3）。固定點 `stock-top` (156,160,66) 離船殼 3 格。
- **舵輪＋座**（Ship_Helm §9.8.1）：沿用憲法號雙舵輪 `-wheel`（meta kind=wheel、spin rudder 540、元件預設 render=wheel）＋木頭雙柱座 `-wheel-stand`（kind=wheel_stand，擺法照抄輪那一條），後甲板中線 x 266（後桅前、羅經櫃後）。⚠ 1660 年代荷蘭船用 whipstaff，遊戲要舵輪（同收穫號）。
- **錨**：共用錨元件 ×2（scale 0.85、kind=anchor、anchor=bower）吊在船頭舷外 x 501.8、ring z 104、錨臂順著船殼切線（rz ±76）、離船殼 5.5 格（試了 x 498–506 × z 102–108）；錨架 `-anchor-gear`（billboard 托板，關聯 `錨架`）1,002 格；錨鏈孔固定點 hawse-S／P (528, ±21, 76)（只登記、沒有開孔）。
- 讀數（`tools/check_stage95.py`，從作品讀）：舵、錨架結果帳 0 差；舵模型 CLI ok、stock-top 8 格內有船殼、舵跟組裝件重疊 0、轉 ±35° 掃進實心 0；錨 2 隻 CLI ok、撞實心 0、腳是錨架、來源有 ring；hawse 在船殼上、在那一舷；問題 0。舵輪與座：撞實心 0、腳下有甲板。遊戲讀的那一份（組裝件 `export format=parts`）：舵、舵輪都有 spin。**反向對照**：`--drop=錨-P` ⇒ 只報 P 舷沒有錨；`draft_rudder_anchor.py --probe=shift=錨-S:-3` ⇒ 只有錨-S 報 1,152 樣本。

## 步驟 12 砲門蓋板（2026-10-26）
工具 `design/tools/portlids.py`（照抄 basecamp 憲法號的通用砲門蓋板工具；改開頭的表成藍鯊號一艘、兩層、一件蓋板、persona gura；`CLOSE_ADJ` 給 砲M-P03／S03 關角 −2°）⇒ `portlids_placement.json`、`verify_portlids.json`、蓋板子作品 `-portlid`（9×9×2：外面船殼褐 136、裡面紅 224、鉸鏈板 73）。
- 封閉砲甲板（main、puente）每個砲門一片 ＝ **22 片**（P 舷 11、rotate 180 − rz，⛔ 不用 mirror=y）；meta kind=portlid、lid_of ＝ 砲的物件 id（照模型 meta 對，22／22 都對上）。
- ⚠ **lid_of 要砲的物件 id ⇒ 要先做步驟 14 的匯入＋`admin.py ids`**，回頭做蓋板，再 reimport（已補進 Ship_Steps 步驟 12 那一行）。
- 鏡板那 2 個船尾砲門沒蓋（工具只處理舷側砲門）—— 記 todo。
- 讀數（`portlids.py check`）：開著撞船 0、撞砲 0；關著撞船最多 2.19%（> 5% 的 0 片）、收砲後撞砲 0；砲門 22／22 蓋滿；鉸鏈中心在鉸鏈下 3.77–3.99；掛上去 cells 162 結果帳 0 差、models_bad 0、鉸鏈最大差 0.0005。**反向對照**：house 0（砲不收）⇒ 22 片全撞砲；mirror=y ⇒ 11 片往上開。

## 步驟 14 給遊戲的 meta 與匯入（2026-10-26）
組裝件 `-assembly` kind=ship、waterline_z 33；匯出 vxk ⇒ Blockside 自己的 worktree（分支 gura/0967-pinas）`admin.py import`（el `ship-pinas`、名字 藍鯊號）⇒ `admin.py ids`（100 個，加蓋板後再 22 個）⇒ reimport。
- 給遊戲那側填 geo 的高度（z 從龍骨底，格 ＝ 0.1 m）：水線 33；甲板 orlop 24、overloop 42、verdek 60、bak 82、halfdek 84、hut 101 ⇒ game.json `geo`：`spar [61,103]`、`marines [55,130]`、`center 75`、`aim 55`、`aimZ [25,400]`、`deckAim [46,76]`、`rigAim [130,380]`；`crew {marines 6, top 1}`。
- 讀數：reimport checksum **162350042**、模型 97、繩 327（猜綁 0）；shipcheck ✗ 0 ⚠ 2（搬火藥 11／12；一個梯子腳被遊戲擺的「帆布櫃」家具擋到）；ladcheck ✗ 0 ⚠ 1；ropecheck 654 端 ok；關聯重疊 0。
- 船卡：599 t、37.1 m、24 門、帆 12、船員 150。選船彈窗（`?pick=@host`）：14.7 節（fun 模式）、吃水 3.29 m、全長 49.8 m、貨艙 225 t。
- 對打（report.py，pinas vs cosecha、seed 1／2、120 秒）：藍鯊號開火 145、命中 62%；砲可開 84%／裝填 14%；砲被打掉平均 2／24；航速時間線 seed 1 最高 5.7 節、seed 2 最高 12.9 節 ⇒ 開得動、砲打得出去。
- **泊位反向對照**（`scratchpad/pinas/berth_fit.cjs`，照 Blocksail 地球儀 docksFit：泊位 loa ≥ 全長、泊位與航道水深 ≥ 吃水 ＋ 1.5）：windward 6 城 61 個泊位 ⇒ large 23／23、titan 6／6 停得進；**small 0／20**（全部太短 36 < 49.8）、boat 0。對照組 30 m 的船 ⇒ small 20／20。

## 步驟 15 交船（2026-10-26）
照 Ship_Game §10 換一艘船時的檢查表逐條看過（遊戲那一份：`admin.py shipcheck --id pinas` ✗ 0 ⚠ 2）：
- ✓ ropecheck 654 端 ok、沒有 bind／snap；組裝件名 ＝ 藍鯊號、船殼帶 sub；mpv 0.1 每件都記、模型明寫 scale；開工前查過現有元件（上面「沿用的現有元件」）。
- ✓ 砲 24、帆桁、舵輪、火藥桶 32、絞盤、羅經櫃、小艇都是外部模型帶 kind；舵 kind=rudder＋stock-top、`__game.lostModels(0)` 是空的；spin：舵 ±35°、舵輪 540°；操舵鏈「舵令 ⇒ 甲板-alcazar/舵輪 ⇒ 舵 100%」。
- ✓ kind=ship waterline_z 33（高度在步驟 14 那一段）；甲板 6 層 kind=deck、梯子 9 座 kind=ladders 四個固定點；ladcheck ✗ 0 ⚠ 1；ratlines 橫繩組、下桅 6 組繩梯；三角帆桁 rig=lateen＋fore；彈藥庫有桶、24／24 門送藥走得到；窗的玻璃獨立關聯 material=glass（225 格）。
- ✓ 繩與帆的端點綁 model:、ropes_broken／sails_broken／models_broken 0；帆 meta 齊、帆桁 sail ＝ 帆名；組裝件 1 元件、空腔 0、link_overlap 0；vxk checksum 跟遊戲那側對過（162350042）。
- ✓ 舷側砲門蓋板 22 片（gun-23／24 是鏡板的兩門，沒蓋，見下）。
- 不適用：槳、撞角、蒸汽、鐵甲與金屬部件、迴旋砲／砲塔、空艙房（沒隔艙，艙房 0）。
- ⚠ 兩條照實留著：送藥手站得到 11／12；船首那座往上甲板的梯腳前面 1–2 格有下甲板的帆布櫃（繞得過去）。

### todo（沒做的，照實留著）
- ~~砲具與砲索、門、廚房、鏡板兩門的砲門蓋板~~ ⇒ 下面「補做」那一段做了。
- 錨鏈孔只登記固定點、沒開孔。艙口沒有艙蓋（本船乾舷高，艙口都在上甲板以上）。shot garland、rammer／sponge 沒做。

## 補做：砲具與砲索、廚房、艙壁門、船尾板砲門蓋板（2026-10-26，Tim「繼續 go」）
- **砲具與砲索**（Ship_Guns §4.4）：plan `gunfittings_build`（照收穫號）；`draft_gunfittings.py` ⇒ `tools/build_gunfittings.py`。子作品 `-gunfittings`（關聯 `砲具`）120 格（船牆的環 96、甲板環 24）、固定點 72；繩 120 ＝ 24 門 × 5（breeching ×2、side tackle ×2、train tackle）。
  - 🩸 M04 的甲板環第一版找不到：P 舷正後方是底艙梯子的井（x 276–290 沒有甲板），兩舷鏡像一起找 ⇒ 兩舷都放不下；往旁邊挪 ±3／±5 繩還擦過井的圍板（x 291）⇒ 加 `deck_ring.lat`（沿砲的側向挪，兩舷同一個 lat），挪 10 格才過。
  - 讀數（`tools/check_stage12.py`）：結果帳 0 差、固定點 72 都在實心上、繩 120 CLI 全 ok、每門五條缺 0、端點對不上 0。**反向對照**：`--drop=ring-砲M-S04-aft` ⇒ 只報那兩條。
- **廚房爐灶**（Ship_Fittings §9.13）：現有元件只有 1850 年代的鐵製爐灶（光榮號、拿破崙號）⇒ 自己做 kombuis：`draft_galley.py` ⇒ `tools/build_galley.py`，子作品 `-galley`（0.05 m，17,548 格：鉛盤、黃磚 IJsselsteen、拱形爐口朝船尾、炭火、鐵板、銅鍋、磚煙囪上段包銅、鐵帽）、上甲板子作品的模型 `爐灶`（scale 0.5、at 469.5,160.5,62、meta kind=galley）；放在船艏樓底下中線，煙囪在兩根橫樑（x 464／480）之間穿過船艏樓甲板 ⇒ 甲板-castillo 刻 8 格（從甲板設計遮罩算，`check_decks.py` 扣掉這個洞）。撞實心 0、腳下 0 懸空、船尾那一面站得住。
- **艙壁門**（Ship_Fittings §9.7）：`draft_doors.py` ⇒ `tools/build_doors.py`，一件門板 `-door`（0.05 m，2×14×32 ⇒ 船上 1×7×16，直條木板＋兩道鐵鉸鏈帶；固定點 hinge-a 上、hinge-b 下 ⇒ 往外開）、6 扇掛在 break 艙壁朝外那一面（後甲板 x 301、船尾樓 x 208 rotate 0；船艏樓 x 435 rotate 180），meta kind=door open=side。撞實心 0、背後都是艙壁（37 格 ＝ 7×16 − 門洞 75）。
- **船尾板兩門追擊砲的蓋板**：`tools/portlids.py` 加 `to_aft`（砲口朝 −x ⇒ 轉成「往外 ＝ ＋y」的座標照舊量，擺法換回 rotate ＋90）⇒ 24 片；舷側 22 片重跑逐位元組相同。鏡板那兩片：鉸鏈 x 157、z 78，鏡板斜 12.8°，關上撞船 0.27%、開口 49／49 蓋滿、開著撞 0。
- **遊戲那側**：Blockside b4326f6（重匯：格 ＋112、繩 ＋120、模型 ＋9；ids 發 galley-1、door-1～6、portlid-23／24、part-13）；shipcheck ✗ 0 ⚠ 8 —— 新的 6 筆是直立的門「正下方沒有空的格 ⇒ 打掉也不進水」（遊戲找門的開口只看門底下那一層；門洞在水線上 2.5 m 以上，照實）。廚房：廚師 1 位、四面都站得住。對打 seed 1／2：開火 203、命中 54%、船員 151。Blocksail cc086ed（Blockside → b4326f6、重套 battle.html）。
