# 拉貝爾號（La Belle）—— 法國 barque，Rochefort 1684（0.1 m／格）—— 建造筆記

委託：Tim 2026-10-26「/scp-task 965 GO」—— TASK-0965《Blocksail》1666 加勒比船型：長型小帆船 barque longue（法），拉貝爾號那型（傘 TASK-0964，erina 開單）。
範圍（遊戲用）：外部完整；內部只做甲板、艙口、梯子、彈藥庫這些遊戲用得到的大致構造。步驟照 `Ship_Steps`（單上的驗收標準）。

## 座標約定
- 空間 352×160×256；X 船長（船頭 +X）、Y 船寬（**中線 ＝ 第 80 格**，鏡像 y ↔ 160 − y）、Z 高度（z 0 ＝ 龍骨底面）；P ＝ y < 80。
- 「在不在船裡」：|y − 80| ≤ 半寬（格心判斷）⇒ 兩舷逐格對稱。
- 0.1 m／格（船殼與組裝件的書卡都記了 meters_per_voxel）。1 pied du roi ＝ 0.3248 m ＝ 3.248 格。

## 作品
- 船殼 `ame-labelle-01m`「拉貝爾號 船殼」：任務作品（commission TASK-0965），tags sub。
- 組裝件 `ame-labelle-01m-assembly`「拉貝爾號」：主作品，關聯 `船殼` at 0,0,0。

## 步驟 3 資料與新圖紙（2026-10-26）
查證：研究代理一輪 ⇒ `references/research_labelle_2026-10-26.md`；主要出處 Grieco 2003（INA Quarterly 30.4，Rochefort 船廠 devis 的尺寸在 Fig.4）—— **ame 自己逐頁讀了 p.4–7、11、13–16**（pypdf 抽文字），devis 9 個數、Joutel 吃水、甲板高度、砲門、砲、迴旋砲都對過原文。Boudriot 的圖版沒拿到 ⇒ 桅帆長度是設計決定。

設計 `design/plan.json`（每個數字的 `src`）；程式（出處：calli-cosecha-01m/design，檔頭都寫了）：
- `lines.py`：艏柱換成冪次曲線 x ＝ forefoot ＋ 14.6·(z／26.8)^0.55（devis 的傾出量在 8 pi 3 po 高）；收穫號照 60.5 格半寬調的常數照半寬等比縮；wing transom 那一格就是 tableau 全寬。
- `draft_lines.py` ⇒ `sheet01_lines_v1.png`、`verify_lines.json`、`masks/hull/hull_01.vox.txt`（48,663 格）。船殼 ＝ 線形實心往裡留 3 格牆（外板 1、肋骨 141、內板 177）；外板水線 z 23 以下灰白 182、以上原木 177。
- `layout.py`＋`draft_layout.py` ⇒ `sheet02_layout_v1.png`、`verify_layout.json`。

| 項目 | 讀數 | devis（GR Fig.4） |
|---|---|---|
| 龍骨 | 146.2 格 | 45 pi ＝ 146.2 |
| 艏柱到艉柱（z 26.8） | 165.7 格（16.57 m） | 51 pi ＝ 165.6 |
| 艏柱傾出／艉柱傾出 | 14.6／4.9 | 4 pi 6 po ＝ 14.6／1 pi 6 po ＝ 4.9 |
| 寬 | 45 格（寬只能奇數） | 14 pi ＝ 45.5 |
| wing transom 寬（z 30） | 33 格 | 10 pi ＝ 32.5（GR 照 1673 年法規推） |
| 吃水 | z 23 | 7 pi ＝ 22.7（Joutel） |
| 排水量（水線下實心 × 1.025） | 87 t | 噸位 40–50 tonneaux（容積噸，只當量級） |
| 船殼牆 | 48,663 格；1 元件、空腔 0、鏡像差 0 | — |

- 甲板（甲板面 z）：貨艙地板 7（x 84–196）、主甲板 27（舷弧 船尾 +2、船頭 +5）、船尾小艙 22（break 後、下沉 2 pi）、後甲板 40（高 3 pi，＋1 給站人頭頂）、船首樓 41（x 189 起）。
- 砲門：每舷 3 個、18 po 見方（5 格）、門檻 1 pi 2 po（4 格），中心 x 98.5、119.5、166.5（v1 等距的第二門落在主桅旁）；4 磅砲 6 門。
- 桅：前桅 x 200（腳在 breasthook）、主桅 x 140（船長中點稍前）、後桅 x 86（break 前，腳在主甲板）、艏斜桅 30° 8 m；主桅頂離龍骨底 18.3 m（ANCRE 模型推 18.7 m，只當量級）；主帆桁 9.2 m（Barroto 16 cubits × 0.5747）。
- ⚠ devis 的艉柱傾出（10.4°）跟 GR 量到殘骸艉柱外面 74°（16°）對不上 —— 本圖照 devis（全長、龍骨、傾出三個數都要對上）。

讀數與反向對照：
- `draft_lines.py --probe=half_beam=3` ⇒ 全寬 45 → 51；站 x 80／120／160／200 的水線半寬 14／22／22／16 → 17／25／25／18（每站 +2～+3，兩頭的收縮 × 3 取整）。
- `draft_layout.py --probe=port=main:2:+3` ⇒ x0 [96, 117, 164] → [96, 120, 164]、邊距 [16, 42] → [19, 39]。
- 產生程式重跑：5 個輸出檔（清單、兩張圖、兩份 verify）逐位元組相同。
- 🩸 v1 的半寬圖像駁船（平行中段 x 95–190）⇒ 船尾收縮 30% → 40%、船頭 68% → 60%、圓舭 2.8 → 2.3、平底半寬 10 → 8；排水量 101 → 87 t。
- 🩸 v1 wing transom 寬 25 格（收穫號的公式要到 z_wt ＋ 6 才全寬）⇒ 改成 z_wt 那一格全寬 ⇒ 33。

