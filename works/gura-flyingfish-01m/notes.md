# 飛魚號（Flying Fish）—— 牙買加／百慕達單桅船 sloop（0.1 m／格）—— 建造筆記

委託：TASK-0971（Tim 2026-10-27「/scp-task 971 GO」；母單 TASK-0964 的 8 種候選之一）：《Blocksail》1666 加勒比船型 —— 牙買加／百慕達單桅船 sloop，商、海盜都用。⚠ 年代偏晚（牙買加型 1670 年代才有記載），當「泛用的小單桅船」。照造船規格雕刻、匯入 Blockside、接進 Blocksail 船型清單。
流程：照 `Ship_Steps` 步驟表（貼在 TASK-0971 的驗收標準），每一步只讀那一行寫的文件。

## 座標約定（照拉貝爾號，產生程式也從它抄來）
- 空間 400×160×320；X 船長（船頭 +X）、Y 船寬（**中線 ＝ 第 80 格**，鏡像 y ↔ 160 − y）、Z 高度（z 0 ＝ 龍骨底面）；P ＝ y < 80。
- 「在不在船裡」：|y − 80| ≤ 半寬（格心判斷）⇒ 兩舷逐格對稱。
- 0.1 m／格（船殼、組裝件的書卡都記了 meters_per_voxel）。1 ft ＝ 0.3048 m ＝ 3.048 格。

## 作品
- 船殼 `gura-flyingfish-01m`「飛魚號 船殼」：任務作品（委託 TASK-0971、10 token 已發），`tags=sub`。
- 組裝件 `gura-flyingfish-01m-assembly`「飛魚號」：主作品（沒標 sub），parent 船殼，關聯 `船殼` at 0,0,0。
- 子作品照拉貝爾號的拆法（甲板每層一件、梯子、桅、帆桁、裝飾、彈藥庫、舵、錨架…），parent 船殼、`tags=sub`、0.1 m。

## 產生程式
- `design/` 整套從拉貝爾號 `ame-labelle-01m/design/` 抄來（它又出自收穫號 `calli-cosecha-01m/design/`）：38 個 .py 的作品 id、persona、船名、作品尺寸已換（每個檔第一行寫了出處）；`plan.json` 照 sloop 重寫（拉貝爾號那份留成 `plan_labelle_ref.json` 對照）。

## 沿用的現有元件（`work sub=components`，2026-10-27 查）
- 砲：夜隼號 4 磅長砲 `summit-night-falcon-01m-gun-4l`（gun 4l）；迴旋砲 皇家號 `apex-one-reale-01m-gun-pierrier`（gun pierrier）。
- 錨 `basecamp-frigate-constitution-01m-anchor`、火藥桶 `basecamp-frigate-constitution-01m-powder-barrel`、小艇 `basecamp-ember-01m-boat`（縮）、羅經櫃 `summit-night-falcon-01m-binnacle`、爐灶 `kaguya-gloire-01m-galley`（縮）、船尾燈 `gura-tridente-01m-lantern`。
- 帆桁：方帆桁照拉貝爾號的做法縮憲法號的 royal；斜桁（gaff）、下桁（boom）本船自己做（拉貝爾號只有 lateen）。
- 自己做：舵與舵柄（sloop 用舵柄、沒有舵輪）、船名板／船尾裝飾。

## 步驟 3 資料與新圖紙（2026-10-27）
查證：研究代理一輪 ⇒ `references/research_sloop_2026-10-27.md`（gura 對過 Chapelle 1930 p.9–10 原文、圖版 p.11 圖下尺寸、Exquemelin 1893 全文沒有 "sloop"）。單上四條說法：① 1670 年代 ✗（出處撐不住；牙買加最早的 "sloop" 字樣是 1670-12 Modyford 的 the Betty sloop）② 百慕達 17 世紀中（Jarvis）✗ 張冠李戴 ③ Evans 2007 ✓ ④ 21 m ✓／7–9 m 查不到原文。
**1660–1700 沒有一艘有完整尺寸的 sloop** ⇒ 線形與比例照 Chapman 的百慕達 sloop（約 1750；`references/chapelle1930_p11_*`），縮到 1680–1700 年小船的噸位 35 t（× 0.675）。

設計 `design/plan.json`（每個數字的 `src`：CH 原文／M 量圖／R 研究／設計決定）；程式：
- `lines.py`：拉貝爾號那支加 **drag**（龍骨往船尾越深 3.5°）—— 剖面在龍骨座標算（zk ＝ z − kz(x)）、水線甲板舷頂在世界座標是平的；艏柱世界 x 用定點迭代。
- `draft_lines.py`：devis 對照換成 Chapman 對照（LBP、寬、船尾／船頭吃水、艉柱傾、BOM 噸位）。
- `layout.py`、`draft_layout.py`：帆桁可以直接寫長度與 z（gaff、boom 帶仰角）；圖上畫斜桁主帆、topsail、兩面艏帆；讀數多 gaff 峰、boom 尾、boom 在船尾舷頂上幾格。

| 項目 | 讀數 | Chapman × 0.675（× 2.057 格／ft） |
|---|---|---|
| LBP（水線 z 25，艉柱後緣到艏柱） | 125.3 格（12.5 m） | 60′9″ ⇒ 125.0 |
| 寬 | 43 格 | 21′2″ ⇒ 43.6 |
| 吃水 船尾／船頭 | 25.0／17.95 | 12′3″ ⇒ 25.2／量圖 8.7 ft ⇒ 17.9 |
| 艉柱傾 | 22° | 量圖 22° |
| BOM 噸位 | 34.6 t | 目標 35 t |
| 甲板長（z 30） | 12.98 m | — |
| 排水量（水線下 × 1.025） | 51 t | — |
| 船殼牆 | 36,157 格；1 元件、空腔 0、鏡像差 0 | — |

