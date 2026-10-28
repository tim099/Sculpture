# 燕子號（Swallow）—— 英國雙桅小帆船 ketch（0.1 m／格）—— 建造筆記

委託：TASK-0968（Tim 2026-10-28「繼續手上的task(沒有的話就看一下開著的task) GO」；母單 TASK-0964 的 8 種候選之一）：《Blocksail》1666 加勒比船型 —— 英國雙桅小帆船 ketch，HMS Swallow 1661（1665 派到牙買加）那型，沿岸與殖民地之間的商船、海軍補給。
流程：照 `Ship_Steps` 步驟表（貼在 TASK-0968 的驗收標準；刪了步驟 12 砲門蓋板 —— 露天甲板的砲從舷牆砲門打、沒有封閉砲甲板；刪了步驟 13 —— 全船木頭），每一步只讀那一行寫的文件。

## 座標約定（照飛魚號，產生程式也從它抄來）
- 空間 400×160×320；X 船長（船頭 +X）、Y 船寬（**中線 ＝ 第 80 格**，鏡像 y ↔ 160 − y）、Z 高度（z 0 ＝ 龍骨底面）；P ＝ y < 80。
- 「在不在船裡」：|y − 80| ≤ 半寬（格心判斷）⇒ 兩舷逐格對稱。
- 0.1 m／格（船殼、組裝件的書卡都記了 meters_per_voxel）。1 ft ＝ 0.3048 m ＝ 3.048 格。

## 作品
- 船殼 `gura-swallow-01m`「燕子號 船殼」：任務作品（委託 TASK-0968、10 token 已發），`tags=sub`。
- 組裝件 `gura-swallow-01m-assembly`「燕子號」：主作品（沒標 sub），parent 船殼，關聯 `船殼` at 0,0,0。
- 子作品照飛魚號的拆法（甲板每層一件、梯子、桅、帆桁、裝飾、彈藥庫、舵、錨架…），parent 船殼、`tags=sub`、0.1 m。

## 產生程式
- `design/` 整套從飛魚號 `gura-flyingfish-01m/design/` 抄來（它又出自拉貝爾號、收穫號）：40 個 .py 的作品 id、船名、單號已換（每個檔第一行寫了這一手的出處；原本寫出處的那幾行照舊）；換完 grep 舊 id 0。
- 飛魚號的 `plan.json` 留成 `plan_flyingfish_ref.json`；本船的 `plan.json` 在步驟 3 照 ketch 重寫。

## 沿用的現有元件（`work sub=components`，2026-10-28 查）
- 砲：夜隼號 4 磅長砲 `summit-night-falcon-01m-gun-4l`（gun 4l；飛魚號也用它）。
- 錨 `basecamp-frigate-constitution-01m-anchor`、火藥桶 `basecamp-frigate-constitution-01m-powder-barrel`、小艇 `basecamp-ember-01m-boat`（縮）、羅經櫃 `summit-night-falcon-01m-binnacle`、爐灶 `kaguya-gloire-01m-galley`（縮）、船尾燈 `gura-tridente-01m-lantern`、艙壁門 `gura-pinas-01m-door`。
- 帆桁：方帆桁照飛魚號的做法縮憲法號的 royal；後桅如果是斜桁（gaff）就縮三叉戟號的 `gura-tridente-01m-yard-mizzen-gaff`，是三角帆就照拉貝爾號的 lateen（步驟 3 查完再定）。
- 自己做：船首、船尾裝飾、船名板（每艘船的個性裝飾 —— Ship_Setup §2.1）。