## 步驟 4 船殼落格、砲門、塗裝、船尾窗（2026-10-26）
- 船殼：標記 `船殼:begin`（upto=start）→ `design/tools/stamp_lists.py ame-labelle-01m 0 masks/hull/hull_01.vox.txt`（1 刀，placed 48,663 ＝ 清單）→ `船殼:end`。
- 砲門與塗裝：`design/draft_ports.py`（出處收穫號；菱格、粉帶拿掉）⇒ `masks/ports/carve.vox.txt`（500，顏色守門）、`paint.vox.txt`（5,873，stampvox overwrite=1）、`verify_ports.json`、`sheet03_ports_paint_v1.png`。
  - 塗裝（plan.paint）：原木底 177；兩道黑 wale（甲板 −3..−2、＋1..＋2，照舷弧）；upper wale 以上到舷頂下一格藍 frieze 74；每個 x 船殼最高那一層黑 36；砲門框紅 160；tableau（wing transom 以上的船尾面）藍、wing transom 那一列與頂下一列金 248；船尾小艙兩扇窗（寬 5、高 5，玻璃 87、金框）。
  - 🩸 舷頂黑線 v1 照折線四捨五入取 z ⇒ 舷弧那幾段斷斷續續；v2 改成每個 (x, y) 最上一格 ⇒ 內收的舷側每一階都算、滿身黑點；v3 每個 x 船殼最高那一層 ⇒ 連續。（都在落格之前、圖紙上看到的）
  - 🩸 落格後渲圖：船尾樓舷牆頂上零星金點 —— tableau「從最後面往前第一格」在船尾肩膀抓到舷側格。改成只塗 x ≤ x_aft(z) ＋ 2 那一層；`tools/hull_expected.py`（出處收穫號，沒有的清單跳過）先拿舊清單組 ⇒ 跟作品差 0（帳組得對），新清單 ⇒ `tools/delta_apply.py` 換色 18 格（標記 `船尾金點`）。
- 讀數（`design/tools/check_stage3.py`，作品從 export 讀）：
  - **結果帳**：作品 48,163 ＝ 船殼 − 刻 ＋ 換色，缺 0、多 0、色差 0（`船尾金點:end`）。
  - 6 個砲門開口從作品量：裡面還有實心的 0 個。**正向對照**：同一把尺量 `船殼:end` ⇒ 6 個全報（各 75 格）。**反向對照**：`draft_ports.py --probe=skip_port=main:2` ⇒ 只報第 2 門兩舷（各 75）。
  - 船殼線形對照（`tools/check_hull.py`，站距 8、高度每 3 格）：276 點差 0；`probe_x=124`（設計那一站 +3）⇒ 報 12 點、最大 3。
  - 引擎 `stats structure=1 mirror=y:80`：1 元件、空腔 0、鏡像差 0。
- 組裝件 `ame-labelle-01m-assembly` 關聯 `船殼`；過程圖 `overlays/stage4_hull_{bowq,sternq,side}.png`。
- ⚠ 看得到的：艙裡是空的（甲板在步驟 5）；船頭是圓的到舷頂（船首喙、船首像在步驟 6）；tableau 上的百合花、船名在步驟 6。

## 步驟 5 甲板、梯子（2026-10-26）
設計 plan.json `decks_build`；產生 `design/draft_decks.py`（出處收穫號；break 加 bulkhead 開關）⇒ `masks/decks/<層>.vox.txt`、`masks/ladders/<上面那層>.vox.txt`、`ladder_points.json`、`verify_decks.json`、`sheet04_decks_v1.png`；落格 `design/tools/build_decks.py`。
- 甲板（甲板面 z）：貨艙地板 7（x 84–196）、船尾小艙 22（break 後）、主甲板 27（舷弧，x 81 起）、後甲板 40（x ≤ 80）、船首樓 41（x 189 起）。板：艙裡 177、露天 209；樑每 12 格（GR／DX：14 根）寬 2、深 1–2，136；圍欄與 break 141。
- 開口：後艙口 x 126–132、前艙口 168–176（半寬 4）；主艙口 ＝ 貨艙梯子的井（147–161）；桅孔（前 r 2、主 2.5；後桅腳在主甲板 ⇒ 不開）。
- break：x 80 一道艙壁（小艙地板到後甲板，不開門 —— 主甲板到後甲板只有 10 格高，站不了人）＋後甲板邊 5 格胸牆；x 189 船首樓下只有 9 格高 ⇒ 前面不封，只做胸牆。梯子頭留口。
- 梯子 6 座（每 3 格一階、每階 2 格、踏板 7 寬）：貨艙→主甲板（井，x 145）、主甲板→後甲板兩舷（x 89 往船尾、頭 x 78）、小艙→後甲板（井，x 61 往船頭）、主甲板→船首樓兩舷（x 181、頭 x 195）。每層都走得到（reach：hold 1、cabin 1、main 5、quarter 3、forecastle 2）。
- 🩸 v1 小艙梯子放在 dy 8 ⇒ 梯腳落在船尾收窄處的牆裡（腳下沒地板、頭頂撞格）⇒ 中線；v1 主甲板從 x 80 起 ⇒ 跟 break 艙壁疊 33 格 ⇒ 81。
- 貨艙地板底下封死的空氣 386 格（三段）照收穫號的作法填成樑色 136。
- 子作品（parent 船殼、tags sub、0.1 m、352×160×256、at 0,0,0）：`-deck-{hold,cabin,main,quarter,forecastle}`、`-ladders-{main,quarter,forecastle}`（關聯 `梯子`，meta kind=ladders；固定點 `<梯名>.foot／lo／hi／head`）。
- **甲板 meta**（§9.3，`design/decks_meta.tsv`）：每層 `export format=vxk links=none` ⇒ Blockside `src/decks.py` 量 ⇒ 三處照設計改：貨艙地板兩頭太窄、取樣點湊不到兩點 ⇒ 被截成 105–181，改照設計 84–196；小艙改 58–80（包到梯腳 x 60）；後甲板 thick 量成 8（break 艙壁算進去）⇒ 3。level：hold 0、cabin 1、main 2、quarter 3、forecastle 4。
- 預覽 preset：`藏船殼`。

