# 澤漢號（Zeehaen 型福祿特 fluyt／flyboat）—— 荷蘭東航散貨船，1660 年代（0.1 m／格）—— 建造筆記

委託：Tim 2026-10-27「/scp-task 966 GO」—— TASK-0966《Blocksail》1666 加勒比船型：福祿特 fluyt（荷）／英稱 flyboat（傘 TASK-0964，erina 開單）。
範圍（遊戲用）：外部完整；內部只做甲板、艙口、梯子、彈藥庫、艙房這些遊戲用得到的大致構造。步驟照 `Ship_Steps`（單上的驗收標準）。
產生程式出處：`ame-labelle-01m/design`（拉貝爾號；它又出自 `calli-cosecha-01m/design`）—— 同是露天甲板舷牆砲門、後桅 lateen 的小船；作品 id、persona、單號已全部換掉（grep 舊 id 0）。

## 座標約定（步驟 2）
- X 船長（船頭 +X）、Y 船寬、Z 高度（z 0 ＝ 龍骨底面）；中線與空間大小照步驟 3 的主尺寸定（寫在 plan.json `space`），鏡像 y ↔ 2·yc − y；P ＝ y < yc。
- 「在不在船裡」：|y − yc| ≤ 半寬（格心判斷）⇒ 兩舷逐格對稱（照拉貝爾號）。
- 0.1 m／格（船殼與組裝件的書卡都記了 meters_per_voxel；子作品建立時一律補）。模型一律明寫 scale。

## 作品（步驟 2）
- 船殼 `abigail-fluyt-01m`「澤漢號 船殼」：任務作品（commission TASK-0966，已發 10 token），tags sub。
- 組裝件 `abigail-fluyt-01m-assembly`「澤漢號」：主作品，關聯 `船殼` at 0,0,0。
- 船名：步驟 3 改成「澤漢號」（借 Zeehaen 1639，Tasman 的福祿特）—— ⚠ 尺寸照 Witsen 的 110 呎東航規則，不是 Zeehaen 本身的尺寸。
- 空間 480×192×384（中線 y 96、鏡像 y ↔ 192 − y）；子作品照這個大小建。
- 拆法照拉貝爾號：甲板每層一件、梯子每層一件、桅每根一件、channels 兩舷一件、船首喙、彈藥庫、舵、錨架各一件；砲、帆桁、小艇、羅經櫃、火藥桶、錨、爐灶、門、燈是外部模型。

## 用現有元件（`work sub=components`，2026-10-27 查）
| 東西 | 來源 | 備註 |
|---|---|---|
| 舷側輕砲 | `summit-stormkaap-01m-gun-6l` 縮 0.375（meta gun=4l） | 跟拉貝爾號同一個 scale ⇒ 遊戲裡同一份網格 |
| 方帆桁 | 憲法號 royal 系列，沿長度縮 | 照拉貝爾號 |
| 小艇 | `basecamp-ember-01m-boat`（cutter） | |
| 羅經櫃 | 夜隼號 binnacle | |
| 火藥桶 | 憲法號 powder barrel 0.2（kind=powder） | |
| 錨 | `basecamp-frigate-constitution-01m-anchor`（bower） | |
| 爐灶 | `gura-pinas-01m-galley`（荷蘭 kombuis，kind=galley） | 同是荷蘭船 |
| 艙壁門 | `gura-pinas-01m-door`（kind=door） | |
| 艙蓋 | 拉貝爾號／飛魚號的 hatch（kind=door） | 尺寸合才用 |
| 艉燈 | 三叉戟號船尾燈 | 照拉貝爾號 |
新做的只有本船的個性件（船首像、船尾 hek 的雕飾）與船殼、甲板、桅、舵這些照尺寸長的。

## 步驟 3 資料與新圖紙（2026-10-28）
查證：研究代理一輪 ⇒ `references/research_fluyt_2026-10-28.md`（原文引句、出處、查不到的清單）。
- **單上「沒核」那條（Witsen 1671 福祿特章節）核過了**：研究代理看了掃描頁影像（archive.org gri_33125008247716）。W p.159 的 gemeene Fluit 只有「lang over steven 130 voet, wijt 26½ voet, hol 13 voet 5 duim」與 verdeck 5'6"、wale 寬度 —— 其餘照 134 呎 pinas 的比例（原文明說）；那艘是兩層甲板、約 400 t 以上，比本單的 200–300 t 大。
  ⇒ 本船改用 **W p.160 的 Oostervaerder 規則**（100 呎 ⇒ 寬 22、深 11、100 last；115 呎 ⇒ 23½、150 last；125 呎 ⇒ 24、12、200 last；「Deze zijn maer van een holte, deck ofte dack」）內插 110 呎 ⇒ 約 130 last ≈ 260 噸〔估〕；桅桁照 **W p.130 實測 110–112 呎 Oostervaarder 的桅桁表**〔查〕。
- 單上的 ~24 m〔估〕不採用：Witsen 的 200–300 噸是 100–115 呎（28–33 m）。

設計 `design/plan.json`（每個數字的 `src`）；`design/plan_stage3.py` 一次性寫前半段（之後的段落各步驟自己改）。程式（出處：ame-labelle-01m/design）：
- `lines.py` 照抄（結構）；`draft_lines.py` ⇒ `sheet01_lines_v1.png`、`verify_lines.json`、`masks/hull/hull_01.vox.txt`（138,440 格；外板 1、肋骨 141、內板 177；水線 z 30 以下灰白 182）。
- `layout.py` 照抄；`draft_layout.py`（畫布換成本船大小）⇒ `sheet02_layout_v1.png`、`verify_layout.json`。