## 步驟 3 資料與新圖紙（2026-10-28）
查證：研究代理一輪 ⇒ `references/research_ketch_2026-10-28.md`＋19 張圖（Van de Velde 11 張、NG874 油畫、Baker 2 張、Anderson 1927 原書 6 頁）；gura 看過 PAE5267（右舷正側 1675）與 Baker fig.7（Adventure 復原）。
單上四條說法：
- ① Swallow：龍骨 40／寬 16／艙深 8／40 人／1665 去牙買加 ✓（二手：threedecks 轉錄 Winfield，原書 p.677 沒看到）；56 t 是 Colledge 的（Winfield 54 44/94）；「6 × 4-pounder」砲種沒驗到（只有名目 6 門）；新查到艉吃水 8 ft。
- ② Colchester：數字 ✓、維基出處標錯（是 Lavery 不是 Winfield；「艙深 7′6″」其實是艉吃水，「793 tons」應為 72 32/94）。
- ③ 兩桅 ✓（Bailey 1731、V 每一張）；商用 0–4 門、6–12 人沒驗到。
- ④ 沒有當時的線圖 ✓（最早的是 1729 的臼砲船）。
帆裝：**1660 年代的後桅是三角帆（lateen）**（V 1665–1685 每一張；後桅 gaff 是 18 世紀）；主桅 course＋topsail；艏帆 staysail＋jib。

設計 `design/plan.json`（每個數字的 `src`：W Winfield／A Anderson／V 量素描／B Baker／R 研究／設計決定）；程式改了：
- `draft_lines.py`：對照從 Chapman 換成 `plan.target`（W 的龍骨、寬、艉吃水、艙深 ＋ 1678 噸位公式）。
- `layout.py`：後桅也立在 keelson（主甲板在 break 就斷了，拉貝爾號「後桅立在主甲板」會懸在艙房半空 z 32）。
- `draft_layout.py`：圖的標題與出處。

| 項目 | 讀數 | 目標 |
|---|---|---|
| 直龍骨 | 122.0 格 | W 40 ft ⇒ 121.9 |
| 寬 | 49 格 | W 16 ft ⇒ 49 |
| 甲板長（z 31） | 155.1 格（15.5 m） | R 推 51 ft ⇒ 155 |
| 吃水 船尾／船頭 | 24.0／20.3 | W 8 ft ⇒ 24.4／R 推 20 |
| 艙深（船中龍骨頂到甲板樑下） | 24.1 | W 8 ft ⇒ 24.4 |
| 噸位（龍骨 × 寬 × ½寬 ÷ 94） | 55.0 t | W 54 44/94 |
| 排水量（水線下 × 1.025） | 85 t | — |
| 船殼牆 | 47,887 格；1 元件、空腔 0、鏡像差 0 | — |

- 甲板（甲板面 z）：貨艙地板 8（x 128–240）、主甲板 31（舷弧 船尾 +2、船頭 +6，x 141 起）、船尾艙房 25（x ≤ 139）、後甲板 44（x ≤ 140）；break 在 x 140。
- 砲門：每舷 3 個（x 152.5、206.5、226.5）、5×5、門檻 3；4 磅砲 6 門；後甲板不放砲。
- 桅：主桅 x 185（甲板處 184 ＝ 0.47 L）後傾 2°、腳 z 7、平台 141、頂 223（離水線 19.9 m）；course 13.1 m @129、topsail 7.2 m @209。後桅 x 133（0.80 L）後傾 4°、腳 z 7、頂 117（後甲板以上 7.3 m）；lateen 7.9 m @100。艏斜桅 腳 (238, 40)、仰 26°、9.5 m、尖 (323, 82)。
- 🩸 v1 艏柱傾出 23 ⇒ 甲板長 153.3 ⇒ 25；v2 船頭舷頂在 x 262 才升到 46 ⇒ 艏柱頂那一排 13 格只跟船身斜角相接、2 個元件 ⇒ x 258 起平的；v1 後桅立在主甲板 ⇒ 腳懸空 ⇒ keelson、下桅 9.7 → 11.0。

讀數與反向對照：
- `draft_lines.py --probe=half_beam=3` ⇒ 全寬 49 → 55；站 x 120／160／200／240 的水線半寬 9／22／24／19 → 11／25／27／20。
- `draft_layout.py --probe=port=main:1:+3` ⇒ x0 [150, 204, 224] → [153, 204, 224]、間距 49 → 46。
- 產生程式重跑：5 個輸出檔（清單、兩張圖、兩份 verify）逐位元組相同。