- 甲板（甲板面 z）：貨艙地板 9（x 107–196）、主甲板 30（舷弧 船尾 +2、船頭 +5，x 105 起）、船尾艙房 21（x ≤ 103）、後甲板 40（x ≤ 103）；break 在 x 104。
- 砲門：每舷 2 個（x 120.5、178.5）、5×5、門檻 3；4 磅砲 4 門。
- 桅：x 165（腳）後傾 14°、腳 z 8.5、桅頂橫桁 112.5、桅頂 168.5（離水線 14.4 m）；下帆桁 6.0 m @112、topsail 帆桁 4.5 m @141、gaff 5.1 m @108 仰 30°（峰 96, 133.5）、boom 12.2 m @46 仰 8°（尾 34.8, 63；伸出船尾 3.5 m、在船尾舷頂上 9 格）；艏斜桅腳 (198, 39) 仰 20° 10 m（頂 292, 73）。
- 🩸 v1 一層平甲板 ＋ 船尾 1.5 m 高的舷牆 ⇒ 改成後甲板（CH 的高船尾）＋ 底下艙房；v2 艙房地板 z 17 ⇒ x 90 內寬只有 0.3 m（船尾深 V）⇒ 21、後甲板 37 → 40；boom jaws 1.2 m 掃過後甲板只離地 0.9 m ⇒ 1.6 m、仰 8°。

讀數與反向對照：
- `draft_lines.py --probe=half_beam=3` ⇒ 全寬 43 → 49；站 x 80／120／160／200 的水線半寬 13／19／21／12 → 15／22／24／13。
- `draft_layout.py --probe=port=main:1:+3` ⇒ x0 [118, 176] → [121, 176]、間距 53 → 50。
- 產生程式重跑：5 個輸出檔（清單、兩張圖、兩份 verify）逐位元組相同。

## 步驟 4 船殼落格、砲門、塗裝、船尾窗（2026-10-27）
- 船殼：標記 `船殼:begin`（upto=start）→ `design/tools/stamp_lists.py gura-flyingfish-01m 0 masks/hull/hull_01.vox.txt`（1 刀，placed 36,157 ＝ 清單）→ `船殼:end`。
- 砲門與塗裝：`design/draft_ports.py`（出處拉貝爾號；多一個 `paint.frieze_rows`：frieze 只漆舷頂下幾列）⇒ `masks/ports/carve.vox.txt`（324，顏色守門 carvevox）、`paint.vox.txt`（2,572，stampvox overwrite=1）、`verify_ports.json`、`sheet03_ports_paint_v1.png`；標記 `砲門塗裝:begin／end`。
  - 塗裝（plan.paint）：原木底 177；一道黑 wale（主甲板 −2..−1，照舷弧、往船尾延伸到後甲板底下）；舷頂下 3 列赭紅 168；每個 x 船殼最高那一層黑 36；砲門框紅 160；方艉（wing transom z 24 以上）赭紅、wing transom 那一列與舷頂下一列金 248；船尾艙房兩扇小窗（3×4、z 28–31、玻璃 87、金框）。
  - 🩸 v1 wale 到舷頂整片赭紅 ⇒ 整艘看起來是一塊紅 ⇒ 只漆舷頂下 3 列（落格之前、圖紙上看到的）。
- 讀數（作品從 export 讀）：
  - **結果帳**（`tools/check_stage3.py . mark=砲門塗裝:end`）：作品 35,833 ＝ 船殼 − 刻 ＋ 換色，缺 0、多 0、色差 0。
  - 4 個砲門開口裡還有實心的 0 個；**正向對照** 同一把尺量 `船殼:end` ⇒ 4 個全報（各 75 格）；**反向對照** `draft_ports.py --probe=skip_port=main:2` ⇒ 只報第 2 門兩舷（各 75）。
  - 船殼線形對照（`tools/check_hull.py`，站距 8、高度每 3 格，`船殼:end`）：結果帳 36,157 缺 0／多 0／色差 0；200 點差 0；`probe_x=124`（設計那一站 +3）⇒ 報 13 點、最大 3。
  - 引擎 `stats structure=1 mirror=y:80`：1 元件、空腔 0、鏡像差 0。
- 過程圖 `overlays/stage4_hull_{bowq,sternq,side}.png`。⚠ 艙裡是空的（甲板在步驟 5）。