| 項目 | 讀數 | 設計數（出處） |
|---|---|---|
| 長（艏柱到艉柱，主甲板 z 36） | 311.4 格（31.1 m）；格子 312 | 110 呎 ＝ 311.4（W p.160 內插〔估〕） |
| 龍骨 | 257.6 | 91 呎（VY p.140 比例〔估〕） |
| 艏柱傾出／艉柱傾出 | 48.1／5.7 | 17／2 呎（VY p.140 比例〔估〕） |
| 寬 | 67 格（寬只能奇數） | 23 呎殼板內 ＋ 外板 ≈ 66.6 |
| wing transom 寬（z 46） | 33 | VY p.142 verwulf 照比例 0.51 B〔估〕 |
| 內傾（船腰舷牆頂，每舷） | 6 格 | VY p.141 33 duim 照比例 ≈ 2 呎〔估〕 |
| 吃水 | z 30 | 〔估〕3.0 m |
| 排水量（水線下實心 × 1.025） | 394 t | 載貨約 260 t（130 last）只當量級 |
| 長 ÷ 寬 | 4.65 | 沉船實例 4.6–4.9〔二手〕 |
| 船殼牆 | 138,440 格；1 元件、空腔 0、鏡像差 0 | — |

- 甲板（甲板面 z）：貨艙地板 7（x 100–330）、主甲板 36（最低處 x 255；舷弧 船尾 +6、船頭 +8）、後甲板 58（x ≤ 121，halfdek）、船首樓 59（x ≥ 345，bak 8–10 呎〔查 W p.160〕）。
- 砲門：每舷 4 個、7×6 格、門檻 6（VY p.142：23 × 27 duim、門檻 23 duim〔查〕），中心 x 148.5、178.5、243.5、278.5（避開主桅 channels）；4 磅砲 8 門〔估〕。
- 桅（W p.130〔查〕）：前桅 x 344（腳 z 14、頂 276）、主桅 x 211（腳 z 7、平台 208、上桅頂 340）、後桅 x 110（腳在主甲板、頂 175、lateen 11 m〔估〕）、艏斜桅 13.2 m 32°；主桁 14.4 m、前桁 11.9、上桅桁 8.1／6.8。沒有頂桅（表裡沒有）。
- 圓艉：wing transom（wulf）z 46 以下收到艉柱，水線以上往外鼓（ronde hek）；以上是窄的平 hek（33 格）。

讀數與反向對照：
- `draft_lines.py --probe=half_beam=3` ⇒ 全寬 67 → 73；站 x 120／160／240／320 的水線半寬 28／33／33／29 → 31／36／36／32（每站 +2～+3）。
- `draft_layout.py --probe=port=main:2:+3` ⇒ x0 [145, 175, 240, 275] → [145, 178, 240, 275]。
- 產生程式重跑：5 個輸出檔（清單、兩張圖、兩份 verify）逐位元組相同。
- 🩸 v1 transom_ratio 照全寬算（0.49）⇒ wing transom 只有 29 格（那個高度已經內收 4.7 格）⇒ 改照那個高度的半寬 ⇒ 0.55 ⇒ 33。
- 🩸 v1 aft_pow 1.6 的水線半寬在船尾像楔子 ⇒ 2.1（圓艉）。

## 步驟 4 船殼落格、砲門、塗裝、船尾窗（2026-10-28）
- 船殼：標記 `船殼:begin`（upto=start）→ `design/tools/stamp_lists.py abigail-fluyt-01m 0 masks/hull/hull_01.vox.txt`（1 刀，placed 138,440 ＝ 清單）→ `船殼:end`。
- 砲門與塗裝：`design/plan_stage4.py` 寫 plan.paint／stern；`design/draft_ports.py`（出處拉貝爾號）⇒ `masks/ports/carve.vox.txt`（1,058，顏色守門）、`paint.vox.txt`（16,228，stampvox overwrite=1）、`verify_ports.json`、`sheet03_ports_paint_v1.png`；標記 `砲門塗裝:begin／end`。
  - 塗裝（plan.paint）：原木底 177；兩道黑 barghout（甲板 −7..−5、−1..＋1，照舷弧；W p.159 的 barghout／vulling 交錯，單層甲板只留兩道）；以上到舷頂下一格深綠 45；每個 x 船殼最高那一層黑 36；砲門框紅 160；wulf（z 46）以上的窄 hek 綠底、wulf 那一列與頂下一列金 248；船長室兩扇窗（寬 5、高 5，z 50–54，玻璃 87、金框）。
- 讀數：
  - **結果帳**（`tools/check_stage3.py mark=砲門塗裝:end`，作品從 export 讀）：137,382 ＝ 船殼 − 刻 ＋ 換色，缺 0、多 0、色差 0。
  - 8 個砲門開口從作品量：裡面還有實心的 0 個。**正向對照**：同一把尺量 `船殼:end` ⇒ 8 個全報（各 126 格）。**反向對照**：`draft_ports.py --probe=skip_port=main:2` ⇒ 只報第 2 門兩舷（各 126）。
  - 船殼線形對照（`tools/check_hull.py`，站距 8、高度每 3 格）：719 點差 0；`probe_x=244`（設計那一站 +3）⇒ 報 17 點、最大 3。🩸 抄來的站範圍是拉貝爾號的 x 60–224、z ≤ 47 ⇒ 第一次 probe_x=240 報 0 點（那一站根本沒量）⇒ 範圍換成本船 x 60–380、z ≤ 69。
  - 引擎 `stats structure=1 mirror=y:96`：1 元件、空腔 0、鏡像差 0。
- 過程圖 `overlays/stage4_hull_{bowq,sternq,side,stern}.png`：從正後方看是梨形（下面圓鼓、往上內收、上面窄 hek）。
- ⚠ 看得到的：艙裡是空的（甲板在步驟 5）；船頭圓到舷頂（船首喙、獅子船首像在步驟 6）；hek 上的雕飾板、假砲門（W p.160 的 looze poorten 圓洞）在步驟 6。

