# 三叉戟號 TODO

## 下一步：階段二 船殼落格（TASK-0555）
- 標記 `船殼:begin` → `design/tools/stamp_lists.py gura-tridente-01m 0 masks/hull/hull_0{1..5}.vox.txt`（每刀讀回 placed ＝ 清單格數）→ `船殼:end`。
- 結果帳：`export format=list` vs 清單逐格（缺／多／色差）；`stats structure=1 mirror=y:200`。
- 線形對照：作品每個站位的外緣 vs `hull_lines.hb`，差 ≤ 1 格；反向對照（某站半寬 +3 ⇒ 報 3）。
- 組裝件 `gura-tridente-01m-assembly`（記 meters_per_voxel 0.1、1100×400×800）＋關聯 `船殼` meta `kind=ship, waterline_z=79`。
- 過程圖：船頭／船尾四分之三、側面、從上往下。

## 之後會撞到的
- 砲門階段（TASK-0556）：開口要刻穿 4 格牆；紅帶的紅色號先渲染比幾個再定（168 是銅，別選太近的）；船頭最前那幾個砲門在彎的船殼上（surface step 讀數 4–6）。
- 甲板階段：甲板舷弧照 `layout.deck_z`；桅孔照 plan.masts（後桅腳在 orlop）。
- 艏斜桅尖端會到 x ≈ 980；組裝件 x 1100 夠用。