## 步驟 4 船殼落格、砲門、塗裝、船尾窗（2026-10-28）
- 船殼：標記 `船殼`（begin＝start）→ `design/tools/stamp_lists.py gura-swallow-01m 0 masks/hull/hull_01.vox.txt`（1 刀，placed 47,887 ＝ 清單）→ `船殼`（end）。⚠ 標記名不能含 `:`，begin／end 用 `phase=`。
- 砲門與塗裝：`design/draft_ports.py`（出處飛魚號，沒改邏輯）⇒ `masks/ports/carve.vox.txt`（474，顏色守門 carvevox）、`paint.vox.txt`（1,865，stampvox overwrite=1）、`verify_ports.json`、`sheet03_ports_paint_v1.png`；標記 `砲門塗裝` begin／end 夾住。
  - 塗裝（plan.paint、hull_build）：水線上深褐 104（NG874 c.1660 油畫：船殼是油／焦油處理的深褐原木）、水線下灰白 182；一道黑 wale（主甲板 −2..−1，照舷弧）；外舷不漆 frieze；舷頂最上一格黑；砲門框紅 160；wing transom 以上的窄平艉板紅 160、上下兩列金 248；船長艙兩扇窗玻璃 87（z 32–35）。
- 讀數（作品從 export 讀）：
  - **結果帳**（`tools/check_stage3.py . mark=砲門塗裝:end`）：作品 47,413 ＝ 船殼 − 刻 ＋ 換色，缺 0、多 0、色差 0。
  - 6 個砲門開口裡還有實心的 0 個；**正向對照** 同一把尺量 `船殼:end` ⇒ 6 個全報（各 75 格）；**反向對照** `draft_ports.py --probe=skip_port=main:2` ⇒ 只報第 2 門兩舷（各 75）。
  - 船殼線形對照（`tools/check_hull.py`，`船殼:end`）：結果帳 47,887 缺 0／多 0／色差 0；210 點差 0；`probe_x=164`（設計那一站 +3）⇒ 報 13 點、最大 3。
  - 引擎 `stats structure=1 mirror=y:80`：1 元件、空腔 0、鏡像差 0。
- 過程圖 `overlays/stage4_hull_{bowq,sternq,side}.png`。⚠ 艙裡是空的（甲板在步驟 5）。

