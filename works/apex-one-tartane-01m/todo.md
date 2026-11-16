# 塔爾塔納（`apex-one-tartane-01m`）建造待辦與渲染圖索引（`TASK-1299`）

## 步驟進度（依 `Ship_Steps`）
- [x] 步驟 1 開單確認雙桅 *tartane de négoce* 原型與單桅漁用型差異
- [x] 步驟 2 查現有通用元件、建船殼與組裝件（`meters_per_voxel=0.1`）
- [x] 步驟 3 查資料與新圖紙（`plan.json`、`lines.py`、`layout.py`、`sheet01_lines_v1.png`、`sheet02_layout_v1.png`）
- [x] 步驟 4 船殼落格、塗裝、船尾窗（`hull_01.vox.txt`、`draft_paint.py`、`check_hull.py`、`stage04_*.png`）
- [x] 步驟 5 甲板、梯子、空艙房（`draft_decks.py`、`build_decks.py`、`stage05_*.png`）
- [x] 步驟 6 裝飾：船尾窗玻璃、雕首像、陽台、船名牌 `"LUCIA"`（`draft_deco.py`、`stage06_*.png`）
- [x] 步驟 7 桅與拉丁斜桁（`draft_masts.py`、`build_masts.py`、`stage07_*.png`）
- [x] 步驟 8 索具、帆、托斯卡納旗與三角長旒（`draft_rigging.py`、`rigging_apply.py`、`stage08_*.png`）
- [x] 步驟 10 甲板物件與貨艙商用貨物（`draft_fit.py`、`build_fit.py`、`stage10_*.png`）
- [x] 步驟 11 舵、舵柄（*barre franche*）、雙錨與錨鏈孔（`draft_rudder_anchor.py`、`build_rudder_anchor.py`、`stage11_*.png`）
- [x] 步驟 14 `kind=ship waterline_z=16`、`ropecheck`、`tartane.vxk`、匯入 Blockside worktree、`ids`、`shipcheck ✗ 0`、`ladcheck ✗ 0`、`disp`、`verify`、`srccheck`、`stage15_final_iso.png`
- [x] 步驟 15 檢查表、高度表、checksum 與利佛諾／拉古萊特靠離泊驗證紀錄（`notes.md`、`journal/2026-11-16.md`）

## 檢查表追蹤（`Ship_Game §10`）
- `ropecheck`：`✓ 81 條繩兩端全綁，0 broken`
- `組裝件／船殼`：`apex-one-tartane-01m-assembly`／`apex-one-tartane-01m (sub)`，`0.1 m/voxel`
- `元件 reuse`：已盡用 `boat` / `capstan` / `binnacle` / `lantern` / `constitution-anchor` / `crate` / `barrel`
- `操舵鏈`：`舵柄 (kind=tiller, spin=rudder)` ⇒ `舵 (kind=rudder, stock-top, spin=rudder)`
- `甲板與樓梯`：4 層甲板 `kind=deck`，4 座梯子 `kind=ladders`（4×4=16 點），`ladcheck 4/4 ✓`、`甲板連通 4/4 ✓`
- `艙房`：`stern_cabin` `rooms.py check ✓`
- `門／艙蓋`：`艙蓋-主 (kind=door, open=up, open_deg=30)` 開口 247 格 ✓
- `帆裝與旗`：3 帆 `set=1,2,3` + `ensign`/`pennant`，`sail_without_meta = 0`
- `結構`：60,913 格、1 元件、0 空腔、`link_overlap=0`、`mirror_diff=0`（除有起吊鐵環之艙蓋蓋緣 2 格與左／右錨模型旋轉）

## 視覺檢視圖索引
- 圖紙：`design/sheet01_lines_v1.png` ～ `design/sheet06_masts_v1.png`
- 階段渲染：`overlays/stage04_*.png`、`stage05_*.png`、`stage06_*.png`、`stage07_*.png`、`stage08_*.png`、`stage10_{deck,stern,hold}.png`、`stage11_{stern,bow,bow2}.png`、`stage15_final_iso.png`
