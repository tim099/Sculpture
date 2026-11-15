# 威尼斯貢多拉 gondola（約 1666，敞艙載客船，TASK-1298）

- 作者：`apex-one`
- 主作品：`apex-one-venice-gondola-1666`（`220×70×50`，`0.05 m/voxel`）
- 子作品：
  - `apex-one-venice-gondola-1666-hull`（敞艙船殼與木作：`14,752` voxels）
  - `apex-one-venice-gondola-1666-ferro`（17 世紀艏艉彎鐵與 1624 規制鈍齒 *brocche*：`148` voxels，`material=iron`）
  - `apex-one-venice-gondola-1666-oar`（`12×88×12`，`4.20 m` 站姿單槳 *remo*，`tags=sub,component`，`284` voxels，`kind=oar,rowers=1,side=S,stroke_deg=28,dip_deg=10`）
  - `apex-one-venice-gondola-show-1666`（城內演出用 `0.10 m/voxel` 含站姿船伕與 2 名乘客，`112×48×32`，`4,420` voxels + `oar-S` `@0.5x`）

## 實測規格（`0.05 m/voxel`）
- 軸向與原點：`+X` 船首（*prua*）、`+Y` 右舷（中線 `y = 34.5`）、`+Z` 朝上、`z = 0` 為龍骨底面。
- 全長 `LOA = 10.50 m`（210 格，`x = 5..214`）；設計水線 `z_wl = 4`（吃水 `0.20 m`），水線長 `LWL = 8.25 m`。
- 最大船寬 `B = 1.40 m`（28 格，`y = 21..48`），平底 *fondo* 寬 `0.90 m`，舯乾舷 `+0.30 m`。
- 艏鐵 *ferro di prua* 最高點離龍骨 `1.25 m`（**水線上 `+1.05 m`**），艉鐵 *ferro di poppa* 最高點離龍骨 `1.05 m`（**水線上 `+0.85 m`**）。
- 艉部劃手站台 *poppa* 踏板表面離龍骨 `0.55 m`（**水線上 `+0.35 m`**）；右舷 *forcola* 樞軸 `(48.5, 43.5, 16.5)`（**水線上 `+0.625 m`**）。
- 站姿長槳 *remo* 全長 `4.20 m`（舷內 `1.35 m`、舷外 `2.85 m`，中位姿態 `rotate = -36, 0, 58°`，框 `(9.2,31.1,-17.1)–(68.4,69.2,33.1)`，右舷延伸極限距中線 `+1.735 m` ⇒ 活躍掃掠總寬 `2.435 m`）。
- 拓樸驗算：`stats structure=1` ⇒ `14,900` voxels、`1` 個 6 連通元件、`0` 個封閉空腔、`0` 覆蓋重疊。

## 城內演出版規格與掃掠包絡（步驟 3，`0.10 m/voxel`）
- 作品：`apex-one-venice-gondola-show-1666`（`112×48×32`、`4,420` voxels、`components = 1`、`cavities = 0`），掛載 `oar-S`（`scale = 0.5`，`at = 25.0, 28.0, 8.5`，`94` 三角形）；並已設定 `work_meta`（`waterline_z = 2` @ `0.1 m`；主作 `waterline_z = 4` @ `0.05 m`）與匯出 `.vxk`。
- 水線與尺標：`LOA = 10.50 m`（`105` 格）、`B = 1.40 m`（`14` 格）、`z_wl = 0.20 m`、艉站台 *poppa* 頂面水線上 `+0.40 m`、艏鐵 `+1.00 m` WL、艉鐵 `+0.80 m` WL、座艙 2 名乘客帽頂 `+1.10 m` WL。
- 站姿高度：艉站台船伕頭頂至 `z = 22`（離龍骨 `2.30 m` ＝ **水線上 `+2.10 m`**）；過低橋半蹲姿態推定 **`+1.75 m` WL**。
- *remo* 長槳掃掠（依 `31_drive.js oarAnim`、`stroke_deg = ±28°`、`dip_deg = 10°`）：
  - 中位推送（`Rz = 58°`）：右舷最遠距中線 `+1.735 m` ⇒ **掃掠總寬 `2.44 m`**，槳葉吃水 **`-1.00 m` WL**（最低運河需求水深 `≥ 1.25 m`），手握端 **`+1.44 m` WL**。
  - 動態入水極限（`phi = 0`, `Rz = 30°`）：右舷最遠 `+2.518 m` ⇒ **峰值包絡寬 `3.22 m`**。
  - 收槳／回槳極限（`phi = 0.5`, `Rz = 86°`）：右舷僅 `+0.608 m` ⇒ **收槳通寬 `1.41–1.50 m`**。
- 橋孔淨空包絡（水線上）：
  - `[E1]` 動態划槳全掃掠：`2.10 m H × 3.22 m W`
  - `[E2]` 站姿穩態推槳：`2.10 m H × 2.44 m W`
  - `[E3]` 站姿收槳貼舷：`2.10 m H × 1.50 m W`
  - `[E4]` 半蹲收槳過橋：`1.75 m H × 1.50 m W`
  - `[E5]` 無人繫泊空船（艏鐵頂）：`1.05 m H × 1.40 m W`


