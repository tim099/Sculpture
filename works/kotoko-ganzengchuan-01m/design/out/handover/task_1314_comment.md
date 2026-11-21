**《Blocksail》1666 亞洲船③ 福建趕繒船 Ganzengchuan（`kotoko-ganzengchuan-01m-assembly`）全部 14 項驗收步驟已完成並通過交船對帳** 🔍

- **主要作品與幾何**：
  - 總成：`kotoko-ganzengchuan-01m-assembly`（「福建趕繒船」，`0.1 m/格`，`384×192×384`，`135,808` 格、`components=1`、`cavities=0`、`link_overlap=0`、`models_drawn=62, models_broken=0`、`ropes=98 (ends_ok=196/196)`、`sails=4, sails_broken=0`）。
  - 全 31 件作品（總成＋30 件子作品 `tags=sub`）均具明確 `meters_per_voxel`（`0.1`／`0.05`）；全 62 具模型均明寫 `scale`。
- **步驟 11（舵／舵柄／貓頭錨架／四爪鐵錨）**：
  - `kotoko-ganzengchuan-01m-rudder`（`2,628` 格、5 開孔中式升降舵，`stock-top=(54,96,58)`，`spin=rudder, max_deg=35`）＋ `kotoko-ganzengchuan-01m-tiller`（`47` 格、`spin-a/b` 連動尾樓舵孔 `carve 9+60` 格，`±35°` 掃掠 0 碰撞）。
  - `kotoko-ganzengchuan-01m-anchor-gear`（前腰雙舷貓頭架 `x=279..280, z=51..52`，完全讓開船眼 `x=305..310`）＋ 複用 2 具 `kotoko-fusta-01m-anchor-grapnel`（`scale=0.45`, `kind=anchor, anchor=bower`）＋ 船殼 `hawse-S=(282,120,48)`／`hawse-P=(282,72,48)`；`DETERMINISTIC = True`、`probe shift=錨-S:-4` 檢出 `19` 格碰撞。
- **步驟 13（兩舷輔佐長櫓＋`render=pole`）**：
  - 新建通用長櫓 `kotoko-ganzengchuan-01m-oar`（`655` 格、`0.05 m/格 ⇒ scale=0.5`、`render=pole`、`components_6=1, cavities=0`），配置雙舷各 2 支＝共 4 支（`x=195.5, 246.0`、`rowers=2`、總計 8 位操櫓手、`total_static_hits=0`、`total_sweep_hits=0`、8/8 站位 `floor_ok/head_ok/mod_ok=true`、`probe drop=oar-S01:-3` 檢出 `10/313` 碰撞）。
- **步驟 14 & 15（Blockside 匯入對帳與交船基準）**：
  - 匯出 `.vxk`：`D:/Unity/Valhalla/Sculpture/exports/kotoko-ganzengchuan-01m-assembly.vxk`（`421,379` bytes、`sha256: 4a3774d90478a5229352523dca430638f8fcec3ca19309adc9eb229a30b8d66d`、`voxels=135,808`、`checksum=3783087331` / `0xe17d54e3`）。
  - 隔離 worktree `D:/Unity/Valhalla/scratchpad/kotoko-1314-blockside`（分支 `kotoko/1314-ganzengchuan`，commit `651daa0`，未動共用 `dev`）：
    - `admin.py ids` 全 80 件發配穩定 ID（含 `彈藥庫 hoist="ladders-1#hold,ladders-3#poop,ladders-2#fore"`）。
    - `admin.py shipcheck --id ganzengchuan`：**`✗ 0　⚠ 0`**（`✓ 沒有發現問題`；竹篾 `7/7`＋`9/9` 最遠 `0.05` 格；砲 `12/12` 全滿編且可補藥最遠 `8.2 m`；舵令 100%；槳 `4` 支 2P/2S 槳手 `8/8`）。
    - `admin.py ladcheck --id ganzengchuan`：`3` 座梯子 **`✗ 0、⚠ 0、✓ 3`**，4 層甲板全連通。
    - `admin.py disp`：`空載 100.5 / 標準 143 / 滿載 188 噸（載重 45 t，24%）`；`leakcheck` 超載極限 `+272 噸（+2.10 m）`。
    - `vxk_compare.py`（雕刻匯出 `.vxk` vs Blockside `_cache/ganzengchuan.vxk`）完全吻合（`135,808` 格、`checksum 3783087331`）；完整交船高度與 `geo/cfg/crew` 基準寫入 `notes.md` 與 `design/out/handover/`。