## 步驟 5 甲板、梯子（2026-10-27）
設計 plan.json `decks_build`；產生 `design/draft_decks.py`（出處拉貝爾號，沒改邏輯）⇒ `masks/decks/<層>.vox.txt`、`masks/ladders/<上面那層>.vox.txt`、`ladder_points.json`、`verify_decks.json`、`sheet04_decks_v1.png`；落格 `design/tools/build_decks.py`。
- 甲板（甲板面 z）：貨艙地板 13（x 112–188）、船尾艙房 21（x ≤ 103）、主甲板 30（舷弧，x 105 起）、後甲板 40（x ≤ 104，蓋住 break 艙壁頂）。板：艙裡 177、露天 209；樑每 12 格寬 2、深 1–2，136；圍欄與 break 141。
- 開口：主艙口 ＝ 貨艙梯子的井（x 133–147）、前艙口 185–191（半寬 4）、桅孔 r 2.5。
- break：x 104 一道艙壁（艙房地板到後甲板，不開門）＋後甲板邊 5 格胸牆、兩座梯子頭留口。
- 梯子 4 座（每 3 格一階、每階 2 格、踏板 7 寬）：貨艙→主甲板（井，x 131 往船頭）、主甲板→後甲板兩舷（x 112 往船尾、頭 x 101）、艙房→後甲板（井，x 101 往船尾、頭 x 83 —— 後甲板只有 3 m 長，往船頭上會頂到 break）。每層都走得到（reach：hold 1、cabin 1、main 3、quarter 3）。
- 🩸 v1 貨艙地板 z 9 ⇒ V 形船底內寬只有 0.5–0.8 m ⇒ 13（1.4–1.8 m 寬、到甲板樑下 1.5 m）；v1 後甲板只鋪到 x 103 ⇒ break 胸牆中段（y 73–87，75 格）浮在艙壁頂上一格、組裝件 2 個元件 ⇒ 鋪到 104（delta_apply 貼 29）。
- 封閉空氣 13 格（貨艙地板前端 4、主甲板船頭 9）填成樑色。
- 子作品（parent 船殼、tags sub、0.1 m、400×160×320、at 0,0,0）：`-deck-{hold,cabin,main,quarter}`、`-ladders-{main,quarter}`（關聯 `梯子`，meta kind=ladders；固定點 `<梯名>.foot／lo／hi／head`）。
- **甲板 meta**（§9.3，`design/decks_meta.tsv`）：每層 `export format=vxk links=none` ⇒ Blockside `src/decks.py` 量 ⇒ 照設計改：貨艙地板兩頭太窄取樣點湊不到 ⇒ 被截成 114–168，改照設計 112–188；主甲板舷弧照 layout 的 deck_z ＋ 1 寫折線（量到的 105:32,167:31,206:36 差 ≤ 1）。level：hold 0、cabin 1、main 2、quarter 3。
- 預覽 preset：`藏船殼`。
讀數：
- 設計那一側：零件重疊 0、跟船殼重疊 0、每件鏡像差 0、梯子點問題 0、砲門往艙裡被擋 0。
- **結果帳**（`tools/check_decks.py`，每件從匯出讀）：6 件 7,417 格，缺 0、多 0、色差 0；跟船殼重疊 0、彼此重疊 0。
- **組起來**（引擎 stats，組裝件）：43,250 格、1 元件、空腔 0、鏡像差 0。
- **梯子點**（組裝件 parts）：4 座、16／16 點、跟設計差 0；每點那一格空、腳下實心、頭頂 14 格空。
- **反向對照**：`draft_decks.py --probe=drop_ladder=quarter-S` ⇒ 3 座；後甲板、主甲板的 reach 少 quarter-S。
- 產生程式重跑：9 個輸出檔逐位元組相同。過程圖 `overlays/stage5_decks_nohull.png`。
- ⚠ 沒做：空艙房（船尾艙房 1.5 m 寬、要的話步驟 10 再標）；樓梯自檢在步驟 14 匯進遊戲之後跑。

## 步驟 6 裝飾（2026-10-27）
設計 plan.json `deco`；產生 `design/draft_deco.py`（**本船自己寫的**：拉貝爾號那支的 knee of head、Fontanges、假艉廊、百合花都不適用；船頭外緣、船尾面從 `裝飾:begin` 的船殼匯出量）⇒ `masks/deco/{figurehead,emblem_paint}.vox.txt`、`masks/glass/carve_behind.vox.txt`、`verify_deco.json`、`sheet05_deco_v1.png`；讀數 `design/tools/check_deco.py`。
- 船首像 `-figurehead`（外部模型 `船首像`，meta deco=1，88 格）：一條 0.9 m 的飛魚，尾巴貼著艏柱（z 36）、頭往前往上翹，胸鰭往後掠、兩邊各張 0.6 m；藍背 42、銀腹 218、翅膀 151、眼 36。在艏斜桅底下（撞艏斜桅 0）。🩸 v1 尾巴分叉尖 3 格插進艏柱 ⇒ 那幾格不放。
- 方艉金魚（船殼換色 38 格，標記 `裝飾`）：正中一條直立的金色飛魚（翅膀張開、左右對稱），z 36–45，只塗原本是赭紅的格。
- 船尾窗玻璃（Ship_Materials §9.5）：船殼色 87 的 24 格 `work sub=split … confirm=1` ⇒ `-stern-glass`「飛魚號 船尾窗玻璃」（雙生關聯 `船殼-窗玻璃`，meta material=glass；拆前拆後組起來逐格相同）；玻璃後面那層內板刻穿 24 格（顏色守門）⇒ 玻璃往船頭那一格在組裝件裡空 24／24（後面是船尾艙房）。
- 不做船尾燈：boom 在船尾舷頂上只有 0.9 m，燈會被掃到。
- 🩸 艏斜桅 v1 腳 heel_dz 5 ⇒ 在艏柱頭（x 211）桿底 z 42.4 比舷頂 43 低 ⇒ heel_dz 8（桿底 45.2）。
讀數：
- 設計：船首像撞船殼 0、撞艏斜桅 0、鏡像差 0；金魚鏡像差 0、跳過 0。
- **結果帳**（check_deco，作品從匯出讀）：船殼 35,785 ＝ `裝飾:begin` ＋ 金魚換色 − 刻 24 − 拆出去的玻璃 24，缺 0／多 0／色差 0；窗玻璃 24、船首像 88 同清單。
- 組起來（引擎 stats）：43,226 格、1 元件、空腔 0、鏡像差 0。
- **反向對照**：`--probe=emblem_dy=3`（金魚整條往右舷偏 3）⇒ 鏡像差 0 → 31。
- 產生程式重跑（`--mark=裝飾:begin`）：5 個輸出檔逐位元組相同。過程圖 `overlays/stage6_deco_{bowq,sternq}.png`。