## 步驟 5 甲板、梯子（2026-10-28）
設計 plan.json `decks_build`（`design/plan_stage5.py` 寫，重跑逐位元組相同）；產生 `design/draft_decks.py`（出處拉貝爾號；多一個 `well_to`）⇒ `masks/decks/<層>.vox.txt`、`masks/ladders/<上面那層>.vox.txt`、`ladder_points.json`、`verify_decks.json`、`sheet04_decks_v1.png`；落格 `design/tools/build_decks.py`。
- 甲板（甲板面 z）：貨艙地板 7（x 100–330 的設計範圍，船底兩頭抬 ⇒ 實際 117–326）、主甲板 36（舷弧 船尾 42、船頭 44；一路鋪到船尾 ⇒ 後甲板底下是船長室）、後甲板 58（x ≤ 121）、船首樓 59（x ≥ 345）。板：艙裡 177、露天 209；樑每 10 格（VY p.141 樑距 3½ 呎）寬 2、深 1–2，136；圍欄與 break 141。
- 開口：後艙口 x 157–167（半寬 5）、主艙口 222–236（半寬 7，主桅前）、前艙口 299–311（半寬 5）；貨艙梯子的井 254–272；桅孔（前 r 2.5、主 3；後桅腳在主甲板 ⇒ 主甲板不開、後甲板開）。
- 前桅挪到 x 352（穿過船首樓；VY 艏柱後 0.064 L）、艏斜桅腳 x 360 —— 🩸 v1 前桅 x 344 跟船首樓 break x 345 疊在一起。
- break：x 121 艙壁（主甲板到後甲板、中線門 5 格寬 15 格高 ⇒ 船長室）＋ 5 格胸牆；x 345 艙壁（中線門 ⇒ 船首樓底下）＋ 5 格胸牆；梯子頭留口。
- 梯子 5 座（每 3 格一階、每階 2 格、踏板 7 寬）：貨艙→主甲板（井，x 252 往船頭，9 階）、主甲板→後甲板兩舷（x 136 往船尾、頭 x 118）、主甲板→船首樓兩舷（x 329 往船頭、頭 x 348）。每層都走得到（reach：hold 1、main 5、quarter 2、forecastle 2）。
- 🩸 貨艙梯子比拉貝爾號長（9 階對 6 階）⇒ 抄來的井寫死 xs ＋ 2..16、head 在 ＋18 ⇒ hi 點在主甲板板底下（ladder_point_problems 報了）⇒ 加 `well_to`（＋20）、head_x 274。
- 貨艙地板底下封死的空氣 2,218 格（五段）照拉貝爾號的作法填成樑色 136。
- 子作品（parent 船殼、tags sub、0.1 m、480×192×384、at 0,0,0）：`-deck-{hold,main,quarter,forecastle}`、`-ladders-{main,quarter,forecastle}`（關聯 `梯子`，meta kind=ladders；固定點 `<梯名>.foot／lo／hi／head`）。
- **甲板 meta**（§9.3，`design/decks_meta.tsv`）：每層 `export format=vxk links=none` ⇒ Blockside `src/decks.py` 量 ⇒ 照量的 floor／thick，名字換成 plan 的。level：hold 0、main 1、quarter 2、forecastle 3。
- 預覽 preset：`藏船殼`。
- 船殼關聯重接一次（加關聯時作品框 448×192×352、後來放大 ⇒ links 報「尺寸變過」）。

讀數：
- 設計那一側：零件重疊 0、跟船殼重疊 0、每件鏡像差 0、梯子點問題 0、砲門往艙裡被擋 0。
- **結果帳**（`tools/check_decks.py`，每件從匯出讀）：7 件 37,440 格，缺 0、多 0、色差 0；跟船殼重疊 0、彼此重疊 0。
- **組起來**（引擎 stats，組裝件）：174,822 格、1 元件、空腔 0、鏡像差 0。
- **梯子點**（組裝件 parts）：5 座、20／20 點、跟設計差 0；每點那一格空、腳下實心、頭頂 14 格空。
- **反向對照**：`draft_decks.py --probe=drop_ladder=forecastle-S` ⇒ 4 座；船首樓 reach 只剩 forecastle-P。
- 產生程式重跑：11 個輸出檔逐位元組相同。過程圖 `overlays/stage5_decks_nohull.png`。
- ⚠ 沒做：空艙房（§9.2；船長室、船首樓底下可以當艙房，步驟 10 擺完東西再量）；樓梯自檢（ladcheck）在步驟 14 匯進遊戲之後跑。

## 步驟 6 裝飾（2026-10-28）
設計 plan.json `deco`（`design/plan_stage6.py`）；產生 `design/draft_deco.py`（出處拉貝爾號的船首喙與量法；船首像、hek 的圖、假砲門重寫，百合花與假艉廊拿掉）⇒ `masks/deco/{head,figurehead,paint}.vox.txt`、`verify_deco.json`、`sheet05_deco_v1.png`；落格 `design/tools/build_deco.py`（拉貝爾號是手打的 CLI，本船寫成程式：head／figure／paint／glass／behind／glassfill／lamp）。
- 船首喙 `-head`（關聯 `船首喙`，1,279 格）：knee of head 伸出艏柱 1.8 m（中線 3 格厚、前端上緣金）＋每舷兩根 head rail。🩸 v1 rail 前端 z 51／48，第一根浮在 knee 頂（z 50）上面 ⇒ 組裝件 3 個元件 ⇒ 49／46（delta_apply 刻 58、貼 62）。
- 船首像 `-figurehead`（外部模型 `船首像`，meta deco=1，420 格）：荷蘭紅獅（W p.85 pinas 的 leeuw〔查〕；紅身、金鬃、金冠、紅舌）趴在 knee 前端，1.5 m 長。v1 獅腳踩進 knee 4 格 ⇒ put 讓先放的部件優先。
- hek 的海公雞（船殼換色，船尾面那一層 45 格）：9 × 10、金身紅冠（船名 Zeehaen）；W p.83 船艉平板照慣例裝紋章〔查，pinas〕。⚠ 圖本來就不對稱 ⇒ 組裝件鏡像差 19 對是它。
- 圓形假砲門（W p.160 looze poorten〔查〕；換色，不開洞）：兩舷船尾 x 86 z 50、船頭 x 356 z 52，直徑 0.5 m、黑洞紅框，84 格。
- 船尾窗玻璃（Ship_Materials §9.5）：船殼裡色 87 的 50 格 `work sub=split … confirm=1` ⇒ `-stern-glass`（雙生關聯 `船殼-窗玻璃`，meta material=glass）；玻璃後面的船殼牆刻穿 50 格（`masks/glass/carve_behind.vox.txt`，顏色守門）⇒ 緊鄰那格空 50／50。
  🩸 hek 面是斜的（艉柱 9°）⇒ 每扇窗最上一排比下面往船尾一格、只在斜角相碰 ⇒ 玻璃 4 片 ⇒ `glassfill` 往下一排補 1 格（10 格，`masks/glass/fill.vox.txt`）⇒ 60 格、2 片（一扇一片）。