讀數：
- 設計那一側：零件重疊 0、跟船殼重疊 0、每件鏡像差 0、梯子點問題 0、砲門往艙裡被擋 0。
- **結果帳**（`tools/check_decks.py`，每件從匯出讀）：8 件 10,724 格，缺 0、多 0、色差 0；跟船殼重疊 0、彼此重疊 0。
- **組起來**（引擎 stats，組裝件）：58,887 格、1 元件、空腔 0、鏡像差 0。
- **梯子點**（組裝件 parts）：6 座、24／24 點、跟設計差 0；每點那一格空、腳下實心、頭頂 14 格空。
- **反向對照**：`draft_decks.py --probe=drop_ladder=forecastle-S` ⇒ 5 座；船首樓 reach 只剩 forecastle-P、主甲板少一座。
- 產生程式重跑：11 個輸出檔逐位元組相同。
- 過程圖 `overlays/stage5_decks_nohull.png`。
- ⚠ 沒做：空艙房（§9.2；船尾小艙可以當一間，要配功能艙再標）；樓梯自檢（ladcheck）在步驟 14 匯進遊戲之後跑。

## 步驟 6 裝飾（2026-10-26）
設計 plan.json `deco`；產生 `design/draft_deco.py`（本船重寫：收穫號那支是 galleon 的 espolón 與 galleries；船頭外緣、船尾面、船尾側面都從作品匯出量）⇒ `masks/deco/{head,figurehead,bouteilles}.vox.txt`、`fleurs_paint.vox.txt`、`verify_deco.json`、`sheet05_deco_v1.png`。
- 船首喙 `-head`（關聯 `船首喙`，768 格）：knee of head 伸出艏柱 1.5 m（中線 3 格厚、前端上緣金）＋每舷兩根 head rail（FR：小 éperon、每側 2 根 herpes）。
- 船首像 `-figurehead`（外部模型 `船首像`，meta deco=1，97 格）：Mlle de Fontanges —— 藍衣金腰帶、高聳的白色 fontanges 頭飾，1.2 m。🩸 v1 頭飾多一列 ⇒ 艏斜桅半徑 2.5 格內 1 格 ⇒ 少一列，撞格 0。
- 假艉廊 `-bouteilles`（外部模型 `假艉廊`，deco=1，666 格，兩舷在同一件）：船尾兩舷 0.9 m 長、凸出 0.3 m，上蓋下墜、兩扇漆的假窗（FR：fausses bouteilles 只是貼面）。
- tableau 三朵金百合（GR p.4，船殼換色 63 格，標記 `裝飾`）：7×7（🩸 v1 5×7 像三叉戟）。
- 船尾窗玻璃（Ship_Materials §9.5）：船殼裡色 87 的 50 格 `work sub=split … confirm=1` ⇒ `-stern-glass`（雙生關聯 `船殼-窗玻璃`，meta material=glass；拆前拆後組起來逐格相同）；玻璃後面那兩層內板刻穿 66 格（`masks/glass/carve_behind.vox.txt`，顏色守門）⇒ 玻璃後面緊鄰那格空 50／50（14 格往船頭第 3 格碰到側牆 —— 船尾收窄）。🩸 split 不帶 confirm 只是預覽，第一次以為拆了。
- 艉燈（外部模型 `艉燈`，meta kind=light）：三叉戟號的船尾燈 0.5 倍（1.8 m；FR：超過 1 m），站在 taffrail 中間（x 51–53、z 47 上）。
讀數：零件重疊 0、跟船殼重疊 0、每件鏡像差 0、百合花鏡像差 0；艏斜桅撞格 0。**反向對照**：`--probe=fleur_dy=3`（整排往右舷偏 3）⇒ 百合花鏡像差 0 → 37、換色 63 → 41（偏出去的那幾格落到 tableau 邊外）。過程圖 `overlays/stage6_deco_{bowq,sternq}.png`。

## 步驟 7 桅與帆桁（2026-10-26）
設計 plan.json `masts`、`rig_build`；產生 `design/draft_masts.py`（出處收穫號：cofa 換成桅頂橫桁、沒有 bonaventure）⇒ `masks/masts/<桅>.vox.txt`、`masks/yards/lateen-mizzen.vox.txt`、`yards_placement.json`、`yards_lateen.json`、`verify_masts.json`、`sheet06_masts_v1.png`；落格 `design/tools/build_masts.py`。
- 桅（子作品，關聯 前桅／主桅／後桅／艏斜桅）：前桅 x 200 腳 z 7（breasthook）、下桅頂 103.6、上桅頂 155.6；主桅 x 140 腳 z 7、下桅頂 121、上桅頂 183（離龍骨底 18.3 m）；後桅 x 86 腳在主甲板 z 29、頂 94；半徑 主 2.0→1.5、前 1.8→1.3、後 1.3→1.0、上桅 1.4／1.3→0.9／0.8。
- 桅頂橫桁（FR：Boudriot 版沒有桅樓）：trestletrees 沿 x、crosstrees 沿 y，半長 5／6 格。🩸 v1 橫桁放在 dy ±(ceil(r)+1) ⇒ 跟桅頂空一格，組裝件 3 個元件 ⇒ floor(r)+1 緊貼（delta_apply 主桅、前桅各刻 52／44、貼 52／44）。⚠ 遊戲的桅頂水手要平台 ⇒ 本船派不出桅頂水手。
- 艏斜桅：腳立在船首樓甲板（x 205、z 42）、仰角 28°、8 m、半徑 1.8→1.2；從船頭欄杆上方越過 ⇒ 船殼開孔 0 格。🩸 v1 腳在主甲板 x 206、30° ⇒ 會撞船首樓甲板與船頭舷牆。
- 方帆桁（外部模型，放在各自的桅子作品裡；Ship_Setup §2.1 沿用憲法號的元件、只沿長度縮）：本船帆桁短又細 ⇒ 挑憲法號最細的 royal（截面 4×3）：主帆桁 9.2 m ← main-royal（×0.989）、前帆桁 7.6 m ← fore-royal、主／前上桅帆桁 5.5／4.6 m 與 spritsail 5.2 m ← mizzen-royal；brace course −15°、topsail −17°；meta kind=yard、mast、yard、sail、length_m、pivot_anchor、turn_axis、rotate_z_deg。
- lateen（後桅，子作品 `-yard-mizzen-lateen`、398 格、固定點 pivot／sling／fore／peak／jackstay-01..06）：6 m、40°、吊點 40%；meta yard=gaff、rig=lateen；後端沒伸出船尾（−0.37 m）。
讀數：
- 設計：每件鏡像差 0；帆桁撞格 0（6 根）；艏斜桅跳過 3 格（腳貼著船首樓甲板）。
- **結果帳**（`tools/check_stage6.py`）：4 件桅＋lateen 缺 0／多 0／色差 0；船殼 ＝ `裝飾:end`（孔 0 格）差 0；帆桁模型 6 根 meta 與來源固定點問題 0。
- **組起來**：62,842 格、1 元件、空腔 0、鏡像差 0。
- **反向對照**：`--probe=pivot=yard-main-course:-75`（主帆桁吊點降 7.5 m 到甲板附近）⇒ 主帆桁撞格 0 → 38，其他 0。
- 產生程式重跑：9 個輸出檔逐位元組相同。過程圖 `overlays/stage7_masts.png`。

