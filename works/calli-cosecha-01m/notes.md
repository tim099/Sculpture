# 收穫號（La Cosecha）—— 西班牙大帆船，參考 1618 年 Ordenanza（0.1 m／格）—— 建造筆記

委託：Tim 2026-10-15（TASK-0589 傘，子單 TASK-0590～0599）：「接著開task造一艘新船吧 可以嘗試用西班牙大帆船的船型做參考(可以找真實圖紙&參數等資訊) 由妳重新設計圖紙打造一艘專屬於妳的船吧(自由發揮) 另外要是遊戲用的規格」。
範圍（遊戲用）：外部完整；內部只做甲板、艙口、梯子、彈藥庫這些遊戲用得到的大致構造。造船規格見 Senate `Docs/Workflows/Sculpture_Shipbuilding.md`。

## 座標約定
- 空間 800×320×640；X 船長（船頭 +X）、Y 船寬（**中線 ＝ 第 160 格**，鏡像 y ↔ 320 − y）、Z 高度（z 0 ＝ 龍骨底面）；P ＝ y < 160。
- 「在不在船裡」：|y − 160| ≤ 半寬（格心判斷）⇒ 兩舷逐格對稱。
- 0.1 m／格（書卡 meters_per_voxel 已記）。1 codo de ribera ＝ 0.57468 m ＝ 5.7468 格。

## 設計方向（開工時的決定）
- 船名「收穫號」：死神的鐮刀原本是農具 —— Memento Mori → Vivere → Harvest。船首像、船尾雕飾、船名板是本船自己的（TASK-0594）。
- 船型：**1618 年 Ordenanza 的 manga 21 codos（946½ toneladas）**，兩層砲甲板（主甲板＋puente）＋三座船樓（toldilla、alcázar、castillo）＋espolón。不描任何一張圖：每個尺寸照法令的比例表與條文算，算不到的才是設計決定。
- 線形的程式結構參考 gura 的三叉戟號（`gura-tridente-01m/design/hull_lines.py`：船中剖面 × 長度方向收縮）；剖面、兩端、舷頂換成 galleon 的（平底＋astilla、大圓弧艏柱、平的 espejo、法令的 tumblehome 規則）。`design/tools/wio.py`、`stamp_lists.py` 照抄三叉戟號（檔頭註明）。
- 沿用現成零件當模型：砲（18l／12l／6l）、舵輪、火藥桶、燈、羅經櫃、絞盤、小艇（`work sub=components`）。

## 階段一 新圖紙 01／02（2026-10-15，TASK-0590）
查證：兩個獨立研究 agent 並排 ⇒ `references/research_ordenanzas_2026-10-15.md`（法令比例表、Palacio、Cano）、`references/research_galleons_2026-10-15.md`（實船與複製船：Andalucía、San José、Atocha、Manila galleons、Red Bay）。互相不同意的照列（codo 0.57468／0.57864／0.557；San José 的 codo 0.418 vs 0.5747；Andalucía 長 48／49／50／51 m）。主要出處兩份都逐頁讀過的是 Fernández-González 2009（UPM）。

設計 `design/plan.json`（每個數字的 `src`：參考資料附出處／設計決定）；程式：
- `lines.py`：線形 ⇒ 每個 (x, z) 的半寬。
- `draft_lines.py` ⇒ `sheet01_lines_v1.png`（側面、半寬、橫剖面、主尺寸）、`verify_lines.json`、`masks/hull/hull_01..02.vox.txt`（船殼清單，at 0,0,0）。船殼 ＝ 線形實心往裡留 4 格牆（外板 1、肋骨 141 ×2、內板 177）；外板水線 z 52 以下灰白 182、以上黑 36（塗裝在階段三）。舷頂以上多算 EXTRA ＝ 60 層再切（階段二的坑，見下）。
- `layout.py`＋`draft_layout.py` ⇒ `sheet02_layout_v1.png`（甲板、砲門、桅、帆桁、帆、俯視）、`verify_layout.json`。