- 艉燈（外部模型 `艉燈`，meta kind=light）：三叉戟號船尾燈 0.5 倍，站在 hek 頂中間（x 50.5、z 69）。🩸 v1 量 hek 頂沒限制在船尾 ⇒ 整條中線取中點 x 217（半空中）⇒ 只看 x < 70。
讀數：
- 設計：零件重疊 0、跟船殼重疊 0、每件鏡像差 0、假砲門鏡像差 0；艏斜桅撞格 0。
- **結果帳**：船殼 137,282 ＝ 船殼清單 − 砲門 ＋ 塗裝 ＋ 裝飾換色 − 玻璃 − 玻璃後面，缺 0／多 0／色差 0；船首喙 1,279、紅獅 420 缺 0／多 0／色差 0。
- 組起來：176,061 格、1 元件、空腔 0；鏡像差只有海公雞那 19 對。
- **反向對照**：`--probe=emblem_dy=3`（公雞往右舷偏 3）⇒ 中線左右 22／17 → 1／26。
- 產生程式重跑：5 個輸出檔逐位元組相同。過程圖 `overlays/stage6_deco_{bowq,sternq}.png`。

## 步驟 7 桅與帆桁（2026-10-28）
設計 plan.json `masts`、`rig_build`（`design/plan_stage7.py`）；產生 `design/draft_masts.py`（出處拉貝爾號：本船用回收穫號的 cofa ＝ 荷蘭圓桅樓；畫布換本船）⇒ `masks/masts/<桅>.vox.txt`、`masks/yards/lateen-mizzen.vox.txt`、`yards_placement.json`、`yards_lateen.json`、`verify_masts.json`、`sheet06_masts_v1.png`；落格 `design/tools/build_masts.py`。
- 桅（子作品，關聯 前桅／主桅／後桅／艏斜桅）：前桅 x 352 腳 z 20.5（踩在艏柱 deadwood 裡 58 格，同拉貝爾號腳在 breasthook）、平台 177、上桅頂 283；主桅 x 211 腳 z 7、平台 208.5、上桅頂 340.5（離龍骨底 34 m）；後桅 x 110 腳在主甲板 z 40、頂 175；半徑 主 2.5→1.8、前 2.2→1.6、後 1.6→1.2、上桅 1.6／1.4→1.0／0.9（W p.130 主桅 17 palm）。
- 桅樓（cofa）：主 r 12、前 r 11、籃子 6 格高、綠腰帶、金頂（W p.94 pinas 的 mars 直徑照船長 × 0.82；遊戲的桅頂水手站半徑 9／12 一圈）。後桅沒有桅樓。
- 艏斜桅：腳立在船首樓甲板 x 360、仰角 32°、13.2 m（W p.130）、半徑 2.2→1.4；從船頭欄杆上方越過 ⇒ 船殼開孔 0 格。
- 方帆桁（外部模型，放在各自的桅子作品裡；照拉貝爾號沿用憲法號的元件、只沿長度縮，挑長度最接近的）：主帆桁 14.4 m ← main-topgallant（×1.007）、主上桅帆桁 8.1 ← main-royal、前帆桁 11.9 ← fore-topgallant、前上桅帆桁 6.8 ← mizzen-royal、spritsail 8.2 ← fore-royal；brace course −15°、topsail −17°；meta kind=yard、mast、yard、sail、length_m、pivot_anchor、turn_axis、rotate_z_deg。
- lateen（後桅，子作品 `-yard-mizzen-lateen`、723 格、固定點 pivot／sling／fore／peak／jackstay-01..13）：11 m、40°、吊點 40%；meta yard=gaff、rig=lateen；後端在船尾裡面 0.14 m。
讀數：
- 設計：每件鏡像差 0；帆桁撞格 0（6 根）。
- **結果帳**（`tools/check_stage6.py`）：4 件桅＋lateen 缺 0／多 0／色差 0；船殼 ＝ `裝飾:end`（孔 0 格）差 0；帆桁模型 6 根 meta 與來源固定點問題 0。
- **組起來**：187,062 格、1 元件、空腔 0；鏡像差只有 hek 海公雞 19 對。
- **反向對照**：`--probe=pivot=yard-main-course:-150`（主帆桁吊點降 15 m 到甲板附近）⇒ 主帆桁撞格 0 → 54，其他 0。
- 產生程式重跑：10 個輸出檔逐位元組相同。過程圖 `overlays/stage7_masts.png`。