## 步驟 8 索具、帆、旗（2026-10-26）
設計 plan.json `rigging`；產生 `design/draft_rigging.py`（出處收穫號 階段七；沒有桅樓 ⇒ 上桅 shrouds／futtock 綁桅頂橫桁兩端外一格；ratlines 改成橫繩組；channels 每根桅自己的間距、在舷頂那兩格；旗換法國的）⇒ `masks/rigging/channels.vox.txt`、`rigging_plan.json`、`textures/ensign.png`、`verify_rigging.json`；套用 `design/tools/rigging_apply.py`（多一步 `ratlines` ＝ `sub=ratlines`）。
- channels `-channels`（關聯 `支索板`，762 格，兩舷一件）：舷頂那兩格的舷外（砲門頂 z 35 上面）、寬 3；deadeye 每舷 前 3＋1、主 4＋1、後 2（FR：主 4、前 3、後 2）。前桅間距 3 ⇒ backstay 的 deadeye x 189 還在船首樓舷牆上；後桅間距 5。
- 靜索 46：shrouds 18、topmast backstays 4、topmast shrouds 8（桅頂橫桁兩端）、futtock 8、stays 5（fore → 艏斜桅、fore topmast → 艏斜桅帽、main → 前桅腳（船首樓甲板）、main topmast → 前桅橫桁後端、mizzen → 主桅腳）、bobstay 1、艏斜桅 shrouds 2。
- ratlines：橫繩組 6（三根下桅 × 兩舷，step 4、start 5、stop 12、min_span 4）⇒ 40 道。上桅只有兩根 shroud、底下相距 4 格往上收攏 ⇒ 不做；沒有桅樓平台 ⇒ 不標 climb（Ship_Rigging §6）。
- 帆 8：fore／main course、topsail（帆角綁帆桁模型 earing；course 帆腳在舷頂上 3 格，sheet 往後、tack 往前綁舷頂）、spritsail、mizzen lateen（tack 綁主甲板 x 100、sheet 綁船尾舷頂）、ensign（白底三朵金百合，貼圖 `textures/ensign.png`，掛 lateen 後端）、pennant（主桅頂、白藍）。預設風 4.5,−1.5,0、3 秒。
- meta 25：帆 8（kind、mast、sail；旗 flag=ensign／pennant）＋帆自己的繩 17（kind=sheet／tack、sail）。
- 🩸 v1 上桅 shroud 的固定點在桅頂橫桁實心格上 ⇒ 挪到端外一格；v1 bobstay 兩條（艏斜桅 50%、65%）穿過船首喙與船首像 16 格 ⇒ 一條，knee 前端 z 28 → 艏斜桅 75%；v1 上桅 ratlines、後桅間距 3 的 ratlines 都被 CLI 擋下（第一道短於 min_span）⇒ 上桅不做、後桅間距 5（channels delta 刻 12、貼 36）。
讀數：
- 設計：channels 鏡像差 0、跟船上的格重疊 0；固定點落在實心格 0；靜索（兩端各留 3 格）穿過實心 0；帆自己的繩沒 meta 0；繩名重複 0。
- 引擎：繩 103（standing 46、ratlines 40、running 17）全部 ok、broken 0；帆 8 面 ok、sails_broken 0。最鼓：方帆往前 13.6–35.2 格（風從船尾）、lateen 6.6、旗 4.6／7.4。
- **結果帳**：channels 作品 ＝ 清單（delta_apply --dry 差 0）。
- **反向對照**：`--probe=nometa=main-course.sheet-S` ⇒ 「帆自己的繩沒 meta」報那一條。
- 產生程式重跑：4 個輸出檔逐位元組相同。過程圖 `overlays/stage8_rig_bowq.png`。
- ⚠ main course 最鼓 3.5 m（帆高 6.9 m）偏飽（fullness 1.05 照規格，沒調）。