| 項目 | 讀數 | 1618 年 Ordenanza（21 codos） |
|---|---|---|
| 甲板長（主甲板 z 65，艏柱到艉柱） | 37.92 m（379.2 格） | eslora 66 codos ＝ 37.93 m |
| 龍骨 | 29.30 m | quilla 51 codos ＝ 29.31 m |
| 最大寬（含外板） | 12.10 m（121 格） | manga 21 codos ＝ 12.07 m |
| 比例 甲板長／寬、龍骨／寬 | 3.13、2.42 | 3.14、2.43（研究者照表算的） |
| mura（艏柱往後 L/4＋1 codo）的寬 | 115 格 | manga − 1 codo ＝ 115.3（art.21） |
| cuadra（艉柱往前 L/4＋2 codos）的寬 | 111 格 | manga − 2 codos ＝ 109.5（art.21）—— 寬只能是奇數格，111 是最近的 |
| hold beams（z 45）／puente（z 85）那一層的寬 | 119／119 | 兩者相等（art.22 的 tumblehome 規則） |
| 設計水線 | z 52（5.2 m） | 法令沒給（設計決定；Atocha 4.3 m） |
| 排水量（水線下實心 × 1.025） | 1,130 t | 946½ toneladas 是容積噸，不是排水量（只當量級） |
| 船殼牆 | 426,821 格；1 元件、空腔 0、鏡像差 0（第一版 428,046，階段二修掉船樓前後緣 1,225 格） | — |

- 甲板（甲板面 z）：底艙 orlop 45（只 x 190–430）、主甲板 65、puente 85、alcázar 102（到 x 268）、toldilla 119（到 x 196）、castillo 102（從 x 422）。主甲板與 puente 有舷弧（aft 6、fwd 3 格，FG）；船樓平的（art.16）。
  ⚠ 甲板間距 20 格（1589 年 galleon 3½ codos）而不是 1618 年的 3 codos（17 格）—— 遊戲裡站人要頭頂 14 格空，17 扣掉甲板板和橫樑不夠。船樓照 1618 的 17 格。
- 砲門（art.42：下緣在甲板上 1 codo、1¼ codos 見方）：主甲板每舷 9（18l）、puente 8（12l）、alcázar 2、castillo 2（6l）＋船尾追擊 2（18l）＝ **44 門**。間距 27–28 格；puente 的砲門頂到船腰舷頂留 2 格（船腰舷牆拉到 z 100）。
- 桅（art.66–68：主桅腳在龍骨中點 x 296、前桅腳在艏柱 rake 中點 x 472）：fore 29.6＋14.8 m、main 30.2＋15.1 m（Cano 2½ manga、上桅 ½）、mizzen 18.4 m＋lateen 24.5 m、bonaventure 13.8 m＋lateen 17 m、bowsprit 23.7 m @ 32°（Palacio）。主桅頂離水線 38.6 m（Andalucía 複製船 air draft 37 m，只當量級對照）。⚠ 桅帆比例只讀到 MP 部落格的轉述（二手，沒對過 Cano／Palacio 原文）；1618 年 art.72–91 的桅帆條文兩個 agent 都沒拿到。
- espolón：art.45 manga 的 3/5 ＝ 7.24 m 伸出艏柱（圖上只畫外框，TASK-0594 做）。

讀數與反向對照：
- `draft_lines.py --probe=half_beam=3` ⇒ 最大寬 121 → 127（每舷 +3）；站位表 33 格中 19 格 +3、12 格 +2、各 1 格 +1／0（＋2 以下的都在兩頭：長度方向收縮 × 3 再取整）。
- `draft_layout.py --probe=port=main:5:+3` ⇒ 主甲板間距 [28, 27, 28, 27, 28, 28, 27, 28] → [28, 27, 28, **30, 25**, 28, 27, 28]。
- 產生程式重跑：6 個輸出檔（兩份清單、兩張圖、兩份 verify）逐位元組相同。

⚠ 已知、之後的階段處理：
- 艏柱 z 57.5 以上是直的，船頭面是一整片平的到舷頂（x 500）—— espolón、船首像、castillo 前緣的裝飾在 TASK-0594。
- 船尾是一整片平的 espejo（照艉柱的 23.8° 往後倒）—— 船尾窗、galleries（art.69：最多伸出 ⅔ codo）在 TASK-0592／0594。
- bonaventure 的 lateen 帆桁照「吊點在 40%」畫，後端伸出船尾約 8 m —— 桅與帆桁階段（TASK-0595）要調（吊點改到中間，或船尾加 outrigger）。
- 三角帆（lateen）在遊戲裡怎麼轉、`sail=` 用哪一種，TASK-0595 先跟 ame 對。