## 步驟 8 索具、帆、旗（2026-10-28）
設計 plan.json `rigging`（`design/plan_stage8.py`）；產生 `design/draft_rigging.py`（出處拉貝爾號；本船有桅樓 ⇒ 上桅 shrouds 從桅樓籃子頂上起、futtock 從平台底下起、main topmast stay 綁前桅樓後緣；下桅繩梯 climb=1；繫索點、bobstay 改讀 plan；旗換荷蘭三色旗）⇒ `masks/rigging/channels.vox.txt`、`rigging_plan.json`、`textures/ensign.png`、`verify_rigging.json`；套用 `design/tools/rigging_apply.py`（ratlines 那一步多帶 climb／foot／head）。
- channels `-channels`（關聯 `支索板`，972 格，兩舷一件）：舷頂那兩格的舷外（砲門頂上面）、寬 3；deadeye 每舷 前 4＋1、主 5＋1、後 3（W 的 pinas 主 7、前 6、後 4 照船長縮〔估〕）。前桅在船首樓裡 ⇒ deadeye 從桅前 5 格起、間距 3（x 357–345）；後桅在後甲板裡。
- 靜索 60：shrouds 24、topmast backstays 4、topmast shrouds 12（桅樓籃子邊上一舷 3 根、前後各 4 格排開）、futtock 12、stays 5（fore → 艏斜桅、fore topmast → 艏斜桅帽、main → 前桅腳（船首樓甲板）、main topmast → 前桅樓後緣、mizzen → 主桅腳）、bobstay 1、艏斜桅 shrouds 2。
- ratlines：橫繩組 10（三根下桅 × 兩舷、兩根上桅 × 兩舷，step 4）⇒ 170 道（lower 116、topmast 54）；**前、主桅下桅 4 組繩梯 climb=1**（foot ＝ deadeye 中段往船內、舷牆內側的甲板再往內 2 格；head ＝ 桅樓平台這一舷的邊往裡 3 格）；上桅、後桅不標。
- 帆 8：fore／main course、topsail（帆角綁帆桁模型 earing；course 帆腳在舷頂上 3 格，sheet 往後、tack 往前綁舷頂）、spritsail、mizzen lateen（tack 綁主甲板 x 140、sheet 綁船尾舷頂）、ensign（荷蘭紅白藍三色旗，`textures/ensign.png`，掛 lateen 後端）、pennant（主桅頂紅長旗）。預設風 4.5,−1.5,0、3 秒。
- meta 25：帆 8＋帆自己的繩 17。
- 🩸 bobstay：v1 從 knee z 40 綁到艏斜桅 75% ⇒ 穿 knee 9 格、而且從紅獅身上穿過去（模型不在格子檢查裡，另外量）；knee 前緣往前斜、紅獅趴在 knee 尖 ⇒ 從 knee 往前上拉的線幾乎都會碰到其中一個 ⇒ 紅獅往後挪 8 格（knee 尖後 12 格）＋ 繩從 knee 前端**外一格**（z 44）綁到 70% ⇒ 穿 knee 0、穿紅獅 0（試過 z 30–48 × 0.45–0.75，只有這組兩邊都 0）。
帆裝三段（Ship_Rigging §9.1 的預設，沒有寫 set）：
| 帆裝 | 張哪幾面 |
|---|---|
| 收帆 | fore-topsail、main-topsail（2） |
| 戰鬥帆 | ＋ mizzen-lateen（gaff）（3） |
| 滿帆 | ＋ fore／main course、spritsail（6） |
讀數：
- 設計：channels 鏡像差 0、跟船上的格重疊 0；固定點落在實心格 0；靜索（兩端各留 3 格）穿過實心 0；bobstay 穿過紅獅 0；帆自己的繩沒 meta 0；繩名重複 0。
- 引擎：繩 247（standing 60、ratlines 170、running 17）全部 ok、broken 0；帆 8 面 ok。最鼓：主 course 6.0 m（帆高 14.3 m，fullness 1.05 照規格，⚠ 偏飽，沒調）、前 course 4.5、topsail 2.5–2.9、lateen 1.5、spritsail 2.1。
- **結果帳**：channels 作品 ＝ 清單（delta_apply --dry 差 0）。組起來 188,034 格、1 元件、空腔 0。
- **反向對照**：`--probe=nometa=main-course.sheet-S` ⇒ 「帆自己的繩沒 meta」報那一條。
- 產生程式重跑：4 個輸出檔逐位元組相同。過程圖 `overlays/stage8_rig_bowq.png`。

## 步驟 9 砲（2026-10-28）
設計 plan.json `guns_build`（`design/plan_stage9.py`：只換迴旋砲位置與出處）；產生 `design/draft_guns.py`、`design/gunsim.py`（照抄拉貝爾號）⇒ `guns_placement.json`、`verify_guns.json`；落格 `design/tools/build_guns.py`；檢查 `design/tools/check_stage8.py`。
- 4 磅砲 8 門（每舷 4）：風暴角號 6 磅長砲 `summit-stormkaap-01m-gun-6l` 縮 0.375（跟拉貝爾號同一個 scale ⇒ 遊戲裡同一份網格）、meta kind=gun、gun=4l；掛在 `甲板-main`，名 `砲M-<S|P>01..04`；P 舷 mirror=y。福祿特帶的砲口徑查不到 ⇒ 4 磅〔估〕。
- 迴旋砲 6 門（每舷 3）：皇家號叉架後膛砲縮 0.39（照拉貝爾號）、meta gun=pierrier、mount=turret、arc −80,80、rate 45；插在舷牆頂：後甲板 x 70、84（後桅 channels 後面）、船首樓 x 374（前桅 channels 前面）。W p.160：往西的船人多、帶武器〔查〕；數量設計決定。
- 🩸 **砲門門檻 6 → 4**：v1 門檻照 VY p.142 的 23 duim（大型 fluit 的砲架）⇒ 這門 4 磅砲的砲軸只在甲板上 5 格、砲管頂在門檻上 ⇒ 6 門推不出去（砲口在船殼裡 1.8 格）。改 plan_stage3 的 sill，3→9 的 plan 全部重跑（plan 只差 sill 與 src 兩格）⇒ `draft_ports.py` 重產（刻 1,058、換色 16,228，同數量不同格）⇒ `tools/hull_expected.py`（加了裝飾換色、窗玻璃拆走、玻璃後面三步）組出新的船殼設計帳 ⇒ `tools/delta_apply.py` 刻 336、貼 336、換色 528（標記 `砲門降低:begin／end`）⇒ 再 --dry 差 0；甲板清單重跑逐位元組相同、砲門往艙裡被擋 0；8 個砲門從作品量開口裡實心 0。
- 🩸 順手抓到：`draft_deco.py` 讀「現在的船殼」⇒ 換色落格之後重跑，換色清單變 0 格（步驟 6 的「重跑逐位元組相同」是落格之後兩次比、沒抓到）⇒ 改讀 `裝飾:begin`；舊的船殼設計帳先拿舊砲門清單組 ⇒ 跟作品差 0（帳組得對），再換新的。
- 擺法：舷側砲從船殼外面沿砲身往裡退（0.5 格一步）到零碰撞（格心＋八角、inset 0.2）；退 2–3 格、砲口伸出 4.7–5.7 格、砲軸 z 42–44。
讀數：
- 設計：14 門全部 ok（零碰撞、砲口伸出、砲口空、腳下有甲板 support 1.0）；砲跟砲不撞；兩舷對稱差 0。
- 作品（`tools/check_stage8.py`，從 CLI 讀）：模型 14＝設計 14、CLI ok 14；參數差 0；外框（gunsim vs CLI）最大差 0.045 格；碰撞 0；砲口不在船殼外 0；meta 不合 0（4l 8、pierrier 6）。
- **反向對照**：`--probe=push=砲M-S01:4`（往外推 4 格）⇒ 那一門碰撞樣本 1,881，其他 0。
- 產生程式重跑：2 個輸出檔逐位元組相同。過程圖 `overlays/stage9_guns.png`（sails=0）。
- ⚠ 沒做：砲具與砲索（Ship_Guns §4.4，「要的話」；小砲、甲板窄，同拉貝爾號）；砲門蓋板不做（露天甲板舷牆上的砲門，刪了步驟 12）。