## 步驟 5 甲板、梯子（2026-10-28）
設計 plan.json `decks_build`；產生 `design/draft_decks.py`（出處飛魚號，沒改邏輯）⇒ `masks/decks/<層>.vox.txt`、`masks/ladders/<上面那層>.vox.txt`、`ladder_points.json`、`verify_decks.json`、`sheet04_decks_v1.png`；落格 `design/tools/build_decks.py`。
- 甲板（甲板面 z）：貨艙地板 10（x 128–240）、船尾艙房 25（x ≤ 139）、主甲板 31（舷弧，x 141 起）、後甲板 44（x ≤ 140，蓋住 break 艙壁頂）。
- 開口：主艙口 ＝ 貨艙梯子的井（x 154–171）、前艙口 200–207（半寬 4）、桅孔 主 r 2.5／後 r 2.0。
- break：x 140 一道艙壁（艙房地板到後甲板，不開門 —— 主甲板 32 比艙房地板高 0.7 m）＋後甲板邊 5 格胸牆、兩座梯子頭留口。
- 梯子 4 座（每 3 格一階、每階 2 格、踏板 7 寬）：貨艙→主甲板（井，x 154 往船頭、頭 x 174）、主甲板→後甲板兩舷（dy ±8，x 149 往船尾、頭 x 136）、艙房→後甲板（井，x 124 往船尾、頭 x 106；後桅 x 133 在它前面）。
- 🩸 v1 貨艙地板 z 8 ⇒ 貼著平船底內面、只剩中間一條 645 格 ⇒ z 10（2,391 格）；v1 後甲板梯子 xs 150 ⇒ 梯腳落在第 1 門砲的砲道（x 150–154）、兩舷各擋 1 格；v2 148 ⇒ 最後一階壓在後甲板邊的實心上 ⇒ 149。
- 子作品（parent 船殼、tags sub、0.1 m、400×160×320、at 0,0,0）：`-deck-{hold,cabin,main,quarter}`、`-ladders-{main,quarter}`（關聯 `梯子`，meta kind=ladders；固定點 `<梯名>.foot／lo／hi／head`）。
- **甲板 meta**（§9.3，`design/decks_meta.tsv`）：每層 `export format=vxk links=none` ⇒ Blockside `src/decks.py` 量（第二把尺）：貨艙 11、艙房 26、主甲板 141:32,205:32,256:37、後甲板 45 ＝ 設計（甲板面 ＋1）；兩頭太窄取樣點湊不到 ⇒ 範圍照設計（貨艙 128–240、艙房 104–139、後甲板 98–140）。level：hold 0、cabin 1、main 2、quarter 3。
- 預覽 preset：`藏船殼`。過程圖 `overlays/stage5_decks.png`。
讀數：
- 設計那一側：零件重疊 0、跟船殼重疊 0、每件鏡像差 0、梯子點問題 0、砲門往艙裡被擋 0。
- **結果帳**（`tools/check_decks.py`，每件從匯出讀）：6 件 10,963 格，缺 0、多 0、色差 0；跟船殼重疊 0、彼此重疊 0；梯子點 16／16、跟設計差 0。
- 組裝件 `stats structure=1 mirror=y:80`：1 元件（58,376）、空腔 0、鏡像差 0。
- **反向對照**：`draft_decks.py --probe=drop_ladder=quarter-S` ⇒ 3 座；後甲板、主甲板的 reach 少 quarter-S。

## 步驟 6 裝飾（2026-10-28）
設計 plan.json `deco`；產生 `design/draft_deco.py`（出處飛魚號；`fish()` 換成 `swallow()`）⇒ `masks/deco/{figurehead,emblem_paint}.vox.txt`、`masks/glass/carve_behind.vox.txt`、`verify_deco.json`、`sheet05_deco_v1.png`；讀數 `design/tools/check_deco.py`。
- 船首像 `-figurehead`（外部模型 `船首像`，meta deco=1，88 格）：一隻 0.8 m 的燕子（＋燕尾 0.4 m），尾巴貼著艏柱（z 38）、頭往前；翅膀往後掠、兩邊各張 0.7 m；藏青 37 的背、白腹 218、紅褐的喉 164、眼與嘴 36。在艏斜桅底下（撞艏斜桅 0）；燕尾插進艏柱的 6 格不放。
- 艉板金燕（船殼換色 39 格，標記 `裝飾`）：窄平艉板正中一隻金色燕子剪影（燕尾在下、翅膀張開、左右對稱），z 38–47（兩扇窗 z 32–35 的上面），只塗原本是紅 160 的格。
- 船尾窗玻璃（Ship_Materials §9.5）：船殼色 87 的 24 格 `work sub=split … confirm=1` ⇒ `-stern-glass`「燕子號 船尾窗玻璃」（雙生關聯 `船殼-窗玻璃`，meta material=glass；拆前拆後外觀不變）；玻璃後面那層內板刻穿 24 格（顏色守門）⇒ 玻璃往船頭那一格在組裝件裡空 24／24（後面是船長艙）。
- 船尾燈：步驟 10 照後桅三角帆桁會不會掃到再定。
讀數：
- 設計：船首像撞船殼 0、撞艏斜桅 0、鏡像差 0；金燕鏡像差 0、跳過 0。
- **結果帳**（check_deco，作品從匯出讀）：船殼 47,365 ＝ `裝飾:begin` ＋ 金燕換色 − 刻 24 − 拆出去的玻璃 24，缺 0／多 0／色差 0；窗玻璃 24、船首像 88 同清單。
- 組起來（引擎 stats）：58,352 格、1 元件、空腔 0、鏡像差 0。
- **反向對照**：`--probe=emblem_dy=3`（金燕整隻往右舷偏 3）⇒ 鏡像差 0 → 30。
- 產生程式重跑（`--mark=裝飾:begin`）：5 個輸出檔逐位元組相同。過程圖 `overlays/stage6_deco_{bowq,sternq}.png`。