## 階段二 船殼落格（2026-10-15，TASK-0591）
- 標記 `船殼:begin`（upto=start）→ `design/tools/stamp_lists.py calli-cosecha-01m 0 masks/hull/hull_01..02.vox.txt`（2 刀：250,000 ＋ 178,046，每刀讀回 placed ＝ 清單格數）→ `船殼:end`。
- 🩸 渲出來第一眼：**船樓前後緣（toldilla／alcázar、alcázar／船腰、船腰／castillo）的舷頂各多一條橫跨船寬的橫桿**。成因：`draft_lines` 算牆用「離船外的距離 ≤ 4」，舷頂以上只多算 12 層 ⇒ 船腰上方 z 112 起就是「船外」，船樓內側離它不到 4 格的那一條被當成牆。各自的讀數（元件 1、空腔 0、鏡像 0）全綠 —— 橫桿兩頭接在舷牆上，是一塊合法的實心。
  修法：舷頂以上多算 EXTRA ＝ 60 層（> 船樓與船腰最大落差 33）⇒ 新清單是舊清單的子集（新有舊沒有 0 行；舊有新沒有 1,225 行，全在 x 195／196、267／268、421／422）。刻：`masks/hull_fix/carve_breaks.vox.txt`（carvevox 帶刻之前的顏色守門，carved 1,225）→ 標記 `船殼修正`。
- **結果帳**（`design/tools/check_hull.py`：作品那側從 `export format=list links=none mark=船殼修正` 讀）：作品 426,821 ＝ 設計 426,821，缺 0、多 0、色差 0。
- **結構**（引擎 `stats structure=1 mirror=y:160`）：1 元件、封閉空腔 0、鏡像差 0／0／0。
- **線形對照**：右舷外緣（每個 (x, z) 最大的 dy）vs `lines.hb` 取 floor，x 100..480 每 20、z 4..129 每 5，412 點、差 0。**反向對照**：設計那一站（x 300）+3 ⇒ 報 20 點（那一站每個高度）、最大差 3。
- **組裝件** `calli-cosecha-01m-assembly`「收穫號」：0.1 m、800×320×640（parent 船殼，沒標 sub ＝ 主作品）；關聯 `船殼` at 0,0,0、meta `kind=ship, waterline_z=52`。船殼標 `tags=sub`、名稱「收穫號 船殼」。
- 產生程式重跑（EXTRA 60 之後）：清單、verify、圖逐位元組相同。
- 過程圖：`overlays/stage2_hull_{bowq,sternq,side}.png`（yaw 30／150／90）。
- ⚠ 看得到的：船殼一整片黑（帶子、砲門在階段三）；船頭是平的圓頭到舷頂（espolón 在階段五）；艙裡是空的（甲板在階段四）。

## 階段三 砲門、塗裝、船尾窗（2026-10-15，TASK-0592）
設計 plan.json `paint`、`stern`；產生 `design/draft_ports.py`（船殼照 draft_lines.hull_volume ＝ 作品，階段二證過；結構照三叉戟號的 draft_ports）⇒ `masks/ports/carve.vox.txt`（8,633，帶刻之前的顏色守門）、`masks/ports/paint.vox.txt`（19,278，換色）、`verify_ports.json`、`sheet03_ports_paint_v1.png`。
- 砲門 ＝ `layout.ports`（每舷 9／8／2／2，兩舷同一組 x）：開口 (x, z) 範圍裡、那一舷 |dy| ≥ 6 的牆全刻；外擴 1 格那一圈牆漆玫瑰粉 242（reveal）。
- 塗裝（只換外板那一層的黑 36；水線下灰白不動）：
  - **wale 三條**（art.52：主甲板下 1 codo、主甲板上 2½ codos；puente 上 14 格比照）：玫瑰粉 2 列＋上下各一列金 248，照甲板舷弧走。
  - **船樓菱格**：toldilla（z 121–131）、alcázar 與 castillo（z 107–114／115）舷牆外面玫瑰粉菱形配黑底（週期 10、半徑 3，只照 x、z 算 ⇒ 兩舷對稱），上下金邊。
  - 舷頂最上一格金。
- 船尾 espejo（每個 (y, z) 從最後面往前那一段牆）：puente 5 扇、alcázar 5 扇、toldilla 3 扇窗（寬 5、刻最外一格、第二格玻璃 87、外一圈金框）；主甲板兩個追擊砲門（寬 7，整段牆刻穿）。窗寬一律奇數、對稱取整。
- 🩸 v1 每層砲列一整條 11 格的帶子（三叉戟號的作法）⇒ 舷側一半是粉的，不像 galleon；改成 wale 細帶＋砲門框。
- 🩸 wale 漏漆讀數（wale 高度裡外板還是黑的）兩次不是 0：① puente 的 wale 照舷弧在兩頭抬到 z 105，被從 z 104 起的船樓菱格蓋黑（184 格）⇒ 菱格改從 z 107 起；② 舷弧拋物線過了 x 120 還外推，最船尾 x 105–112 的 wale 抬到 z 107（16 格）⇒ `layout.deck_z` 的舷弧在 x 120／500 夾住（甲板範圍都在 x ≥ 113，主甲板與 puente 那一段 deck_z 變了；砲門 x ≥ 168 不受影響，verify_layout 重產）。
- 落格：`砲門:begin` → carvevox（顏色守門，carved 8,633）→ stampvox overwrite=1（placed 19,278）→ `砲門:end`。