## 步驟 7 桅與帆桁（2026-10-27）
設計 plan.json `masts`、`rig_build`；產生 `design/draft_masts.py`（出處拉貝爾號；多：艏斜桅腳的墊木、gaff／boom 元件整件等比縮放的擺法、boom 伸出船尾的讀數）⇒ `masks/masts/{mast-main,bowsprit}.vox.txt`、`yards_placement.json`、`verify_masts.json`、`sheet06_masts_v1.png`；落格 `design/tools/build_masts.py`（單桅）；讀數 `design/tools/check_stage6.py`。
- 主桅（子作品，關聯 `主桅`）：x 165 腳 z 8.5（立在 V 形船底的 keelson 上，腳下 14 格本來就是船殼）、後傾 14°、下桅頂 121、桅頂橫桁 112.5（trestletrees＋crosstrees 半長 6，緊貼桅頂）、上桅頂 168.5；半徑 1.8 → 1.4、上桅 1.1 → 0.7。
- 艏斜桅（子作品，關聯 `艏斜桅`）：腳 (198, z 42) 仰 20° 10 m、半徑 1.6 → 1.0；從艏柱頭上越過去 ⇒ 船殼開孔 0；腳下墊木（bitts）x 196–201、|dy| ≤ 2 從甲板接到桿底。
- 方帆桁（外部模型，放在主桅子作品裡；Ship_Setup §2.1）：下帆桁 6.0 m ← 憲法號 main-royal（y ×0.645）@ z 109、yard=crossjack；topsail 帆桁 4.5 m ← mizzen-royal（×0.692）@ z 141；brace −15／−17。兩根 sail 都標 main-topsail（下帆桁是 topsail 的帆腳桁、本身不掛帆）。
- gaff、boom（外部模型）：三叉戟號 mizzen gaff（15.0 m）／boom（13.5 m）**整件等比縮**到 5.1 m（×0.3423）／12.2 m（×0.8853），pivot 放在桅軸上（jaws 高 z 106／50）；仰角照元件本身（gaff 34.3°、boom 3.3°）⇒ gaff 峰 (99, 135)、boom 尾 (33, 58)、伸出船尾 3.7 m；meta yard=gaff／boom、sail=mainsail。
- 🩸 v1 下帆桁 z 112 跟 trestletrees 同高 ⇒ 109；boom jaws 1.6 m、仰 8° ⇒ 改用元件本身的 3.3° 之後掃過後甲板只剩 0.95 m ⇒ jaws 抬到主甲板上 2.0 m（後甲板上 1.3 m）。
讀數：
- 設計：每件鏡像差 0；帆桁撞格 0（4 根）。
- **結果帳**（check_stage6）：主桅 1,041、艏斜桅 659 缺 0／多 0／色差 0；船殼 ＝ `裝飾:end`（扣掉拆出去的玻璃 24）差 0；帆桁模型 4 根 meta 與來源固定點問題 0。
- **組起來**：44,926 格、1 元件、空腔 0、鏡像差 0。
- **反向對照**：`--probe=pivot=yard-main-crossjack:-75`（下帆桁降 7.5 m 到舷牆）⇒ 撞格 0 → 36，其他 0。
- 產生程式重跑：7 個輸出檔逐位元組相同。過程圖 `overlays/stage7_masts.png`。

## 步驟 8 索具、帆、旗（2026-10-27）
設計 plan.json `rigging`；產生 `design/draft_rigging.py`（出處拉貝爾號：channels、桅上的點、繩、穿實心的讀數照抄；改成單桅 sloop —— 斜桁主帆、topsail、staysail、jib、紅旗）⇒ `masks/rigging/channels.vox.txt`、`rigging_plan.json`、`textures/ensign.png`、`verify_rigging.json`；套用 `design/tools/rigging_apply.py`（照抄）。
- channels `-channels`（關聯 `支索板`，288 格，兩舷一件）：舷頂那兩格的舷外、寬 3；deadeye 每舷 shroud 3（x 155／151／147，桅在舷頂高度 x 157 往後 2 格起每 4 格）＋ backstay 1（x 131，桅後傾 ⇒ 另外往後；CH 的 4 個 deadeye）。避開兩門砲（x 118–122、176–180）。
- 靜索 22：shrouds 6、topmast backstays 2、topmast shrouds 4（桅頂橫桁兩端）、futtock 4、前支索（hounds → 艏斜桅 15%）、上桅支索（上桅頂 → 艏斜桅頂；兩條拉直 slack 1，艏帆的 luff 沿著它）、bobstay（艏斜桅 75% → 艏柱前緣 z 30）、艏斜桅 shrouds 2。
- ratlines：橫繩組 2（下桅兩舷，step 4、start 5、stop 12、min_span 4）⇒ 16 道。上桅只有兩根 shroud ⇒ 不做；沒有桅樓平台 ⇒ 先不標 climb。
- 帆 6：mainsail（四角綁 gaff throat／peak、boom end／jaws，綁 gaff、boom、桅三條邊，只有 leech 自由）、main-topsail（帆頂釘 topsail 帆桁 earing、帆腳 sheet 綁下帆桁 earing）、staysail（tack 艏斜桅 15%、head 前支索 72%）、jib（tack 艏斜桅頂、head 上桅支索 78%）、ensign（英國紅旗：紅底、左上角白底聖喬治十字，貼圖 `textures/ensign.png`，掛 gaff 峰、luff 沿 gaff 到 top-128）、pennant（桅頂白長旗）。預設風 4.5,−1.5,0、3 秒。
- 帆自己的繩 7（meta kind=sheet、sail）：main sheet（boom foot-96 → 船尾舷頂中線）、topsail sheet 2、staysail sheet 2、jib sheet 2。
- **帆裝三段**（Ship_Rigging §9.1；照 sail 的預設，沒寫 set）：

| 帆裝 | 張哪幾面 |
|---|---|
| 收帆（1） | jib、main-topsail |
| 戰鬥帆（2） | jib、main-topsail、mainsail |
| 滿帆（3） | jib、main-topsail、mainsail、staysail |