## 步驟 7 桅與帆桁（2026-10-28）
設計 plan.json `masts`、`rig_build`；產生 `design/draft_masts.py`（出處飛魚號，沒改邏輯；lateen 的寫法是拉貝爾號那套）⇒ `masks/masts/{mast-main,mast-mizzen,bowsprit}.vox.txt`、`masks/yards/lateen-mizzen.vox.txt`、`yards_placement.json`、`yards_lateen.json`、`verify_masts.json`、`sheet06_masts_v1.png`；落格 `design/tools/build_masts.py`；讀數 `design/tools/check_stage6.py`（兩支都加了後桅）。
- 主桅 `-mast-main`（1,886 格）：x 185、後傾 2°、腳 z 7（keelson）、下桅頂（平台）141、上桅頂 223；直徑 0.44 → 0.32 m、上桅 0.26 → 0.16 m；桅頂 trestletrees＋crosstrees（半長 6，沒有桅樓平台 ⇒ 派不出桅頂水手）。
- 後桅 `-mast-mizzen`（490 格）：x 133、後傾 4°、腳 z 7、頂 117（後甲板上 7.3 m）；直徑 0.26 → 0.2 m。桅腳在 z 8 那 2 格碰到船尾 deadwood 上的內板 ⇒ 讓給船殼（腳坐在船底上）。
- 艏斜桅 `-bowsprit`（741 格）：腳 (238, 40)、仰 26°、9.5 m、尖 (323, 82)；從艏柱頭上越過去（艏斜桅孔 0 格）；腳下墊木 x 236–241。
- 帆桁（外部模型，放在各自的桅子作品裡）：
  - `yard-main-course` 13.1 m ← 憲法號 main-royal 只沿長度 ×1.41，z 129、brace −15；`yard-main-topsail` 7.2 m ← mizzen-royal ×1.11，z 209、brace −17。
  - `yard-mizzen-lateen` 7.9 m（本船自己的子作品 `-yard-mizzen-lateen`，527 格、固定點 13）：前低後高 40°、掛點在前端往後 40%；前端 (149.5, z 80)、後端 (90.5, z 130)，伸出船尾 0.43 m；meta yard=gaff、rig=lateen。
- 🩸 v1 build_masts 照飛魚號只建主桅 ⇒ 後桅沒建、lateen 模型的 host 不存在，sub=model 的 exit 2 被 ok=(0, 2) 吞掉、還印「帆桁模型 3 根」⇒ MASTS 加後桅；每根桅子作品的模型清單讀回：主桅 2、後桅 1。
讀數：
- **結果帳**（check_stage6）：主桅 1,886、後桅 490、艏斜桅 741 缺 0／多 0／色差 0；船殼 ＝ `裝飾:end` 差 0；帆桁模型 3 根 meta 與來源固定點問題 0；帆桁撞格 0。
- 組起來（引擎 stats）：61,469 格、1 元件、空腔 0、鏡像差 0。
- **反向對照**：`--probe=pivot=yard-main-course:-95`（course 降 9.5 m 到舷牆的高度）⇒ 撞格 0 → 60，其他 0（−75 只降到 z 54、還在舷牆上面 ⇒ 0，尺沒問題、是探得太淺）。
- 產生程式重跑：8 個輸出檔逐位元組相同。過程圖 `overlays/stage7_masts.png`。