讀數（`design/tools/check_stage3.py`，作品從 export 讀）：
- **結果帳**：作品 418,188 ＝ 設計（船殼 − 刻 ＋ 換色），缺 0、多 0、色差 0。
- 42 個舷側砲門開口（兩舷）：**從作品的格子量**，開口裡還有實心的 0 個；船尾兩個追擊砲門：船尾面那一段牆 0 格。
  **正向對照**（同一把尺量刻之前的 `船殼修正`）⇒ 42 個全報（每個 196 格）、追擊砲門各 49 —— 尺會說話。
  **反向對照**：`draft_ports.py --probe=skip_port=puente:4` ⇒ 只報 puente 第 4 個（兩舷各 196 格）。
- wale 漏漆 0；引擎 stats：1 元件、空腔 0、鏡像差 0。
- 換色：玫瑰粉 11,741、金 7,122、玻璃 415；刻掉：外板 2,467、肋骨 4,114、內板 2,052。
- 產生程式重跑：8 個輸出檔（船殼清單、砲門清單、verify、圖）逐位元組相同。
- 過程圖：`overlays/stage3_sheet.png`、`overlays/stage3_ports_{bowq,sternq,side,astern}.png`。
- ⚠ 看得到的：船尾四分之三那個角上，wale 與菱格在圓弧的船尾肩膀上從船尾看成一條一條直的粉色細線（像滴下來的漆）—— 先放著，船尾 galleries（TASK-0594）會蓋住那一段；艙裡沒甲板 ⇒ 從砲門看得到對面的牆。

## 階段四 甲板、船樓、艙口、梯子（2026-10-15，TASK-0593）
設計 plan.json `decks_build`；產生 `design/draft_decks.py`（結構照三叉戟號：甲板板＋橫樑＋圍欄、梯子踏板與 stringer、組起來找封閉空腔）⇒ `masks/decks/<層>.vox.txt`、`masks/ladders/<上面那層>.vox.txt`、`ladder_points.json`、`verify_decks.json`、`sheet04_decks_v1.png`；落格 `design/tools/build_decks.py`。
- 甲板（甲板面 z；主甲板與 puente 有舷弧）：底艙 orlop 45（只 x 190–430）、主甲板 65、puente 85、alcázar 102（x ≤ 268）、toldilla 119（x ≤ 196）、castillo 102（x ≥ 422）。艙裡的甲板板 177、露天的（puente、三座船樓）209；橫樑每 16 格、寬 2、深 3（船樓 2）136；圍欄與 break 141。
- 開口：艙口三個疊在中線（後 214–226、主 312–332、前 395–409，orlop／主甲板／puente 都開）＋圍欄 2 格；梯子井；桅孔照桅的傾斜軸線（r：前、主 4、後 3、bonaventure 2.5；桅腳立在那一層 ⇒ 不開）。
- **break**（1618 art.5）：alcázar 前緣 x 268、toldilla 前緣 x 196、castillo 後緣 x 422 —— 一道艙壁（從下一層甲板到船樓甲板，兩扇門 寬 5 高 15）＋船樓甲板邊上一道 7 格高的胸牆（梯子頭留口）；放在船樓那一層的子作品裡。
- 梯子 9 座（每 3 格一階、每階 2 格、踏板 7 寬）：艙裡 3 座（orlop→主甲板 x 270、主甲板→puente 後 x 262／前 x 372，在上一層開井）；船樓 6 座（puente→alcázar、alcázar→toldilla、puente→castillo 各兩舷），靠在 break 外面、頭踩上船樓甲板。每一層要讓人走得到的甲板都有梯子（reach：orlop 1、主甲板 3、puente 6、alcázar 4、toldilla 2、castillo 2）。
- 子作品（parent 船殼、tags sub、0.1 m、800×320×640、at 0,0,0）：`-deck-{orlop,main,puente,alcazar,toldilla,castillo}`、`-ladders-{main,puente,alcazar,toldilla,castillo}`；梯子掛在它上面那一層甲板裡（關聯 `梯子`，meta `kind=ladders`），固定點 `<梯名>.foot／lo／hi／head`。組裝件關聯 `甲板-<層>`。
- **甲板 meta**（§9.3）：每層甲板子作品 `export format=vxk links=none` ⇒ `Blockside/src/decks.py` ⇒ `design/decks_meta.tsv`（name 換成 plan 的中文名）⇒ `work sub=meta`：kind=deck、deck、level 0–5、name、floor、thick（艙裡 4、船樓 3）。
  🩸 第一次匯出沒帶 `links=none` ⇒ 甲板子作品把關聯的梯子一起匯出，三座船樓的 floor 多了往下走的尾巴（alcázar 271–279 從 z 103 降到 92 ＝ 梯子踏板）。遊戲照 floor 判斷梯子接哪一層 —— 這條尾巴會讓 puente 的梯子腳被判到 alcázar。