## 威尼斯大運河與渡口場景驗證（步驟 4，`TASK-1291` 1666 威尼斯規劃實測）
- 測試基準：以 `TASK-1291`（`bs1291` 威尼斯 1666 運河與街橋資料）在隔離 worktree `bs1298` 產出 `venice_plan_1291.json`（`roads=3082`、`bridges=395`、`banks=662`、`piers=3`、`berths=9`），配合 `world/water/venice.js`（`228` 條運河、總長 `53,731.7 m`）及 `63_towns.js` `townBridgeForm` 實測算式。
- 運河通航（`228 / 228` 條全部通過）：
  - 水深 `2.50–5.00 m` vs 貢多拉吃水 `0.20 m` 與長槳最低葉尖 `-1.00 m` WL（最低需求 `≥ 1.25 m`）：**228 / 228（100%）合格**；小運河餘裕 `≥ 1.50 m`、大運河 `5.00 m`（餘裕 `+4.00 m`）。
  - 河寬 `6.00–70.00 m`（大運河 `Canal Grande` 長 `3,644.1 m`、寬 `41.3–70.0 m`），完全涵蓋單船動態滿划包絡 `[E1] 3.22 m` 與會車需求。
- 橋孔淨空（`395` 座橋，依最佳拱孔與實測寬高包絡）：
  - 站姿全程可過：**313 / 395（79.2%）** —— `[E1]` 全力掃掠（`2.10 m H × 3.22 m W`）`214` 座、`[E2]` 穩態推槳（`2.44 m W`）`82` 座、`[E3]` 站姿收槳貼舷（`1.50 m W`）`17` 座。
  - 低姿收槳可過（`[E4]` `1.75 m H × 1.50 m W`）：再增 `68` 座，合計 **381 / 395（96.5%）** 可通航；餘 `9` 座僅限無船伕空船（`[E5]`，拱頂 `1.45–1.70 m`）、`5` 座極窄 `2–3 m` 跨距小弄橋（拱頂 `0.70–1.20 m`）不可過。
  - 代表地標橋讀數：
    - **Ponte di Rialto (`p-ponte-di-rialto~br1`)**：現況 `1291` 預設 4 拱石拱橋（跨水 `43.0 m`、水深 `5.0 m`），中孔 `k=1, 2` 孔寬 `9.35 m`、拱頂 `+2.338 m` WL，`@ +2.10 m` 淨寬 `3.884 m` ⇒ **`[E1]` PASS**；待 `TASK-1291` 接上歷史單拱 `kit:"rialto"`（約 `28.8 m` 跨、`+7.3 m` 拱頂）亦大幅裕度通過。
    - **Ponte della Paglia (`p-ponte-della-paglia~br1`)**：`10.5 m` 單拱、拱頂 `+2.353 m`、`W@2.10 = 4.477 m` ⇒ **`[E1]` PASS**。
    - **Ponte del Traghetto (`p-ponte-del-traghetto~br1`)**：`8.5 m` 單拱、拱頂 `+2.400 m`、`W@2.10 = 3.894 m` ⇒ **`[E1]` PASS**。
    - **Ponte delle Guglie (`p-ponte-delle-guglie~br1`)**：`22.5 m` 2 拱、拱頂 `+2.199 m`、`W@2.10 = 2.933 m` ⇒ **`[E2]` PASS**。
    - **Ponte dei Tre Archi (`p-ponte-dei-tre-archi~br1`)**：`24.5 m` 2 拱、拱頂 `+2.027 m < 2.10 m`，需半蹲收槳（`W@1.75 = 5.462 m`）⇒ **`[E4]` PASS**。
- 停泊與渡口高差實測（船尾站台 *poppa* `+0.40 m` WL／舯舷緣 `+0.30 m` WL）：
  - **大運河渡口（Santa Maria del Giglio `cb-25`／San Samuele `cb-24`）**：石砌 *fondamenta* 寬 `5.0 m`、頂高 **`+0.75 m` WL**（鄰接街 `v-campo-del-traghetto` `+0.20–0.23 m`、水深 `5.0 m`），跨步高差僅 **`+0.35 m`**（至舯舷緣 `+0.45 m`），為最貼近實作單階登船高度之天然渡口泊位。
  - **San Marco Molo 海堤（`quay-1`）**：碼頭面高 **`+1.00 m` WL**（離 *poppa* `+0.60 m`），可供低舷岸停泊；大型棧橋 `pier-1 / pier-2` 高 `+1.40 m`（`+1.00 m` 高差，配大船用），且規劃報告 `berth-boat-1..4` 因與 `berth-small-5` 航道交會而被移出 ⇒ 貢多拉以運河堤岸渡口與 `quay-1` 為主。
  - **Rialto 兩岸石堤（`cb-38` 西 `+2.05 m`、`cb-13` 東 `+1.99 m`）** 與 **San Tomà (`cb-217` `+1.22 m`)**：屬高位廣場堤岸（離 *poppa* `+1.59–1.65 m`／`+0.82 m`），對應威尼斯階梯狀 *riva* 登船階。
- 產出驗證與截圖：
  - `design/metrics_step4.json`、`design/render_step4_venice.py`
  - `design/sheets/step4_rialto_pass.png`
  - `design/sheets/step4_traghetto_moor.png`
  - `design/sheets/sheet03_venice_scene_verify.png`