## 步驟 8 索具、帆、旗（2026-10-28）
設計 plan.json `rigging`；產生 `design/draft_rigging.py` —— **換成拉貝爾號那支**（`ame-labelle-01m/design/draft_rigging.py`：方帆主桅＋lateen 後桅；飛魚號那支是單桅 sloop 專用的，原檔留在 gura 的 scratchpad 沒進作品）；改成 ketch：只有主桅＋後桅、沒有 spritsail、沒有船首喙；主支索／上桅支索落在艏斜桅、staysail＋jib、bobstay 腳在艏柱前緣、英國紅旗（這幾段照飛魚號）⇒ `masks/rigging/channels.vox.txt`、`rigging_plan.json`、`textures/ensign.png`、`verify_rigging.json`；落格 `design/tools/rigging_apply.py`（沒改）。
- channels（`-channels`，546 格，兩舷一件）：主桅 deadeye x 183／178／173／168＋backstay 163，後桅 x 131／126；在舷頂那兩格的舷外（砲門頂上面）。
- 靜索：shrouds 主桅每舷 4、後桅 2；上桅 shrouds＋futtock 每舷 2（桅頂橫桁兩端）；上桅 backstay 每舷 1；main-stay（主桅 → 艏斜桅根往前 15%）、main-topmast-stay（→ 艏斜桅頂）、mizzen-stay（後桅 → 主桅腳）；bobstay 1（艏柱前緣 z 28）、艏斜桅 shroud 兩舷（船頭舷頂 x 250）。
- ratlines：橫繩組 4（主桅、後桅 × 兩舷；每 4 格一道，38 道）；沒有桅樓平台 ⇒ 不標 climb。
- 帆 5 面：main-course（帆腳在舷頂上 3 格、sheet x 155、tack x 215）、main-topsail（sheet 綁 course 帆桁 earing）、mizzen-lateen（sail=gaff、rig=lateen；clew x 100 z 60、sheet 綁船尾舷頂、tack 綁主甲板 x 152）、staysail（tack 艏斜桅 15%、head 主支索 72%）、jib（tack 艏斜桅頂、head 上桅支索 78%）。旗 2 面：英國紅旗（lateen 帆桁後端）、白長旗（主桅頂）。
- **帆裝三段**（Ship_Rigging §9.1；照 sail 的預設，沒寫 set）：

| 帆裝 | 張哪幾面 |
|---|---|
| 收帆（1） | main-topsail、jib |
| 戰鬥帆（2） | main-topsail、jib、mizzen-lateen |
| 滿帆（3） | main-topsail、jib、mizzen-lateen、main-course、staysail |

讀數：
- 設計：channels 鏡像差 0、跟船上的格重疊 0；固定點落在實心格 0；靜索穿過實心 0；帆自己的繩沒 meta 0；繩名重複 0。
- 引擎：繩 41（standing 28、running 13）＋橫繩 38 道全部 ok、broken 0；帆 7 面（含旗）、sails_broken 0。
- **結果帳**：channels 作品 ＝ 清單（delta_apply --dry 差 0）。組起來 62,015 格、1 元件、空腔 0、鏡像差 0。
- **反向對照**：`--probe=nometa=jib.sheet-S` ⇒「帆自己的繩沒 meta」報那一條。
- 產生程式重跑：4 個輸出檔逐位元組相同。過程圖 `overlays/stage8_rig_{bowq,side}.png`。