- 預覽 preset（組裝件）：`藏船殼`、`只看主甲板以下`。
- 🩸 設計時抓到的兩個：① orlop 梯子的 lo 點頭頂 14 格碰到主甲板的橫樑（梯子井從第 4 格才開）⇒ 井從第 2 格開；② 主甲板多開了後桅的孔 —— 拿「整層甲板最高的 z」跟桅腳比，主甲板船尾舷弧抬到 71 > 後桅腳 67 ⇒ 改拿桅那一格的甲板高度。

讀數：
- 設計那一側：重疊（船殼／彼此）0、砲門往艙裡 20 格內被甲板／樑／艙壁擋到的 0、梯子點問題 0、封閉空腔 0、每件鏡像差 0。
- **結果帳**（`design/tools/check_decks.py`，每件從匯出讀）：11 件、168,839 格，缺 0、多 0、色差 0；跟船殼重疊 0、彼此重疊 0。
- **組起來**（引擎 `stats structure=1 mirror=y:160`，組裝件）：587,027 格、1 元件、空腔 0、鏡像差 0。
- **梯子點**（組裝件 `export format=parts`，遊戲讀的那一份）：9 座、36／36 點、跟設計差 0；每個點那一格是空的、腳下實心、頭頂 14 格空。
  **尺的反向對照**：把設計的 main-fwd.head 偏 3 格 ⇒ 報「跟設計差 1」、腳下不是實心（設計檔已還原，雜湊對過）。
  **反向對照**：`draft_decks.py --probe=drop_ladder=castillo-S` ⇒ 8 座、castillo 只剩 castillo-P。
- 產生程式重跑：14 個輸出檔逐位元組相同。
- 過程圖：`overlays/stage4_sheet.png`、`overlays/stage4_decks_{nohull,bowq,sternq}.png`。
- ⚠ 還沒做：船樓的艙房（遊戲空艙房 §9.2，之後要配功能艙可以加）；彈藥庫（TASK-0598，orlop 上）。

## 階段五 船首喙、船首像、船尾裝飾與燈（2026-10-15，TASK-0594）
設計 plan.json `espolon`、`figurehead`、`stern_deco`；產生 `design/draft_deco.py`（讀組裝件現在的格子 ⇒ 船殼＋甲板＋梯子，佔用與貼面都照它算）⇒ `masks/deco/<部件>.vox.txt`、`verify_deco.json`、`sheet05_deco_v1.png`；落格 `design/tools/build_deco.py`，之後的修正 `design/tools/delta_apply.py`（作品對清單：多的帶顏色守門刻、少的貼、顏色不同的換）。
- **船首喙**（`-espolon`，關聯 `船首喙`）：1618 art.45 manga 3/5 ＝ 72 格伸出艏柱（x 501–572）；甲板頂 z 73、3 格厚、半寬 24 收到 2；兩舷 head rail（4 格高、每 6 格一根柱、金頂條，停在船首像前面）；下面一片 cutwater（5 格寬、沿前緣 10 格的帶子，從 z 20 的艏柱掃到喙尖，前緣內側一條玫瑰粉線）。
  喙放在 z 73 是因為**艏斜桅**：它從主甲板（x 486, z 69）以 32° 往前上，x 500 中心 z 77.7、x 510 到 z 84 —— 喙放更高會被它穿過。讀數：艏斜桅那條線半徑 3 內的裝飾格 0。