## 步驟 9 砲（2026-10-26）
設計 plan.json `guns_build`；產生 `design/draft_guns.py`（出處收穫號 階段八：船尾追擊砲那段換成迴旋砲）、`design/gunsim.py`（照抄）⇒ `guns_placement.json`、`verify_guns.json`；落格 `design/tools/build_guns.py`；檢查 `design/tools/check_stage8.py`（照抄）。
- 4 磅砲 6 門（GR：6 門鐵 4 磅砲）：風暴角號 6 磅長砲 `summit-stormkaap-01m-gun-6l` 縮 0.375（砲管 2.6 m → GR 的 6 pi ＝ 1.95 m；Ship_Guns §2.2 只差口徑 ⇒ 縮放現有的）、meta kind=gun、gun=4l（砲種表已有 4l「4 磅砲」）；掛在 `甲板-main`，名 `砲M-<S|P>01..03`；P 舷 mirror=y。
- 迴旋砲 8 門（Barroto「eight flues」）：皇家號叉架後膛迴旋砲 `apex-one-reale-01m-gun-pierrier` 縮 0.39（1.9 m → 出土那門 1.478 m）、meta gun=pierrier、mount=turret、arc −80,80、rate 45（照皇家號、越嶺號）；pivot 站在舷牆頂（那一欄最高那一層、牆厚中間）：後甲板 x 60、72（`甲板-quarter`）、船腰 x 108（`甲板-main`）、船首樓 x 212（`甲板-forecastle`），名 `迴旋砲-<S|P>01..04`。
- 擺法：舷側砲從船殼外面沿砲身往裡退（0.5 格一步）到零碰撞（格心＋八角、inset 0.2）；退 2 格、砲口伸出 5.69 格、砲軸 z 33–34。
- 🩸 v1 甲板高度從船殼外緣往裡數 4 個 y 點取最高 ⇒ 兩舷外緣差一格（S 是 max＋1、P 是 min），P 踩到前艙口圍欄、S 沒有 ⇒ S03 浮在甲板上一格（support 0）、兩舷不對稱 ⇒ 改成從中線對稱取 dy 6..12。
讀數：
- 設計：14 門全部 ok（零碰撞、砲口伸出、砲口空、腳下有甲板 support 1.0）；砲跟砲不撞；兩舷對稱差 0。
- 作品（`tools/check_stage8.py`，從 CLI 讀）：模型 14＝設計 14、CLI ok 14；參數差 0；外框（gunsim vs CLI）最大差 0.045 格；碰撞 0；砲口不在船殼外 0；meta 不合 0（4l 6、pierrier 8）。
- **反向對照**：`--probe=push=砲M-S01:4`（往外推 4 格）⇒ 那一門碰撞樣本 2,261，其他 0。
- 過程圖 `overlays/stage9_guns.png`（sails=0）。
- ⚠ 沒做：砲具與砲索（Ship_Guns §4.4，「要的話」；小船、甲板窄）；砲門蓋板不做（露天甲板舷牆上的砲門，Ship_Steps 刪了步驟 12 —— GR p.13 說有出土的砲門蓋，⚠ 遊戲那側蓋板是給封閉砲甲板防進水用的）。

## 步驟 10 彈藥庫與甲板物件（2026-10-26）
設計 plan.json `gear_build`；產生 `design/draft_gear.py`（出處收穫號 階段九：範圍、小艇架的量測高度換本船）⇒ `masks/gear/{magazine,skids}.vox.txt`、`gear_placement.json`、`verify_gear.json`；落格 `design/tools/build_gear.py`；檢查 `design/tools/check_stage9.py`（need 換成 powder、binnacle、boat）。
- **彈藥庫** `-magazine`（關聯 `彈藥庫`，meta kind=magazine、pos=aft、powder_lb=1600；2,208 格）：貨艙後段 x 88–116、地板 z 10、頂 z 24（主甲板樑下）；門朝船頭（x 116，比貨艙地板高 3 格、一步跨得上）、對著貨艙梯子（腳 x 144）。銅皮 168、松木地板 177、橡木框 136。固定點 blast (103,80,18)、door (116,80,11)。
  火藥桶 16 桶（憲法號 -powder-barrel 0.2、kind=powder、powder_lb 100）：底層 14、木架 2。⚠ 16 是照收穫號的每門 2.6 桶換算，不是史料。
  🩸 v1 x 86–104、地板 z 8、走道 3 ⇒ 一桶都擺不下；v2 走道 1 ⇒ 4 桶（船尾貨艙 V 形底，z 9 那層窄）⇒ 往船頭延長、地板抬到 z 10。
- **小艇架** `-boat-skids`（關聯 `小艇架`，280 格）：x 148、176 兩座橫架，樑 z 37–38、立柱 |dy| 6–7。主甲板太短，兩舷的 4 磅砲往裡退幾乎在中線碰頭（GR p.13）⇒ 小艇架在砲上面。
- 模型：小艇（餘燼號 cutter 縮成 4 m，kind=boat、length_m 4；FR：甲板上一艘）z 明寫 39 —— 🩸 v1 自動量到 z 31：砲是模型、不在格網裡，量不到 ⇒ 小艇會穿進兩門 4 磅砲；羅經櫃（夜隼號，kind=binnacle）主甲板 x 92 右舷（FR：後桅右側；後桅旁被後甲板梯子的 stringer 擋）；爐灶（光榮號縮 0.18，deco=1）船首樓下右舷（FR）—— 那裡只有 8 格高、廚師站不下 ⇒ 不標 kind=galley。
- 沒做：絞盤（Boudriot 是船首樓下的 windlass，沒有元件也沒有 kind）；門與艙蓋（艙口都在主甲板上，Ship_Fittings §9.7：沒有門的開口遊戲不當進水口）；抽水機由遊戲自己生。
讀數：
- **結果帳**：彈藥庫 2,208、小艇架 280，缺 0／多 0／色差 0；新格落在實心上 0、封閉空腔 0、浮空 0；鏡像差 0。
- 模型 19＝設計、CLI ok 19；參數差 0、撞實心 0、腳下 12 格內沒有實心 0、模型彼此重疊 0。
- 彈藥庫：powder_lb 1,600 ＝ 16 桶 × 100；blast 空氣、door 空氣且腳下實心。
- 組起來：66,092 格、1 元件、空腔 0、鏡像差 0。
- **反向對照**：`--probe=nokind=小艇` ⇒ 沒 kind 的多報 小艇（爐灶本來就是 deco）。