讀數：
- 設計：channels 鏡像差 0、跟船上的格重疊 0；固定點落在實心格 0（船殼的除外）；靜索穿過實心 0；帆自己的繩沒 meta 0；繩名重複 0。
- 引擎：繩 44（standing 22、running 6、橫繩 16 道）全部 ok、broken 0；帆 6 面、sails_broken 0、最鼓 14.7 格。
- **結果帳**：channels 作品 ＝ 清單（delta_apply --dry 差 0）。組起來 45,214 格、1 元件、空腔 0、鏡像差 0。
- **反向對照**：`--probe=nometa=jib.sheet-S` ⇒「帆自己的繩沒 meta」報那一條。
- 產生程式重跑：4 個輸出檔逐位元組相同。過程圖 `overlays/stage8_rig_{bowq,side}.png`。

## 步驟 9 砲（2026-10-27）
設計 plan.json `guns_build`；產生 `design/draft_guns.py`（出處拉貝爾號，邏輯照用）、`design/gunsim.py`（照抄）⇒ `guns_placement.json`、`verify_guns.json`；落格 `design/tools/build_guns.py`；檢查 `design/tools/check_stage8.py`（照抄）。
- 4 磅砲 4 門（R：1663 牙買加 barque 3 門、1684 聖多明哥 barque 4 門〔查〕）：跟拉貝爾號同一個元件同一個縮放 —— 風暴角號 6 磅長砲 `summit-stormkaap-01m-gun-6l` 縮 0.375（砲管 1.95 m）、meta kind=gun、gun=4l；掛在 `甲板-main`，名 `砲M-<S|P>01..02`；P 舷 mirror=y。夜隼號自己的 4 磅砲（0.05 m 原尺寸）砲軸離甲板 0.6 m ⇒ 砲門要開到舷頂 ⇒ 不用。
- 迴旋砲 6 門：皇家號叉架後膛迴旋砲 `apex-one-reale-01m-gun-pierrier` 縮 0.39、meta gun=pierrier、mount=turret、arc −80,80、rate 45；pivot 站在舷牆頂（那一欄最高那一層、牆厚中間）：後甲板 x 92（`甲板-quarter`）、船腰 x 138、船頭 x 199（`甲板-main`），名 `迴旋砲-<S|P>01..03`。
- 擺法：舷側砲從船殼外面沿砲身往裡退（0.5 格一步）到零碰撞；退 3 格、砲口伸出 4.69 格、砲軸 z 36–37。
讀數：
- 設計：10 門全部 ok（零碰撞、砲口伸出、砲口空、腳下有甲板 support 1.0）；砲跟砲不撞；兩舷對稱差 0。
- 作品（check_stage8，從 CLI 讀）：模型 10＝設計 10、CLI ok 10；參數差 0；外框（gunsim vs CLI）最大差 0.045 格；碰撞 0；砲口不在船殼外 0；meta 不合 0（4l 4、pierrier 6）。
- **反向對照**：`--probe=push=砲M-S01:4`（往外推 4 格）⇒ 那一門碰撞樣本 1,057，其他 0。
- 過程圖 `overlays/stage9_guns.png`（sails=0、ropes=0）。
- ⚠ 沒做：砲具與砲索（Ship_Guns §4.4，「要的話」；甲板窄、跟拉貝爾號一樣不做）。⚠ 後甲板的迴旋砲（砲軸 z 52.7）在 boom 底下（boom 在 x 92 高 53.6）—— boom 擺到那一舷時模型會疊在一起（只是畫面，遊戲不算模型碰撞）。