- **船首像**（`-figurehead`，關聯 `船首像`）：死神見習生 —— 黑斗篷（下襬玫瑰粉）、兜帽裡蒼白的臉、兜帽兩側垂下粉髮、袖子握著立在中線的鐮刀（柄 132、刀刃 219 往前往下彎、柄頂一點金）；站在喙尖。鐮刀在中線 ⇒ 兩舷對稱。
- **船尾裝飾**（`-stern-deco`，關聯 `船尾裝飾`）：船尾陽台（puente 船長室那排窗下、伸出 espejo 5 格、半寬 26、玫瑰粉欄杆金扶手、每 8 格一個托架）＋兩舷 quarter galleries（x 102–140、z 86–118、伸出 4 格 ＝ art.69 的 ⅔ codo；兩排窗、玫瑰粉腰帶、上面一個收進去的頂）＋**三盞船尾燈**（外部模型，沿用 `gura-tridente-01m-lantern`，scale 0.5、meta `kind=light`，站在 toldilla 船尾舷頂 z 134、y 142.5／160.5／178.5）。
  ⚠ galleries 兩舷是一件裡一起產的（照 |dy| 算 ⇒ 對稱），不是造船規格 §2「一舷＋mirror=y 關聯」的做法 —— 它是貼著船殼曲面長的，一舷＋鏡像要另外處理 at 的換算，這件不值得；鏡像差照樣量（0）。
- **船名板**（`-name-board`，關聯 `船名板`）：espejo、alcázar 那排窗上面（z 113–119）、比 espejo 往外一格；3×5 字型「LA COSECHA」金字黑底玫瑰粉框；從船尾看左手 ＝ −y ⇒ 第一個字在 y 最小那邊。字不對稱 ⇒ **這一件的鏡像差 29 對照實報**。
- 裝飾不蓋船的格：落在船殼／甲板／梯子上的不放、照實數（stern-deco 10 格：gallery 的頂在船尾肩膀上用 z 118 那一層的外緣，碰到更上面的船殼）。

🩸 這一階段的坑：
- 設計一開始讀到的組裝件是**空的**：抄來的 `wio.export_list` 固定帶 `links=none`，組裝件自己沒有格子 ⇒ 加 `links` 參數（預設照舊 none）。
- 落過一次之後重產，設計讀的組裝件**已經含舊裝飾** ⇒ 把舊裝飾當成船、新的被大量跳過（喙 5,526 格被跳過）、galleries 往外長 ⇒ 設計那一側扣掉本階段自己的四件。
- 組起來 **28 個元件**（27 小塊共 109 格浮空）：head rail 頂條沿著越收越窄的寬度只在斜角相接、柱子之間一段段浮空；船首像的手、柄、刀刃也只在斜角相接 ⇒ 頂條在寬度變的地方補台階、袖子一塊、柄從甲板面起、刀刃逐段往上補。（第一次補台階的 range 差一格是空的，又多跑一輪。）
- `delta_apply.py` 用 heredoc 寫 ⇒ 反斜線被吃掉、語法錯（我記過的坑，又踩一次）⇒ 用 Edit 工具修。

讀數：
- **結果帳**（`design/tools/check_stage5.py`，每件從匯出讀）：船首喙 7,961、船首像 734、船尾裝飾 9,754、船名板 287，缺 0、多 0、色差 0。
- **組起來**（引擎 stats，組裝件）：605,763 格、**1 元件**、空腔 0；鏡像差 29 對（全是船名板的字）—— `hide_links=船名板` ⇒ 0。
- 跟船（船殼＋甲板＋梯子）重疊 0、部件之間重疊 0；艏斜桅那條線被擋 0；三盞燈腳下實心、models_broken 0。
- **反向對照**：`draft_deco.py --probe=shift=figurehead:3` ⇒ 船首像鏡像差 0 → 668。
- 產生程式重跑：6 個輸出檔逐位元組相同。
- 過程圖：`overlays/stage5_{sheet,full,bow,stern}.png`（bow 那張用 region 框，模型不跟著 region 裁 ⇒ 左上角的三盞燈是船尾的，不是浮在那裡）。
- 階段三的「船尾肩膀滴漆」：galleries 蓋住了那一段（stage5_stern.png）。

## 階段六 桅與帆桁（2026-10-15，TASK-0595）
設計 plan.json `rig_build`（桅帆尺寸與位置在 `masts`）；產生 `design/draft_masts.py`（讀組裝件現在的格子、扣掉本階段自己的件）⇒ `masks/masts/<桅>.vox.txt`、`masks/yards/lateen-<桅>.vox.txt`＋`yards_lateen.json`、`masks/bowsprit_hole/carve.vox.txt`、`yards_placement.json`、`verify_masts.json`、`sheet06_masts_v1.png`；落格 `design/tools/build_masts.py`。
- **桅**（每根一件子作品，關聯 `前桅`／`主桅`／`後桅`／`bonaventure`）：下桅（半徑 3.5→2.5；後桅 2.5→1.8；bonaventure 2→1.4，都比甲板桅孔小、用同一個圓的判斷式）＋**cofa**（圓的桅樓籃子：主 r 19（Palacio：上緣周長 ＝ manga，⚠ 二手）、前 r 15、後 r 9；地板 2 格、籃子 6 格高、玫瑰粉腰帶、金頂）＋上桅（前、主；半徑 2.5→1.5、頂一格金）。桅照 plan 的傾斜軸線（前 −3°、主 1°、後 3°、bonaventure 4°）。
  前桅腳插進船頭 deadwood 的那 112 格是船殼 ⇒ 不放（桅坐在船殼上）。