## 步驟 11 舵、舵柄、錨（2026-10-26）
設計 plan.json `rudder_anchor_build`；產生 `design/draft_rudder_anchor.py`（出處收穫號 階段九半：多一支舵柄、錨避開船首樓的迴旋砲）⇒ `masks/rudder/{rudder,tiller,anchor_gear}.vox.txt`、`rudder_anchor_placement.json`、`verify_rudder_anchor.json`；落格 `design/tools/build_rudder_anchor.py`（舵加 spin）；檢查 `design/tools/check_stage95.py`（中線改讀 plan）。
- **舵** `-rudder`（組裝件模型 `舵`，656 格）：沿艉柱後緣（斜 10.36°）從龍骨底到 wing transom（z 31）；3 格厚、舵葉 0.9 m 收到 0.3 m 的舵頭；水線下白、上黑、每 7 格鐵箍；前緣兩側削 1 格。meta kind=rudder、hinge (60, 80.5, 0)、axis (−0.1798, 0, 0.9837)、max_deg 35、turn_axis=hinge、spin=rudder、spin_k 35、±35、lag 0.3（Ship_Helm §9.8.1）；固定點 stock-top (52,80,31)。
  舵頭到 wing transom 為止 ⇒ 不擋 tableau 中間那朵百合花。
- **舵柄** `-tiller`（`甲板-quarter` 的模型 `舵柄`，50 格）：FR 的 barre franche、沒有 whipstaff ⇒ 獨立模型 kind=tiller（操舵鏈：舵柄被打掉 ⇒ 舵效照鏈扣）；舵頭從後甲板 tableau 內側冒出來（x 57、1×3、z 41–44），舵柄沿中線往前到 x 76、z 43–44；固定點 spin-a／spin-b（垂直軸）、spin=rudder、spin_k 35。⚠ 舵頭在 wing transom 與後甲板之間那一段沒畫（藏在船尾牆裡）。🩸 v1 舵柄 z 42–43 撞到小艙梯子井的圍欄 1 格 ⇒ 抬一格。
- **錨**：共用錨元件（憲法號 bower）縮 0.3（錨幹 1.7 m）×2，meta kind=anchor、anchor=bower，掛在錨架 `-anchor-gear`（關聯 `錨架`，322 格，兩舷 billboard）；照收穫號的搜法：錨臂順著船殼切線（rz ±76）、往外推到零碰撞 ⇒ x 206、ring z 42、離船殼 6.5 格。錨鏈孔固定點 hawse-S／P (216, 90／70, 35)（只登記、沒開孔）。
讀數：
- 設計：舵、舵柄、錨架落在實心上 0、鏡像差 0；舵柄的舵頭腳下都是甲板。
- **結果帳**：舵 656、錨架 322 缺 0／多 0／色差 0（舵柄 50 同清單，見 parts 讀回）。
- 舵：stock-top 8 格內有船格（曼哈頓 2）；跟組裝件重疊 0；轉 ±35° 掃進實心 0。
- 錨 2 隻：撞實心 0、腳落在錨架上、來源有 ring；hawse 兩舷都在船殼格上。檢查問題 0。
- 讀回（`export format=parts`）：舵、舵柄的 meta 都有 spin。
- 組起來：66,414 格、1 元件、空腔 0、鏡像差 0。
- **反向對照**：`--probe=shift=錨-S:-6` ⇒ 錨-S 撞 831、錨-P 0。

## 步驟 14 給遊戲的 meta 與匯入 Blockside（2026-10-26）
- 船殼關聯 meta kind=ship、waterline_z=23。`work sub=ropecheck`：繩 103、206 端全部 ok（沒有 bind／snap／odd／manual）。
- 在自己的 Blockside worktree（從 dev cdf552e 開，`_cache` 從共用工作區抄進去）：`admin.py import --work ame-labelle-01m-assembly --id labelle --name 拉貝爾號` ⇒ game.json 只多一行（這次沒有重排整份）；`admin.py ids --id labelle` 發號（ladders-1..3、magazine-1…）。
- 第一次匯入檢查 ✗ 3：① 後甲板右舷梯子的梯腳出口被羅經櫃（主甲板 x 92）與第 1 門砲堵住 ⇒ 羅經櫃搬到後甲板舵頭右舷（x 60、dy +8；`build_gear` 重放、`unmodel` 舊的）；②③ 後甲板、船首樓找不到 9×9 的火藥取用點 ⇒ 彈藥庫關聯 meta `hoist=ladders-2#quarter-S,ladders-3#forecastle-S`（Ship_Magazine §8：桶擺在梯腳那一層、送藥手在梯頭拿）。⇒ `reimport`、`ids`。
- game.json 手填 ships[labelle]：geo spar [28,42]、marines [33,54]、center 45、aim 28、aimZ [5,185]、deckAim [28,40]、rigAim [55,180]（照本 notes 的高度：甲板 27–42、砲軸 33–34、主桅頂 183）；cfg pump 2、speed 3、agile 4、upwind 2（⚠ 照夜隼號的設計值）；crew 軍官 2、舵手 1、桅頂 0、陸戰隊 4、marineGap 14、handsK 0.25、航海士 0；names。
- **匯入檢查 ✗ 0、⚠ 7**：送藥手 5／7、軍官 1／2 站得到；梯腳前面擋到但走得出去（貨艙梯子：nav 生的木工台；小艙梯子：船殼；船首樓右舷梯子：取用點的火藥桶 —— 遊戲那側的修法）；主甲板第 3 門兩舷的取用點跟砲尾不連通（送藥手直線穿過去）。**樓梯自檢 6 座 ✗ 0、⚠ 3**；火藥 12／14 門走得到取用點；操舵 舵令 ⇒ 舵柄 ⇒ 舵 100%；迴旋砲 8 門 turret ±80°。
- 對拍（無頭 Chrome、headless=1、#dump；對照組 `admin.py snapshot`）：`?demo=60&dump=1&seed=3` dd577bb1b574、`&seed=2&ship=falcon,stormkaap` 43e5b252e487 —— 改之前／之後各兩次、合併後再一次，全部逐位元組相同。戰局：`?demo=120&seed=3&ship=labelle,falcon` ⇒ 拉貝爾號開 41 發、命中 22、斷一根桅、航速 4–13 節。
- 提交：Blockside 2378dcb（匯入）＋ f7ad2c0（合進 dev，成品照合併後的來源重建、srccheck 對得上），已推 dev（一起推上去的還有共用 dev 上先前沒推的 1c4fc7f「每艘船自己的旗」）；`_cache/labelle.vxk` 抄進共用工作區；worktree、分支收了。
- 新做的元件不用標 render（沒有新的桶、槳、舵輪；舵柄、船首像這幾件很小）。