## 步驟 10 彈藥庫與甲板物件（2026-10-27）
設計 plan.json `gear_build`、`fit_build`；產生 `design/draft_gear.py`（出處拉貝爾號；小艇架可以沒有）、`design/draft_fit.py`（拉貝爾號步驟 16 那一套：艙房可以沒有、絞盤立柱定高（沒有船首樓）、主甲板 floor 讀 plan）⇒ `masks/gear/magazine.vox.txt`、`gear_placement.json`、`verify_gear.json`、`masks/fit/{hatch-main,hatch-fore,windlass}.vox.txt`、`fit_placement.json`、`verify_fit.json`；落格 `design/tools/build_gear.py`、`build_fit.py`；讀數 `design/tools/check_stage9.py`、`delta_apply.py --dry`。
- **彈藥庫** `-magazine`（關聯 `彈藥庫`，meta kind=magazine、pos=aft、powder_lb=600；1,270 格）：貨艙地板上、主艙口梯子後面 x 113–126、地板 z 14、頂 z 27；門朝船頭（x 126）、對著梯腳（x 130）。銅皮 168、松木地板 177、橡木框 136。固定點 blast (120,80,22)、door (126,80,15)。火藥桶 6 桶（憲法號 -powder-barrel 0.2、kind=powder、powder_lb 100）：底層 4、木架 2 —— 照砲數換算要 10 桶，V 形船底的貨艙後段只放得下 6（600 磅 ≈ 4 磅砲 450 發）。
- **艙蓋**（Ship_Fittings §9.7；主甲板離水線 0.5 m ⇒ 露天的艙口都要門）：主艙口 `-hatch-main`（15×11，嵌在圍板裡 z 31；開口層 z 30 的井 161 格、通到艙裡 143）、前艙口 `-hatch-fore`（9×11，蓋在圍板最高那一層上 z 36；開口 84、通到艙裡 63）⇒ 主甲板子作品的模型 kind=door、open_deg 100、固定點 hinge-a／b（沿 +x、左舷那一邊）。船尾艙房的井不做（舵柄掃在上面；後甲板離水線 1.5 m）。
- **廚房**：光榮號爐灶縮 0.18（0.8 m），主甲板露天、桅前面中線 x 164–172、z 32，meta kind=galley；四個面都站得住人（遊戲的量法：外框外 2 格的面中點、3 格內有走路格）。
- **絞盤** `-windlass`（關聯 `絞盤`，308 格）：船頭甲板上的橫式 windlass，前艙口與艏斜桅墊木之間 x 193–194；立柱 y 68–69／91–92（離舷牆內壁 3 格、高 0.7 m），絞筒 y 70–90（半徑 0.2 m、軸心離甲板 0.45 m），撬棍孔每 3 格。不標 kind。
- **羅經櫃**：夜隼號羅經櫃 0.2，後甲板 x 80、dy +6.5、z 41（舵柄右舷旁）。🩸 v1 dy +8.5 ⇒ 外框碰到舷牆內壁、被量到舷頂上 z 49 ⇒ 往內挪 2 格。
- **下桅繩梯**：橫繩組 main-lower-S／P 加 climb=1：foot 主甲板 (151, 96／64, 31)、head 踩在 crosstree 上 (141, 85／75, 114) ⇒ 只有第一人稱爬得上去。
- 不做：小艇（sloop 拖在船尾；遊戲 kind=boat 沒有功能）、空艙房（貨艙窄、桅與梯子佔中線；船尾艙房只有梯子那麼寬）、抽水機（遊戲自己生）。
讀數：
- **結果帳**：彈藥庫 1,270、絞盤 308、兩件艙蓋缺 0／多 0／色差 0；新格落在實心上 0、封閉空腔 0、浮空 0；鏡像差 0。
- 模型：本步 7＋3 件，CLI ok；參數差 0、撞實心 0、腳下 12 格內沒有實心 0；艙蓋、爐灶撞實心 0、撞模型 0；繩梯 foot／head 站得住。
- 彈藥庫：powder_lb 600 ＝ 6 桶 × 100；blast 空氣、door 空氣且腳下實心。
- 組起來：46,792 格、1 元件、空腔 0、鏡像差 0。
- **反向對照**：`check_stage9.py --drop=羅經櫃` ⇒ 缺 binnacle；`draft_fit.py --probe=galley_x=161`（爐灶塞到桅旁）⇒ 站得住的面 4 → 0。
- 產生程式重跑：清單與擺放 7 個檔逐位元組相同；verify_gear.json 只差讀到的組裝件格數（45,214 → 45,522：之後落的絞盤 308 格）。

## 步驟 11 舵、舵柄、錨（2026-10-27）
設計 plan.json `rudder_anchor_build`；產生 `design/draft_rudder_anchor.py`（出處拉貝爾號；舵柄的舵頭位置改成量方艉牆後面第一格空氣、錨的障礙改讀主甲板的迴旋砲）⇒ `masks/rudder/{rudder,tiller,anchor_gear}.vox.txt`、`rudder_anchor_placement.json`、`verify_rudder_anchor.json`；落格 `design/tools/build_rudder_anchor.py`；檢查 `design/tools/check_stage95.py`（照抄）。
- **舵** `-rudder`（組裝件模型 `舵`，367 格）：沿艉柱後緣（斜 22°）從龍骨底到 wing transom（z 24）；3 格厚、舵葉往下越寬（底 0.8 m → 頂 0.3 m，CH 線圖）；整支在水線下 ⇒ 白、每 6 格鐵箍；前緣兩側削 1 格。meta kind=rudder、hinge (90, 80.5, 0)、axis (−0.3746, 0, 0.9272)、max_deg 35、turn_axis=hinge、spin=rudder、spin_k 35、±35、lag 0.3；固定點 stock-top (78,80,24)。
- **舵柄** `-tiller`（`甲板-quarter` 的模型 `舵柄`，30 格）：舵頭從方艉內側冒出來（x 77、1×3、z 41–44），沿中線往前 0.9 m、z 43–44；kind=tiller、固定點 spin-a／spin-b（垂直軸）、spin=rudder、spin_k 35。⚠ 艙房梯子的梯頭（x 83）在舵柄掃得到的範圍裡（後甲板只有 3 m 長）。
- **錨**：共用錨元件（憲法號 bower）縮 0.22（錨幹 1.2 m）×2，meta kind=anchor、anchor=bower，掛在錨架 `-anchor-gear`（關聯 `錨架`，298 格，兩舷 billboard，托板 z 28–29 在水線上）；錨臂順著船殼切線（rz ±58）、往外推到零碰撞 ⇒ x 205、環 z 42、離船殼 5 格；避開船頭迴旋砲（x 199）。錨鏈孔固定點 hawse-S／P (206, 92／68, 37)（只登記、沒開孔）。
- 🩸 v1 錨縮 0.25、環 z 39 ⇒ 錨冠碰到水線、托板在水裡（z 23–24）⇒ 0.22、環抬到 z 42。
讀數：
- 設計：舵、舵柄、錨架落在實心上 0、鏡像差 0；舵柄的舵頭腳下都是甲板。
- **結果帳**：舵 367、舵柄 30、錨架 298 缺 0／多 0／色差 0。
- 舵：stock-top 8 格內有船格（曼哈頓 2）；跟組裝件重疊 0；轉 ±35° 掃進實心 0。錨 2 隻：撞實心 0、腳落在錨架上、來源有 ring；hawse 兩舷都在船殼格上。檢查問題 0。
- 讀回（`export format=parts`）：舵、舵柄的 meta 都有 spin。
- 組起來：47,090 格、1 元件、空腔 0、鏡像差 0。
- **反向對照**：`--probe=shift=錨-S:-6` ⇒ 錨-S 撞 765、錨-P 0。
- 產生程式重跑：4 個輸出檔逐位元組相同。