- **bonaventure 往前挪到 x 140**（v0 x 120）：桅腳往上 z 72–79 那一段落在船尾 espejo 的牆裡（被船殼擋 74 格）。甲板的桅孔照差量重開（puente／alcázar／toldilla 各刻補約 20 格，`delta_apply.py`）；lateen 後端伸出船尾從 4.55 m 降到 2.55 m。
- **艏斜桅**（`-bowsprit`，關聯 `艏斜桅`）：主甲板 (486, 69) 起 32°、23.7 m、半徑 3→2；**船頭牆開孔** 180 格（船殼 carvevox 帶顏色守門，標記 `艏斜桅孔`），孔整個由艏斜桅填滿。
  🩸 v1 牆裡那段當成船殼跳過 ⇒ 艏斜桅在牆裡斷開、牆外那段 4,273 格浮空（組起來 2 個元件）；v2 孔比桿大半格 ⇒ 牆裡 10 個小空腔（16 格）；v3 孔整個填滿 ⇒ 1 元件、空腔 0。設計那一側讀開孔之前的船殼（`砲門:end`），重產時孔的清單才不會變空。
- **方帆桁 5 根**（外部模型、放在各自的桅子作品裡）—— 沿用憲法號的帆桁元件，只沿長度（y）縮放到本船的長度（造船規格 §2.1）：

| 帆桁 | 長 | 來源（憲法號） | scale y | brace |
|---|---|---|---|---|
| fore course | 21.7 m | yard-fore-course（24.9） | 0.8715 | −15° |
| fore topsail | 9.7 m | yard-main-royal（9.3） | 1.043 | −17° |
| main course | 27.2 m | yard-main-course（29.1） | 0.9347 | −15° |
| main topsail | 12.1 m | yard-main-topgallant（14.3） | 0.8462 | −17° |
| spritsail | 14.5 m | yard-spritsail（18.5） | 0.7838 | 0 |

  meta `kind=yard、mast、yard、sail（帆名，階段七用）、length_m、pivot_anchor=pivot、turn_axis=z、rotate_z_deg`。吊點在桅軸前面（桅半徑 ＋3.5）；spritsail 在艏斜桅 85% 處、往下 5 格。
- **lateen 帆桁 2 根**（新做的子作品 `-yard-mizzen-lateen`、`-yard-bonaventure-lateen`；沒有現成的）：斜桿，前端低、後端高；後桅 24.5 m／40°／吊點在前端往後 40%；bonaventure 17 m／45°／45%。固定點 pivot、sling、fore、peak、jackstay-NN（每 8 格）。模型 rotate 0（水平投影沿船長），放在桅的左舷側（y − (桅半徑＋2.5)），不穿過桅。meta `yard=gaff`、`rig=lateen`。
  **遊戲怎麼轉**：讀 `Blockside/src/js/30_rig_physics.js` 的 braceYards —— `yard` 是 gaff／boom 的照縱帆往下風擺（8°–80°），其他當方帆桁；所以 lateen 標 `yard=gaff`。已在酒館問 ame（seq 24767），**她還沒回**。⚠ 擺動時前端會掃向主桅那一側（後桅帆桁前端 x 271、主桅 x 296）。