## 步驟 15 交船（2026-10-26）
給遊戲那側填 geo 的高度（格的 z；0.1 m／格）：龍骨底 0、設計水線 23、貨艙地板 7、船尾小艙 22、主甲板 27（舷弧 船尾 29、船頭 32）、後甲板 40、船首樓 41、舷頂 船腰 37–39／艏艉樓 47；砲門 z 31–36、4 磅砲軸 z 33–34、迴旋砲軸 z 41.7（船腰）／51.7（艏艉樓）；桅頂橫桁 前 103.6／主 121、上桅頂 前 155.6／主 183、後桅頂 94；船殼 x 51（tableau）–225（艏柱），船首喙到 x 239、艏斜桅頂 x 275。
遊戲那側的 vxk 指紋：`labelle.vxk` c:83fa5726f3a8dccb3ed0e97180e9eb51183501ac（Blockside f7ad2c0 的 config/vxk_lock.json）；步驟 16 之後 c:03d4444532bf2db69bd7e6f819ec84acb6ff20dd。

Ship_Game §10 檢查表：
| 項目 | 本船 |
|---|---|
| ropecheck | ✓ 103 繩、206 端全 ok |
| 組裝件名 ＝ 船名、船殼「拉貝爾號 船殼」帶 sub | ✓ |
| meters_per_voxel、模型明寫 scale | ✓（每件子作品 0.1；模型 scale 都明寫） |
| sub=components 先查、能用的都引用 | ✓ 砲（6l→4l、pierrier）、帆桁（憲法號 royal）、小艇、羅經櫃、火藥桶、錨、燈、爐灶；新做的只有本船的個性件（船首像、假艉廊）與舵、舵柄 |
| 槳帆船／撞角 | 不適用 |
| 爐灶：廚房或裝飾二選一 | ✓ 廚房 kind=galley（步驟 16：挪到船首樓後緣中線，廚師站主甲板；v1 是裝飾 deco=1） |
| 缺的砲種做成通用部件 | 不適用（4l、pierrier 都在砲種表） |
| 砲、帆桁、火藥桶是模型且帶 meta；甲板物件帶 kind | ✓ |
| 舵是模型、kind=rudder、stock-top；spin | ✓ |
| 操舵鏈：舵柄 kind=tiller | ✓ 匯入檢查「舵令 ⇒ 舵柄 ⇒ 舵 100%」 |
| kind=ship waterline_z；notes 寫高度 | ✓ |
| 梯子 kind=ladders、四點 | ✓ 6 座 24 點 |
| 樓梯自檢 ✗ 0 | ✓（⚠ 3，見步驟 14） |
| ratlines 是橫繩組；繩梯 climb | ✓ 橫繩組 6；前、主桅下桅 4 組 climb=1（步驟 16：head 踩在 crosstree 上）；後桅沒有 crosstree ⇒ 不標 |
| 彈藥庫有火藥桶 | ✓ 16 桶；火藥 14／14 門走得到（步驟 16 主甲板接成一塊之後；v1 12／14） |
| 甲板 kind=deck、每層有梯子 | ✓ 5 層 |
| 三角帆桁 yard=gaff＋rig=lateen＋fore | ✓ |
| 材質（鐵甲、金屬） | 不適用（全船木頭） |
| 窗的玻璃獨立關聯 material=glass | ✓ `船殼-窗玻璃` 50 格，後面刻穿 |
| 空艙房 | ✓ 1 間：貨艙前段 `甲板-hold/艙房/fore` 2.1 × 1.5 × 1.8 m（步驟 16；船尾小艙扣掉梯子只剩 0.5 m 寬） |
| 砲退到零碰撞、砲口在船殼外 | ✓ 14 門 |
| 砲身砲座拆兩件、裝甲、砲塔 | 不適用 |
| 迴旋砲 | ✓ mount=turret ±80（照皇家號；不是 pivot 砲門，不用量每個角度） |
| 蒸汽艦 | 不適用 |
| 露天出入口有門 | ✓ 後艙口、主艙口兩扇門 kind=door；前艙口封死、走得過去（步驟 16）；船尾小艙的井不做（舵柄掃在上面、離水線 1.8 m） |
| 舷側砲門蓋板 | 不做（露天甲板舷牆上的砲門，Ship_Steps 刪了步驟 12） |
| ropes／sails／models broken 0 | ✓ |
| 帆、旗、帆自己的繩 meta | ✓ 帆 8、繩 17 |
| 組裝件 1 元件、空腔 0、link_overlap 0、對稱 | ✓ |
| 產生程式重跑逐位元組相同 | ✓（每一步各自量過） |
| 匯出 vxk、對 checksum | ✓ 上面那一行 |
| 匯入檢查 ✗ 0、⚠ 都看過 | ✓ ⚠ 7 逐條列在步驟 14；步驟 16 之後 ⚠ 5（主甲板第 3 門取用點不連通那兩條沒了） |
| 舵、舵柄 spin | ✓ |