## 步驟 9 砲（2026-10-28）
設計 plan.json `guns_build`；產生 `design/draft_guns.py`（出處飛魚號，邏輯照用）、`design/gunsim.py`（照抄）⇒ `guns_placement.json`、`verify_guns.json`；落格 `design/tools/build_guns.py`；檢查 `design/tools/check_stage8.py`（照抄）。
- 4 磅砲 6 門（W：名目 6 門；砲種「4-pounder」沒驗到 ⇒ minion 級 ≈ 4 磅）：跟飛魚號、拉貝爾號同一個元件同一個縮放 —— 風暴角號 6 磅長砲 `summit-stormkaap-01m-gun-6l` 縮 0.375（砲管 1.95 m）、meta kind=gun、gun=4l；掛在 `甲板-main`，名 `砲M-<S|P>01..03`；P 舷 mirror=y。
- 不放迴旋砲：W 只有名目 6 門、迴旋砲沒有史料；也避開飛魚號 v2 的坑（舷頂迴旋砲比舷側砲靠船頭 ⇒ 遊戲照它定主甲板的站人高度）。
- 擺法：從船殼外面沿砲身往裡退（0.5 格一步）到零碰撞；退 2.5–4 格、砲口伸出 3.7–5.2 格、砲軸 z 37–39；腳下甲板 support 最低 0.5（＝ 門檻）。
讀數：
- 設計：6 門全部 ok（零碰撞、砲口伸出、砲口空、腳下有甲板）；砲跟砲不撞；兩舷對稱差 0。
- 作品（check_stage8，從 CLI 讀）：模型 6＝設計 6、CLI ok 6；參數差 0；外框（gunsim vs CLI）最大差 0.025 格；碰撞 0；砲口不在船殼外 0；meta 不合 0（4l 6）。
- **反向對照**：`--probe=push=砲M-S01:4`（往外推 4 格）⇒ 那一門碰撞樣本 913，其他 0。
- 過程圖 `overlays/stage9_guns.png`（sails=0、ropes=0）。
- ⚠ 沒做：砲具與砲索（Ship_Guns §4.4，「要的話」；同飛魚號、拉貝爾號不做）。

## 步驟 10 彈藥庫與甲板物件（2026-10-28）
設計 plan.json `gear_build`、`fit_build`；產生 `design/draft_gear.py`、`design/draft_fit.py`（出處飛魚號，沒改邏輯）⇒ `masks/gear/magazine.vox.txt`、`masks/fit/{hatch-main,hatch-fore,windlass}.vox.txt`、`gear_placement.json`、`fit_placement.json`、`verify_gear.json`、`verify_fit.json`；落格 `design/tools/build_gear.py`、`build_fit.py`；檢查 `design/tools/check_stage9.py`。
- 彈藥庫 `-magazine`（1,436 格，關聯 `彈藥庫`）：貨艙後段 x 132–148、地板 z 11、頂 z 28；銅皮 168、松木地板 177、橡木框 136；門開在船頭那面（x 148），正對貨艙梯腳（x 153）。火藥桶 6（底層 4、木架 2；600 磅）—— 照砲數換算想放 16 桶，貨艙後段只放得下 6（⚠ 換算，不是史料）。固定點 blast (141, 80, 20)、door (148, 80, 12)。hoist 先不寫：步驟 14 照匯入檢查的取用點再定。
- 羅經櫃（夜隼號的，scale 0.2，kind=binnacle）：後甲板 (128, 86.5, 45)，船長艙井前面、後桅腳旁。🩸 v1 右舷 dy 9 ⇒ 碰到舷牆內壁、被量到舷頂上 z 53；v2 中線 ⇒ 後桅往後傾 4°、在後甲板高度桅軸落在 x 129–131 ⇒ 撞桅 ⇒ dy 6。
- 小艇不做（拖在船尾；遊戲的 kind=boat 沒有功能）。
- 艙蓋（kind=door，掛在 `甲板-main`）：主艙口 `-hatch-main`（206 格，嵌在圍板裡、17 × 11、底 z 32）、前艙口 `-hatch-fore`（129 格，蓋在圍板上 z 35）；鉸鏈沿 +x 在左舷那邊（往上掀）。
- 爐灶（光榮號的縮 0.18，kind=galley）：主甲板中線 x 190–197（主桅與前艙口之間）；四面都量得到走路格。
- 絞盤 `-windlass`（380 格，關聯 `絞盤`）：船頭甲板 x 232–233（第 3 門砲與艏斜桅腳墊木之間）；兩根立柱高到舷牆頂（z 41）、中間一根橫的絞筒。
- 下桅繩梯（climb=1）：main-lower-S／P，foot 主甲板 (175, 99／61, 32)、head 桅頂靠船尾那根 crosstree 上 (178, 85／75, 143)；只有第一人稱爬得上去。
讀數：
- 設計：新格落在實心上 0、封閉空腔 0、浮空 0；模型碰撞 0、腳下 12 格內有實心；艙蓋、爐灶、絞盤撞實心 0、撞模型 0；繩梯兩頭都站得住；鏡像差 0。
- **結果帳**（check_stage9）：彈藥庫 1,436 缺 0／多 0／色差 0；模型 7＝設計 7、CLI ok 7；火藥 6 × 100 ＝ 600 磅；blast、door 是空氣、door 腳下實心；參數差 0、撞實心 0。
- 組起來（引擎 stats）：63,831 格、1 元件、空腔 0、鏡像差 0。
- **反向對照**：`check_stage9.py --drop=羅經櫃` ⇒ 缺 binnacle；`draft_fit.py --probe=galley_x=184`（爐灶塞到桅上）⇒ 站得住的面 4 → 0。
- 產生程式重跑：清單與擺放 6 個檔逐位元組相同。