讀數：
- **結果帳**（`design/tools/check_stage6.py`，每件從匯出讀）：前桅 11,932、主桅 13,264、後桅 3,597、bonaventure 1,229、艏斜桅 4,766、lateen 1,620／1,096，缺 0、多 0、色差 0；船殼 ＝ 砲門:end − 艏斜桅孔 180 ＝ 418,008，缺 0、多 0、色差 0；四層甲板（桅孔搬位）缺 0、多 0、色差 0。
- 帆桁模型 7 根：meta 齊全、來源固定點齊全；models_broken 0（五件桅子作品）。
- **組起來**（引擎 stats，`hide_links=船名板`）：640,084 格、1 元件、空腔 0、鏡像差 0。
- **帆桁穿船**：沿線每 0.5 格取樣、半徑約 1 內有實心（離自己吊點 7 格內不算）⇒ 7 根全 0。**反向對照**：`--probe=pivot=yard-main-course:-200`（往下放到船殼的高度）⇒ 只有那一根報 34 格。
- 作品裡每根帆桁模型的 at／pivot／rotate／scale ＝ 設計（yards_placement.json）：7 根 0 差。**反向對照**：暫時把設計的 yard-main-course at.z −3 ⇒ 只報那一根（作品 274.84 ≠ 設計 271.84）；設計檔已還原、雜湊對過。
- lateen 後端伸出船尾：後桅 0.65 m、bonaventure 2.55 m。
- 梯子點（組裝件 parts）照樣 36／36、0 問題（甲板桅孔搬位之後重量）。
- 產生程式重跑：18 個輸出檔逐位元組相同。
- 過程圖：`overlays/stage6_{sheet,full,side,sternq}.png`。

## 階段七 索具與帆（2026-10-15，TASK-0596）
設計 plan.json `rigging`；產生 `design/draft_rigging.py`（結構參考三叉戟號 draft_rigging）⇒ `masks/rigging/channels.vox.txt`、`rigging_plan.json`、`textures/{ensign,cross_course}.png`、`verify_rigging.json`；套用 `design/tools/rigging_apply.py`。
- **channels**（`-channels`，關聯 `支索板`，兩舷一件、照 |dy| 算 ⇒ 對稱）：每根桅一塊 4 格寬的板、舷頂下 3 格，外緣一排 deadeye（3 格高）；2,164 格、跟船重疊 0。每舷 shrouds 前 5、主 6、後 3、bonaventure 2，前／主各加 1 條 topmast backstay。
- **固定點 113**：桅上 hound／stay-head／futtock／tm-hound／tm-stay-head／cofa 邊（rim、rim-low）／top-aft；stay 下端（前桅 castillo 上、主桅 puente 上、後桅 alcázar 上）；艏斜桅 forestay-foot／cap-top／side／bob；船首喙 cutwater 上的 bobstay 腳；船殼舷頂的 belay；puente／toldilla 甲板上的 lateen tack。cofa 邊那 26 個點落在籃子的實心上 —— 就是要綁在那裡。
- **繩 368 條**：shrouds 32、topmast shrouds 12、futtock 12、backstays 4、stays 6、艏斜桅 4、ratlines 278（下 190、上 88，子繩）、sheets 14、tacks 6。色、粗、slack 照造船規格 §6。
- **帆 9 面**：fore／main course（很深、帆腳在舷頂上 5 格；**畫勃艮第十字**）＋ topsail（sheet 綁下一根帆桁同舷 earing）、spritsail（sheet 往後綁船首樓舷頂）、mizzen／bonaventure lateen（前緣沿帆桁 fore → peak、clew 自由、兩舷 sheet 綁船尾舷頂、tack 從帆桁前端綁甲板）、ensign（**勃艮第十字**，掛在 bonaventure 帆桁後端）、pennant（主桅頂、玫瑰粉）。預設風 4.5,−1.5,0、3 秒。
- **meta**（§9.1）：帆 9（course、topsail、spritsail、gaff ×2、flag ×2）、帆自己的繩 20（sheet／tack ＋ sail ＝ 帆名）。lateen 標 `sail=gaff`（遊戲預設戰鬥帆才開）；spritsail 標 `sail=spritsail`（遊戲不認得的帆種照滿帆，31_sailing.js）。

讀數（`design/tools/check_stage7.py`，從作品／CLI 讀）：
- channels 結果帳 2,164 ＝ 2,164，缺 0、多 0、色差 0。
- CLI：繩 368、**ropes_broken 0**；帆 9、**sails_broken 0**。
- meta（從作品讀回）：帆 9／9、帆自己的繩 20／20、sail 標錯 0；帆桁 meta 的 sail 都是某一面帆的名字（7／7）。
- **反向對照**：check 讀完作品之後當作 `main-course.sheet-S` 沒標 ⇒ 只報那一條；`draft_rigging.py --probe=nometa=fore-topsail.sheet-P` ⇒ 只報那一條。
- 組起來（hide_links=船名板）：642,240 格、1 元件、空腔 0、鏡像差 0。
- 產生程式重跑：5 個輸出檔逐位元組相同。
- 過程圖：`overlays/stage7_{full,side,sternq}.png`、`overlays/stage7_ensign_texture.png`。
- ⚠ lateen 的標法 ame 還沒回（酒館 seq 24767）；她要別的就改帆桁與帆的 meta（不動格子）。