## 步驟 16 補做：艙蓋、廚房、絞盤、艙房、下桅繩梯（2026-10-26）
Tim 2026-10-26「測試ok 加上還沒做的部分吧（另外廚房可以套用遊戲內的功能艙室讓它有功能 目前應該已經加了廚師？」
設計 plan.json `fit_build`；產生 `design/draft_fit.py` ⇒ `masks/fit/{hatch-aft,hatch-main,hatch-fore,windlass,hold_room}.vox.txt`、`fit_placement.json`、`verify_fit.json`；落格 `design/tools/build_fit.py`；讀數 `design/tools/check_stage16.py`。
- **艙蓋**：後艙口 `-hatch-aft`（9×11，蓋在圍板上 z 30、掀 100°）、主艙口 `-hatch-main`（15×11，嵌在圍板裡 z 29、掀 45°：圍板頂跟著舷弧前高後低、兩舷夾著小艇架立柱）⇒ 主甲板子作品的模型 kind=door、固定點 hinge-a／b（沿 +x、左舷那一邊）；遊戲讀到開口 63、157 格。
  前艙口 `-hatch-fore`：🩸 v1 也是門 ⇒ 遊戲的走路格（下面）斷在這裡 ⇒ 改成封死、嵌在圍板裡、頂跟圍板頂齊（z 30）的一層板，關聯 `艙蓋-前`（不是門、沒有開口）；走路點 20／20 站得住（地板 −2～+3 格內）。船尾小艙的井不做（舵柄整條掃在上面；離水線 1.8 m）。
- **廚房**：爐灶（光榮號元件 0.18）從船首樓下右舷 x 203（v1 deco=1）挪到船首樓後緣、中線 x 189.5–197.5，meta kind=galley（deco 刪掉）；爐門（元件 x=0 面）朝船尾 ⇒ 廚師站主甲板露天那一段（x 184–188）。量法照遊戲（外框外 2 格的四個面中點、3 格內有走路格）：新位置 1 面、v1 位置 0 面（反向對照 `--probe=galley_x=203 --probe=galley_y=88.5`；外框跟 v1 匯出的逐位相同）。遊戲裡站得住的面 3。
- **絞盤** `-windlass`（關聯 `絞盤`，280 格）：船首樓下 x 208、兩根立柱 y 72–73／87–88（主甲板頂 z 32 到船首樓底 z 40）、橫的絞筒 y 74–86（半徑 0.22 m、軸 z 35.5），撬棍孔照離中線每 3 格 ⇒ 🩸 v1 照 y % 3 ⇒ 鏡像色差 20 對 ⇒ delta_apply 換色 45。不標 kind。
- **艙房** `-hold-room`（貨艙地板子作品的關聯 `艙房`，meta kind=rooms，631 格）：x 163 一道橫艙壁（貨艙地板到主甲板底下、中線門洞 y 78–82 高到 z 22）；框 `fore.min` (164,73,8)、`fore.max` (184,87,25)、`fore.door` (163,80,8) ⇒ 2.1 × 1.5 × 1.8 m、框內非空氣 0、整格有地板；反向對照 `--probe=room_y0=70` ⇒ 非空氣 22。船尾小艙最大的全空氣框只有 0.5 × 1.5 m ⇒ 不標。遊戲 `rooms.py check` ✓。
- **下桅繩梯**：前、主桅下桅兩舷 4 組 climb=1（foot 舷牆內側甲板、head 踩在 crosstree 上；前桅 foot 從 x 195.5 挪到 198 避開船首樓梯頭）；後桅沒有 crosstree ⇒ 不標。head 不在甲板上 ⇒ 只有第一人稱爬。
- **主甲板接成一塊**（遊戲那側量到的，見下面）：`decks_build.ladders` 的 hold 梯子加 `well_keep_fwd 1` ⇒ `draft_decks.py` 井最前一欄（x 161）|dy| 4–5 留成甲板 ⇒ 主甲板多 4 格（161,75／76／84／85,28），其他 9 個輸出檔逐位元組相同；delta_apply 貼 4。
讀數：
- 設計：艙蓋、爐灶、絞盤、艙壁撞實心 0、撞模型 0；產生程式重跑 7 個檔逐位元組相同。
- **結果帳**（check_stage16，組裝件從匯出讀）：67,410 ＝ 落格前 66,414 ＋ 本步 996，缺 0、多 0、色差 0；部件外框、meta、固定點、繩梯 climb／foot／head 全對（問題 0）。check_decks 8 件問題 0。
- 組起來（引擎 stats）：67,410 格、1 元件、空腔 0、鏡像差 0。
- **遊戲那側**（Blockside worktree，reimport ＋ ids）：🩸 第一次 reimport 廚房沒開：「四個面都沒有連得到待命那一層的走路點」⇒ 在頁面讀走路格：主甲板分三塊 —— 船尾大塊（後甲板梯子）、梯頭那一小塊 x 163–167（貨艙梯子的梯頭；前後是主艙口的井與前艙口、兩舷是第 3 門砲的外框，外框從 x 163.3 起）、船頭那一塊（船首樓梯子、爐灶）；待命那一層 ＝ 最低那座梯子的下端 ＝ 貨艙 ⇒ 預備水手上來只到得了中間那一小塊（v1 就這樣，匯入檢查沒報）。遊戲每 2 格一點、只看那一根格柱（navZ）⇒ 補井的兩角＋前艙口封死。之後：主甲板 1 塊（511 點）、五層各 1 塊、六座梯子都接同一塊；廚房 1 座、廚師 1／1、站得住的面 3；火藥 12／14 → 14／14；匯入檢查 ✗ 0、⚠ 5；樓梯自檢 6 座 ✗ 0、⚠ 3（沒變）；門 2 扇（開口 63、157）；船員 45 → 46。
- 對拍（無頭 Chrome、headless=1；對照組 `admin.py snapshot refs/remotes/dev/dev`）：`?demo=60&dump=1&seed=3` dd577bb1b574、`&seed=2&ship=falcon,stormkaap` 43e5b252e487，改之前／之後相同。
