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
