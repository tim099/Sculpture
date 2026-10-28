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