## 步驟 10 彈藥庫與甲板物件（2026-10-28；拉貝爾號的步驟 10＋16 一起做）
設計 plan.json `gear_build`、`fit_build`（`design/plan_stage10.py`；繩梯 foot／head 從 rigging_plan.json 抄）；產生 `design/draft_gear.py`（量的範圍放大到 x 480）、`design/draft_fit.py`（空間、中線、主甲板 floor 改讀 plan／decks_meta.tsv；windlass 可以 skip）⇒ `masks/gear/{magazine,skids}.vox.txt`、`masks/fit/{hatch-aft,hatch-main,hatch-well,hatch-fore,hold_room}.vox.txt`、`gear_placement.json`、`fit_placement.json`、`verify_gear.json`、`verify_fit.json`；落格 `design/tools/build_gear.py`、`build_fit.py`；讀數 `tools/check_stage9.py`、`tools/check_stage16.py . -`。
- **彈藥庫** `-magazine`（關聯 `彈藥庫`，meta kind=magazine、pos=aft、powder_lb=2000；5,527 格）：貨艙後段 x 124–152、地板 z 8、頂 z 35（主甲板樑下）；門朝船頭（x 152）。銅皮 168、松木地板 177、橡木框 136。固定點 blast (138,96,22)、door (152,96,9)。火藥桶 20 桶（憲法號 -powder-barrel 0.2、kind=powder、powder_lb 100）全在底層。⚠ 20 是照收穫號每門 2.6 桶換算（8 門 4 磅＋6 門迴旋砲），不是史料。
- **小艇架** `-boat-skids`（關聯 `小艇架`，304 格）：x 262、288 兩座橫架，樑 z 47–48（4 磅砲頂約 46）、立柱 |dy| 7–8。🩸 v1 立柱 |dy| 6–7 跟井的艙蓋撞 4 格 ⇒ 7–8（delta_apply 刻 68、貼 76）。
- 模型：小艇（餘燼號 cutter 縮成 4 m，0.222 ＝ 拉貝爾號同一份網格，kind=boat）擱在小艇架上 x 255–295、z 明寫 49；羅經櫃（夜隼號，kind=binnacle）後甲板 x 92、dy +8；**主絞盤**（餘燼號 capstan 0.2，kind=capstan）主甲板中線 x 190.5 —— 船首樓底下的主甲板只到 x 366、前桅在 x 352 ⇒ 拉貝爾號那種橫的 windlass 放不下、放在露天會切斷主甲板 ⇒ 直立絞盤（fit_build.windlass skip）。
- **艙蓋 4 片**（`甲板-main` 的模型，kind=door、鉸鏈沿 +x 在左舷那一邊）：後艙口 `-hatch-aft`（13×13，z 41）、主艙口 `-hatch-main`（17×17，z 39）、貨艙梯子的井 `-hatch-well`（21×13，z 39，掀 30°：上面是小艇架橫樑 z 47）、前艙口 `-hatch-fore`（15×13，z 41）。主甲板離水線 0.6 m ⇒ 露天的開口都要門（Ship_Fittings §9.7）。蓋底 ＝ 從作品量的圍板頂最高那一層 ＋ 1（後、前 40 → 41，主 38 → 39，井 36–38 → 39）。開口（蓋子正下方那一層的空格）134／225／222／158 格。
- **廚房**：光榮號爐灶 0.18（拉貝爾號同一份網格），meta kind=galley（沒有 deco），在船首樓底下的主甲板 x 355–363、右舷 dy +5..+11（前桅在中線 x 352）；荷蘭船的 kombuis 在 bak 底下（W 的 pinas）。四個面都站得住廚師（faces_ok 4）。
- **船長室**（`-cabin-room`，`甲板-main` 的關聯 `艙房`，meta kind=rooms，542 格）：後甲板底下 x 88 一道橫艙壁（主甲板到後甲板底下、中線門洞 0.5 m 寬、到 z 55），隔出船尾的舵艙（steerage）與前面的船長室；框 `cabin.min` (89,85,42)、`cabin.max` (102,107,55)、`cabin.door` (88,96,42) ⇒ 1.4 × 2.3 × 1.4 m、非空氣 0、沒地板 0。🩸 v1 框到 x 103 ⇒ 舷弧在 x 103 掉一格、沒地板 23 格 ⇒ 到 102。⚠ 門開在長邊、病床 1.9 m 只能沿 y 擺，配置頁可能寫放不下（Ship_Decks §9.2：照樣標）。
- 下桅繩梯 4 組（步驟 8 做的）：foot、head 都站得住、不在模型外框裡。
讀數：
- **結果帳**：彈藥庫 5,527、小艇架 304、船長室 542、艙蓋 192／320／296／218，各自缺 0／多 0／色差 0；新格落在實心上 0、封閉空腔 0、浮空 0；鏡像差 0。
- 模型 23＝設計（小艇、羅經櫃、主絞盤、火藥桶 20）、CLI ok 23；參數差 0、撞實心 0、腳下 12 格內沒有實心 0。艙蓋 4、爐灶的外框＝設計、meta 對；艙蓋撞實心 0、撞模型 0。
- 彈藥庫：powder_lb 2,000 ＝ 20 桶 × 100；blast 空氣、door 空氣且腳下實心。
- 組起來：194,407 格、1 元件、空腔 0；鏡像差只有 hek 海公雞 19 對。
- **反向對照**：`draft_gear.py --probe=nokind=小艇` ⇒ 沒 kind 的報 小艇；`draft_fit.py --probe=room_y0=60` ⇒ 艙房非空氣 0 → 589；`--probe=galley_x=352 --probe=galley_y=96`（爐灶擺到前桅上）⇒ 撞實心 0 → 159。
- 產生程式重跑：清單與擺放逐位元組相同；verify_gear.json 只差「組裝件格數」一格（188,034 → 188,576：後來落的船長室艙壁）。過程圖 `overlays/stage10_gear.png`。

