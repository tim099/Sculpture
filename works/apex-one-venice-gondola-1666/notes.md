# 威尼斯貢多拉 gondola（約 1666，敞艙載客船，TASK-1298）

- 作者：`apex-one`
- 主作品：`apex-one-venice-gondola-1666`（`220×70×50`，`0.05 m/voxel`）
- 子作品：
  - `apex-one-venice-gondola-1666-hull`（敞艙船殼與木作：`14,752` voxels）
  - `apex-one-venice-gondola-1666-ferro`（17 世紀艏艉彎鐵與 1624 規制鈍齒 *brocche*：`148` voxels，`material=iron`）
  - `apex-one-venice-gondola-1666-oar`（`12×88×12`，`4.20 m` 站姿單槳 *remo*，`tags=sub,component`，`284` voxels，`kind=oar,rowers=1,side=S,stroke_deg=28,dip_deg=10`）
  - `apex-one-venice-gondola-show-1666`（城內演出用 `0.10 m/voxel` 含船伕乘客版，步驟 3 補入）

## 實測規格（`0.05 m/voxel`）
- 軸向與原點：`+X` 船首（*prua*）、`+Y` 右舷（中線 `y = 34.5`）、`+Z` 朝上、`z = 0` 為龍骨底面。
- 全長 `LOA = 10.50 m`（210 格，`x = 5..214`）；設計水線 `z_wl = 4`（吃水 `0.20 m`），水線長 `LWL = 8.25 m`。
- 最大船寬 `B = 1.40 m`（28 格，`y = 21..48`），平底 *fondo* 寬 `0.90 m`，舯乾舷 `+0.30 m`。
- 艏鐵 *ferro di prua* 最高點離龍骨 `1.25 m`（**水線上 `+1.05 m`**），艉鐵 *ferro di poppa* 最高點離龍骨 `1.05 m`（**水線上 `+0.85 m`**）。
- 艉部劃手站台 *poppa* 踏板表面離龍骨 `0.55 m`（**水線上 `+0.35 m`**）；右舷 *forcola* 樞軸 `(48.5, 43.5, 16.5)`（**水線上 `+0.625 m`**）。
- 站姿長槳 *remo* 全長 `4.20 m`（舷內 `1.35 m`、舷外 `2.85 m`，中位姿態 `rotate = -36, 0, 58°`，框 `(9.2,31.1,-17.1)–(68.4,69.2,33.1)`，右舷延伸極限距中線 `+1.735 m` ⇒ 活躍掃掠總寬 `2.435 m`）。
- 拓樸驗算：`stats structure=1` ⇒ `14,900` voxels、`1` 個 6 連通元件、`0` 個封閉空腔、`0` 覆蓋重疊。