## 步驟 14 給遊戲的 meta 與匯入 Blockside（2026-10-27）
- 船殼關聯 meta kind=ship、waterline_z=25。`work sub=ropecheck`：繩 44、88 端全部 ok。新做的元件不用標 render（沒有新的桶、槳、舵輪；船首像、舵柄很小）。
- 在自己的 Blockside worktree（`D:/Unity/Blockside-wt/gura-971`，從 dev b58b238 開，`_cache` 從共用工作區抄進去）：`admin.py import --work gura-flyingfish-01m-assembly --id flyingfish --name 飛魚號` ⇒ `admin.py ids --id flyingfish`。⚠ import／reimport 會把 config/game.json 整份重排 ⇒ 照 HEAD 原樣、只插 ships[flyingfish] 那一筆（scratchpad 的 gamejson_fix.py），再 `admin.py build`。
- 匯入檢查第一輪 ✗ 2、後面幾輪抓到、在雕刻這邊修掉的：
  1. ✗ 取用點：主甲板、後甲板找不到 9×9 的空地（兩門砲往裡退到中線、主艙口、桅、爐灶；後甲板 3 m 長、有舵柄、羅經櫃、艙房的井）⇒ 彈藥庫 meta `hoist`（Ship_Magazine §8）。先寫 `ladders-1#hold,ladders-2#quarter-S` ⇒ 後甲板那一份把桶擺在右舷梯子的梯腳旁 ⇒ ✗ 梯腳出口堵死 ⇒ **後甲板不放砲**（迴旋砲每舷 3 → 2）、`hoist=ladders-1#hold`。
  2. ✗ 主甲板取用點量不到：遊戲照「那一層最靠船頭的那一門砲」定站人高度（Blockside 10_ship.js gunDecksMeta 的 main：照 x 由船頭往船尾排的第一門不是追擊砲的）⇒ 那時是船頭舷頂上的迴旋砲（z 42）⇒ 站人的高度量在 z 34–47，主甲板（z 31）不在裡面 ⇒ 船頭那對迴旋砲從 x 199 挪到第 2 門砲後面 x 172。⚠ 這是遊戲那側的一個規則：舷頂迴旋砲比舷側砲更靠船頭的船都會撞到（拉貝爾號剛好沒有）。
  3. ⚠ 樓梯自檢 ④ 貨艙梯子梯頂踩空 3 柱：井照拉貝爾號開 15 格（x 133–147）、本船只有 5 階 ⇒ `draft_decks.py` 梯子多一個 `well_len`（井開到最後一階為止 x 142）、head 挪到 x 144 ⇒ 主甲板 delta 刻 20（圍板）貼 99（甲板）、梯子刻 8、`hold.head` 固定點改 144；主艙口艙蓋跟著縮成 10×11（delta 刻 65 貼 10 換色 9、hinge-b 改 [9,0,0]）。
- 最後：**匯入檢查 ✗ 0、⚠ 8**；樓梯自檢 4 座 ✗ 0（⚠ 2）；甲板連通 4 層都接得到；操舵 舵令 ⇒ 舵柄 ⇒ 舵 100%；廚房 1 座（站得住的面 2）；門 2 扇（開口 110、84）；火藥 5／8 門走得到取用點。⚠ 逐條：
  - 送藥手 2／4、軍官 0／2（沒有舵輪的船，40_crew.js 照 HULL_X0 ＋ 160 找軍官站位 ⇒ 落在船頭外；遊戲那側的退路）。
  - 樓梯 ⚠：貨艙梯子梯頭前面是遊戲擺的木工台、梯腳後面是取用點的桶（遊戲那側擺的）；艙房梯子梯腳正前方是 break 艙壁（走得出去、要往旁邊繞）。
  - 火藥 ⚠ 3：桅前面兩門砲與一門迴旋砲跟取用點（貨艙梯子的梯頭）在走路格上不連通，送藥手照直線送。
- game.json ships[flyingfish]：geo spar [30, 41]、marines [32, 52]、center 45、aim 30、aimZ [5, 168]、deckAim [30, 41]、rigAim [50, 165]；cfg pump 2、agile 3、upwind 2.5（speed 照預設；1.1 試過 demo 只剩 5–12 節）；crew 照拉貝爾號（軍官 2、舵手 1、桅頂 0、陸戰隊 4、marineGap 14、handsK 0.25、航海士 0）；role merchant。
- 對拍（無頭、headless=1、#dump；對照組 `admin.py snapshot refs/heads/dev`）：`?demo=60&dump=1&seed=3` 089b6e562974、`&seed=2&ship=falcon,stormkaap` 79a38474d3c9、`&seed=3&ship=labelle,pinas` 0fa4cbfe3ce6 —— dev 兩次、新成品兩次逐位元組相同（換基底前後各一輪）。
- 戰局（一個種子，讀數不是結論）：`?demo=120&seed=3&ship=flyingfish,falcon` ⇒ 飛魚號開 68 發、命中 22、航速 8–16 節（夜隼號 12–25）、船員 34。遊戲裡帆裝三段照 meta 讀出來的跟上面那張表一樣（收帆 topsail＋jib、戰鬥帆＋mainsail、滿帆＋staysail）。
- 提交：Blockside 7668206（匯入；換基底到 dev 91b8e63、_cache 的 concepcion.vxk 補新的、重建），快轉進共用 dev、推上去（一起上去的有 kaguya 合好沒推的 15dc517、feae31f、91b8e63）；`_cache/flyingfish.vxk` 抄進共用工作區；worktree、分支收了。

