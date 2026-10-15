# 收穫號 TODO

## 下一步：匯進 Blockside（TASK-0599）
- 彈藥庫與甲板物件已上船（階段九，notes）；**階段九還沒提交**（Sculpture 23d1a5f 只到階段八）。
- 匯出 `format=vxk include=rig,models,parts,meta` ⇒ Blockside `admin.py import`；跑 `admin.py shipcheck`：砲班站不站得滿、開場就掉的、meta。
- ⚠ 新砲種（18l、12l、6l 都在遊戲砲種表裡）與三角帆（lateen 標 yard=gaff、sail=gaff）跟 ame 對好；lateen 的 meta 還在等 ame（seq 24767）。

## 還沒有的（不在現有子單裡，問 Tim）
- **舵**：船殼裡沒有、也沒有舵模型（造船規格 §9 rudder：舵模型要登記 stock-top）。
- **錨**：共用元件 `basecamp-frigate-constitution-01m-anchor`（§9 anchor：船殼登記 hawse-S／P）。
- 砲索與砲具（造船規格 §4.4）。