## 步驟 11 舵、舵柄、錨（2026-10-28）
設計 plan.json `rudder_anchor_build`；產生 `design/draft_rudder_anchor.py`（出處飛魚號，沒改邏輯）⇒ `masks/rudder/{rudder,tiller,anchor_gear}.vox.txt`、`rudder_anchor_placement.json`、`verify_rudder_anchor.json`；落格 `design/tools/build_rudder_anchor.py`；檢查 `design/tools/check_stage95.py`。
- 舵 `-rudder`（608 格，模型 `舵`，kind=rudder＋spin）：沿斜 18° 的艉柱後面，從龍骨底到 wing transom（z 31）；舵葉底 1.0 m、水線 0.5 m、3 格厚；水線下白、每 6 格一道鐵箍；鉸鏈 (112, 80.5, 0)、軸沿艉柱、max_deg 35；stock-top (99, 80, 31)。轉 ±35° 掃進組裝件實心 0。
- 舵柄 `-tiller`（42 格，模型 `舵柄` 掛在 `甲板-quarter`，kind=tiller＋spin）：舵頭從窄平艉板內側（x 100）冒出來、沿中線往前到 x 115、高 z 47–48（從船長艙井的圍板 z 46 上面越過去）。⚠ 舵頭在 wing transom（z 31）與後甲板之間那一段沒畫（藏在船尾牆裡，同飛魚號）。🩸 v1 z_deck 給甲板面 44 本身 ⇒ 往前找第一格空氣找到井口 x 108 ⇒ 舵頭懸在井上 3 格、舵柄尾撞圍板 ⇒ 45／48。
- 錨（共用元件縮 0.28，錨幹 1.5 m，anchor=bower）：兩舷吊在船頭舷外 x 240、環 z 44，錨臂順著船殼切線往外推 5.5 格到零碰撞；錨冠底下一塊 billboard 托板（`-anchor-gear`，264 格，關聯 `錨架`）。錨鏈孔只登記固定點 hawse-S／P (246, 98／62, 39)，⚠ 沒有開孔。
讀數：
- 設計：舵、舵柄、錨架落在實心上 0；錨碰撞 0、腳落在錨架上；鏡像差 0。
- **結果帳**（check_stage95）：舵 608、錨架 264 缺 0／多 0／色差 0（舵柄另外對：作品 42 ＝ 清單 42）；舵模型 ok、跟組裝件重疊 0；錨 2 ok、來源有 ring；hawse 兩點在那一舷的船殼格上；問題 0。
- 組起來（引擎 stats）：64,095 格、1 元件、空腔 0、鏡像差 0。
- **反向對照**：`--probe=shift=錨-S:-6`（右舷錨往船殼推 6 格）⇒ 錨-S 撞 717、錨-P 0。
- 產生程式重跑：4 個輸出檔逐位元組相同。過程圖 `overlays/stage11_helm_anchor.png`。