## 步驟 11 舵、舵柄、錨（2026-10-28）
設計 plan.json `rudder_anchor_build`（`design/plan_stage11.py`）；產生 `design/draft_rudder_anchor.py`（出處拉貝爾號；舵柄掛哪一層改讀 plan）⇒ `masks/rudder/{rudder,tiller,anchor_gear}.vox.txt`、`rudder_anchor_placement.json`、`verify_rudder_anchor.json`；落格 `design/tools/build_rudder_anchor.py`；檢查 `design/tools/check_stage95.py`。
- **舵** `-rudder`（組裝件模型 `舵`，1,283 格）：沿艉柱後緣（斜 9°）從龍骨底到 z 52（wulf 上面一點：舵頭從窄 hek 的舵孔 hennegat 進船裡；在 hek 海公雞 z 57 底下）；3 格厚、舵葉 1.2 m 收到 0.4 m 的舵頭；水線下白、上黑、每 8 格鐵箍。meta kind=rudder、hinge (60, 96.5, 0)、axis (−0.1564, 0, 0.9877)、max_deg 35、turn_axis=hinge、spin=rudder、spin_k 35；固定點 stock-top (49,96,52)。
- **舵柄** `-tiller`（`甲板-main` 的模型 `舵柄`，76 格）：福祿特在後甲板底下的舵艙用 whipstaff 推舵柄 ⇒ 舵柄獨立模型 kind=tiller（Ship_Helm 操舵鏈；whipstaff 不另做）：舵頭在 hek 內側（x 58、z 43–50），舵柄沿中線往前到 x 84（船長室艙壁 x 88 前面）、z 49–50；spin=rudder、spin_k 35。🩸 抄來的舵柄掛 `甲板-quarter`（拉貝爾號的舵柄在後甲板上）⇒ 本船在後甲板底下 ⇒ plan 加 host、`unmodel` 舊的、掛 `甲板-main`。
- **錨**：共用錨元件（憲法號 bower）縮 0.5（錨幹約 2.9 m；約 260 噸的船）×2，meta kind=anchor、anchor=bower，掛在錨架 `-anchor-gear`（關聯 `錨架`，750 格，兩舷 billboard）；照拉貝爾號的搜法：錨臂順著船殼切線（rz ±76）、往外推到零碰撞 ⇒ x 360、錨環 z 68（船首樓舷牆頂）、離船殼 11 格、錨冠托板 z 38–39。🩸 v1 錨環試 z 58–64 ⇒ 托板落在 z 29（水線上）⇒ 試 68–74。錨鏈孔固定點 hawse-S／P (372, 107／85, 50)（只登記、沒開孔）。
讀數：
- 設計：舵、舵柄、錨架落在實心上 0、鏡像差 0；舵柄的舵頭腳下都是甲板。
- **結果帳**：舵 1,283、舵柄 76、錨架 750 缺 0／多 0／色差 0。
- 舵：stock-top 8 格內有船格（曼哈頓 3）；跟組裝件重疊 0；轉 ±35° 掃進實心 0。錨 2 隻：撞實心 0、腳落在錨架上、來源有 ring；hawse 兩舷都在船殼格上。檢查問題 0。
- 讀回（`export format=parts`）：舵 kind=rudder、spin rudder；舵柄（甲板-main）kind=tiller、spin rudder。
- 組起來：195,157 格、1 元件、空腔 0。
- **反向對照**：`--probe=shift=錨-S:-6` ⇒ 錨-S 撞 1,030、錨-P 0。
- 產生程式重跑：5 個輸出檔逐位元組相同。過程圖 `overlays/stage11_rudder_anchor.png`。

## 步驟 14 給遊戲的 meta 與匯入 Blockside（2026-10-28）
- 船殼關聯 meta kind=ship、waterline_z=30。`work sub=ropecheck`：繩 247、494 端全部 ok；link_overlap 0、link_clipped 0。
- 在自己的 Blockside worktree（從 dev 89f3621 開，`_cache` 從共用工作區抄進去）：`admin.py import --work abigail-fluyt-01m-assembly --id zeehaen --name 澤漢號`；`admin.py ids --id zeehaen` 發號（ladders-1..3、magazine-1…，寫回 10 件作品）。
- 第一次匯入檢查 ✗ 2：後甲板、船首樓找不到火藥取用點（迴旋砲）⇒ 彈藥庫關聯 meta `hoist=ladders-2#quarter-S,ladders-3#forecastle-S`（Ship_Magazine §8，同拉貝爾號）⇒ `metasync`。
- game.json 手填 ships[zeehaen]：role merchant；geo spar [37,60]、marines [43,75]、center 60、aim 37、aimZ [5,340]、deckAim [37,59]、rigAim [75,330]（照下面步驟 15 的高度）；cfg pump 3；crew 軍官 2、舵手 1、桅頂 1、陸戰隊 6、marineGap 14、monkeys 1、handsK 0.25、航海士 0；names。⚠ import／ids／metasync 把整份 game.json 重排 ⇒ 從 HEAD 重建、只加這一筆（34 行全是新增）⇒ `admin.py build`、shipcheck。
- **匯入檢查 ✗ 0、⚠ 3**：桅頂水手 2／3（後桅沒有桅樓）；後甲板右舷、船首樓右舷梯子的梯腳被取用點的火藥桶擋到（遊戲擺桶的位置 —— 修法在遊戲那側，同拉貝爾號）。火藥 14／14 門走得到取用點；操舵 舵令 ⇒ 舵柄 ⇒ 舵 100%；廚房 1 座（站得住的面 4）；門 4 扇；**樓梯自檢 5 座 ✗ 0、⚠ 2**；甲板連通 4 層都接得到；超載極限再多載 353 噸。卡片：394 噸（排水量）、31.3 m、14 門、船員 55。
- 戰局（只當讀數）：`?demo=60&dump=1&seed=3&ship=zeehaen,falcon&headless=1` ⇒ 澤漢號開 57 發、命中 32、被夜隼號打斷兩根桅；有畫面的 `?demo=60&seed=3&ship=zeehaen,labelle` 看得到張帆、航跡、開砲、船尾的荷蘭旗。
- 提交：Blockside a8028f8（分支 abigail/zeehaen）⇒ 進場（coding）快轉合進共用 dev ⇒ 已推 dev（89f3621..a8028f8，只有這一筆）。共用工作區的 ship_cards.json 本來就有別人 shipcheck 留下的 9 行改動 ⇒ 合併前備份、還原、快轉，再寫回別人的改動＋我這一行（diff 裡沒有 zeehaen）。`_cache/zeehaen.vxk` 抄進共用工作區（cmp 相同、`admin.py verify` 1420 份網格逐個相同）；worktree、分支收了。合併的 post-merge 掛鉤重套了 Blocksail 的 battle.html（Blocksail 那側跟 gitlink 一起提交）。
- 新做的元件：沒有（全部現成；小艇、4 磅砲、爐灶跟拉貝爾號同一個 scale ⇒ 同一份網格）⇒ 不用標 render。