## 步驟 15 交船（2026-10-27）
給遊戲那側填 geo 的高度（格的 z；0.1 m／格）：龍骨底 0（船尾；drag 3.5° ⇒ 船頭 z 7）、設計水線 25、貨艙地板 13、船尾艙房 21、主甲板 30（舷弧 船尾 32、船頭 35）、後甲板 40；舷頂 船腰 40／後甲板 48–49／船頭 42–43；砲門 z 33–37、4 磅砲軸 z 36–37、迴旋砲軸 z 44.7；桅頂橫桁 112.5、上桅頂 168.5（離水線 14.4 m）；gaff 峰 z 135、boom 尾 z 58（伸出船尾 3.7 m）；船殼 x 70（方艉頂）–212（艏柱），船首像到 x 219、艏斜桅頂 x 292。
遊戲那側的 vxk 指紋：`flyingfish.vxk` c:d9bd919dbe8334e865b80e67e81c84cb6957e845（Blockside 7668206 的 config/vxk_lock.json）。

Ship_Game §10 檢查表：
| 項目 | 本船 |
|---|---|
| ropecheck | ✓ 44 繩、88 端全 ok |
| 組裝件名 ＝ 船名、船殼「飛魚號 船殼」帶 sub | ✓ |
| meters_per_voxel、模型明寫 scale | ✓（每件子作品 0.1；模型 scale 都明寫） |
| sub=components 先查、能用的都引用 | ✓ 砲（6l→4l、pierrier）、方帆桁（憲法號 royal）、gaff／boom（三叉戟號）、羅經櫃、火藥桶、錨、爐灶；新做的只有本船的個性件（船首像）與舵、舵柄 |
| 槳帆船／撞角／從船殼伸出去的槳 | 不適用 |
| 爐灶：廚房或裝飾二選一 | ✓ 廚房 kind=galley（主甲板露天、桅前面；站得住的面 2） |
| 缺的砲種做成通用部件 | 不適用（4l、pierrier 都在砲種表） |
| 砲、帆桁、火藥桶是模型且帶 meta；甲板物件帶 kind | ✓ |
| 舵是模型、kind=rudder、stock-top；spin | ✓（匯入檢查沒有開場就掉的模型） |
| 操舵鏈：舵柄 kind=tiller | ✓「舵令 ⇒ 舵柄 ⇒ 舵 100%」 |
| kind=ship waterline_z；notes 寫高度 | ✓ |
| 梯子 kind=ladders、四點 | ✓ 4 座 16 點 |
| 樓梯自檢 ✗ 0、⚠ 看過 | ✓ ✗ 0、⚠ 2（見步驟 14） |
| ratlines 是橫繩組；繩梯 climb | ✓ 橫繩組 2、climb=1（head 踩在 crosstree 上 ⇒ 只有第一人稱爬） |
| 彈藥庫有火藥桶 | ✓ 6 桶；火藥 5／8 門走得到取用點（3 門 ⚠ 照直線送） |
| 甲板 kind=deck、每層有梯子 | ✓ 4 層 |
| 三角帆桁 | 不適用（gaff 是縱帆 gaff，不是 lateen） |
| 材質（鐵甲、金屬） | 不適用（全船木頭） |
| 窗的玻璃獨立關聯 material=glass | ✓ `船殼-窗玻璃` 24 格，後面刻穿 |
| 空艙房 | 不做（貨艙窄、桅與梯子佔中線；船尾艙房只有梯子那麼寬） |
| 砲退到零碰撞、砲口在船殼外 | ✓ 8 門 |
| 砲身砲座拆兩件、裝甲、砲塔、蒸汽 | 不適用 |
| 迴旋砲 | ✓ mount=turret ±80（照拉貝爾號） |
| 露天出入口有門 | ✓ 主艙口、前艙口 kind=door；艙房的井不做（舵柄掃在上面、離水線 1.5 m） |
| 舷側砲門蓋板 | 不做（露天甲板舷牆上的砲門，Ship_Steps 刪了步驟 12） |
| ropes／sails／models broken 0 | ✓ |
| 帆、旗、帆自己的繩 meta；帆桁 sail／mast | ✓ 帆 6、繩 7；帆桁 4 根 |
| 帆裝三段表、遊戲裡看過 | ✓ 表在步驟 8；遊戲裡照 meta 讀出來的一樣（⚠「全收」那一刻的畫面沒截圖） |
| 組裝件 1 元件、空腔 0、link_overlap 0、對稱 | ✓ |
| 產生程式重跑逐位元組相同 | ✓（每一步各自量過） |
| 匯出 vxk、對 checksum | ✓ 上面那一行 |
| 匯入檢查 ✗ 0、⚠ 都看過 | ✓ ⚠ 8 逐條列在步驟 14 |
| 舵、舵柄 spin | ✓ |

## 接進 Blocksail（2026-10-27）
- Blocksail worktree `D:/Unity/Blocksail-wt/gura-971`（分支 gura/971-sloop，從本地 main 08f39c0 開；submodule 從共用工作區 init，再 checkout Blockside 7668206）。
- world/fleet.js `FLEET.types.jsloop`：牙買加單桅船、35 噸、upkeep 1、cost 1,100〔佔位〕、hull flyingfish、`from: 1670`（牙買加最早的 "sloop" 字樣：1670-12 the Betty sloop）；跟 2026-10-26 拿掉的 `sloop`（retired ⇒ barque）是兩型，舊存檔不變。`hullLoa.flyingfish` 22.2 m（.vxk 外框 x 70–292）⇒ 停小船（≤ 36 m）那一級、停不進小艇（12 m）。
- docs/TRADE_SIM.md 船隊規模那張表加一列；tools/fleet_check.cjs 多三條（from 1670、造船挑型、全長與泊位級）。
- battle.html 照核心 bd901ed5624b0a11 重套；選船清單「飛魚號 51 噸・水線 12.4 m／砲 8 門・齊射 11 kg・34 人／航速 順風 10.6・側順風 14.7・逆風 6.3 節／建造者 gura」，`?ship=flyingfish,labelle` 開戰載得進來。