## 步驟 15 交船（2026-10-28）
給遊戲那側填 geo 的高度（格的 z；0.1 m／格）：龍骨底 0、設計水線 30、貨艙地板 7、主甲板 36（舷弧 船尾 42、船頭 44）、後甲板 58、船首樓 59、舷頂 船腰 50–56／艏艉樓 68；砲門 z 40–47（每舷 4 個，x 145／175／240／275）、4 磅砲軸 z 42–44、迴旋砲軸 z 72.7；桅樓平台 前 177／主 208.5、上桅頂 前 283／主 340.5、後桅頂 175；船殼 x 49（hek）–385（艏柱），船首喙＋紅獅到 x 404、艏斜桅頂 x 464（spritsail 帆桁 x 455）。
遊戲那側的 vxk 指紋：`zeehaen.vxk` c:b74d83259b82f016c59c1a8210606cbb68194507（Blockside a8028f8 的 config/vxk_lock.json）。

Ship_Game §10 檢查表：
| 項目 | 本船 |
|---|---|
| ropecheck | ✓ 247 繩、494 端全 ok（沒有 bind／snap／odd／manual） |
| 組裝件名 ＝ 船名、船殼「澤漢號 船殼」帶 sub | ✓ |
| meters_per_voxel、模型明寫 scale | ✓（每件子作品 0.1；模型 scale 都明寫） |
| sub=components 先查、能用的都引用 | ✓ 砲（6l→4l、pierrier）、帆桁（憲法號 topgallant／royal）、小艇、羅經櫃、主絞盤、火藥桶、錨、燈、爐灶；新做的只有本船的個性件（紅獅、hek 海公雞是換色）與舵、舵柄 |
| 槳帆船／撞角／從船殼伸出去的槳 | 不適用 |
| 爐灶：廚房或裝飾二選一 | ✓ 廚房 kind=galley（船首樓底下），站得住的面 4 |
| 缺的砲種做成通用部件 | 不適用（4l、pierrier 都在砲種表） |
| 砲、帆桁、火藥桶是模型且帶 meta；甲板物件帶 kind | ✓ |
| 舵是模型、kind=rudder、stock-top；spin | ✓（⚠ `__game.lostModels(0)` 沒有另外量；匯入檢查開局 2 秒沒報掉落） |
| 操舵鏈：舵柄 kind=tiller | ✓ 匯入檢查「舵令 ⇒ 舵柄 ⇒ 舵 100%」 |
| kind=ship waterline_z；notes 寫高度 | ✓ 上面那一段 |
| 梯子 kind=ladders、四點 | ✓ 5 座 20 點 |
| 樓梯自檢 ✗ 0 | ✓（⚠ 2：兩座梯腳被遊戲擺的取用點火藥桶擋到，修法在遊戲那側） |
| ratlines 是橫繩組；繩梯 climb | ✓ 橫繩組 10；前、主桅下桅 4 組 climb=1（head 在桅樓平台）；後桅沒有桅樓 ⇒ 不標 |
| 彈藥庫有火藥桶 | ✓ 20 桶；火藥 14／14 門走得到（hoist 後甲板、船首樓的梯子） |
| 甲板 kind=deck、每層有梯子 | ✓ 4 層；甲板連通 4 層都接得到 |
| 三角帆桁 yard=gaff＋rig=lateen＋fore | ✓ |
| 材質（鐵甲、金屬） | 不適用（全船木頭） |
| 窗的玻璃獨立關聯 material=glass | ✓ `船殼-窗玻璃` 60 格、兩扇各一片 6 連通、後面刻穿（⚠ 遊戲裡的透明沒有截圖看） |
| 空艙房 | ✓ 1 間：`甲板-main/艙房/cabin` 1.4 × 2.3 × 1.4 m；`rooms.py check` ✓ |
| 砲退到零碰撞、砲口在船殼外 | ✓ 14 門 |
| 砲身砲座拆兩件、裝甲、砲塔、蒸汽 | 不適用 |
| 迴旋砲 | ✓ mount=turret ±80（照皇家號；不是 pivot 砲門） |
| 露天出入口有門 | ✓ 4 扇 kind=door（後、主、前艙口與貨艙梯子的井；開口 134／225／222／158 格） |
| 舷側砲門蓋板 | 不做（露天甲板舷牆上的砲門，刪了步驟 12） |
| ropes／sails／models broken 0 | ✓ |
| 帆、旗、帆自己的繩 meta | ✓ 帆 8、繩 17；帆桁 meta sail／mast 對得上 |
| 帆裝三段 | ✓ 表在步驟 8（收帆 2、戰鬥帆 3、滿帆 6 面）；⚠ 遊戲裡 W／S 每一段沒有逐段看 |
| 組裝件 1 元件、空腔 0、link_overlap 0、對稱 | ✓（鏡像差只有 hek 海公雞的 19 對，圖本來就不對稱） |
| 產生程式重跑逐位元組相同 | ✓（每一步各自量過；verify_gear 只差組裝件格數一格，見步驟 10） |
| 匯出 vxk、對 checksum | ✓ 上面那一行 |
| 匯入檢查 ✗ 0、⚠ 都看過 | ✓ ⚠ 3 逐條列在步驟 14 |
| 舵、舵柄 spin | ✓ |
