# 潮墓號 2026-10-15 索具獨立後驗

依 Sculpture_Blueprint_Build §6.6，唯讀作品與遊戲；所有輸出只在本資料夾。沒有 import 作者驗證程式。解析 VXK header/chunk 與事件 placed_colored/carved_voxels，自行重播十桁實心 source cubes；遊戲綁端另直接執行當前原 meshOcc/yardNear 函式。

## 已完成範圍

最新交付輸入是 `final_heads.vxk` SHA256 **`76d945aca4f55556f5b952b7a5a3b4183cbe00a6f1b9d44f7359a56fd3bc5036`**。它由主要驗證輸入 `final_rig.vxk` SHA256 `ba3572e6b7f360fcbdbeb3a05e398b51963c2c5d9034ac0674373268c8a5927d` 增量修 4 條 backstay 上端而成，增量後驗見下。檔案在作品 `design/continued_20261015/`，本資料夾沒有改寫作品。布與 robband 靜態完整三角檢查的輸入是 `after_robbands.vxk` SHA256 `bfe7b534bd0750e7c53d095bda880a8cc2c1afb2803f79b491d61e6b8c96db83`。

- 8 條 main/fore course/topsail lifts、10 條上層 braces：各自 163 個 square-yard absolute 角度，均勻涵蓋 −0.70..+0.70 rad；實讀遊戲常數 BRACE_MAX=.70、r0=−18°，因此旋轉的是 absolute angle−r0。繩為兩點，遊戲 yardRopes 弧長插值恰好等於旋轉臂端＋固定另一端的直線。對 body 與十桁 source cubes 做 segment/capsule 對 AABB 最短距離測試。沒有發現離開附著區的穿越；對 body 接觸只在桅端，最深 2.590 格。對桁接觸只在自己的臂端，lifts 接觸弧長上限 3.556..4.211 格，brace 上限 1.643..3.246 格。這些列為具體臂端附著接觸，沒有把全部首尾三格一律豁免。
- 16 條 main/fore shroud/backstay 對十桁亦做同樣角度取樣，沒有桁穿越。對其 own square yards 另用 source 全寬包絡、半徑擴張的 Z slab、`|dx| cos(.7)−|dy| sin(.7)−source_halfwidth−rope_radius` 對每段 Z 範圍兩端求下界，證明完整連續 ±.70 避開 own yards。最小下界 **1.692607648 格**。這個連續證明不替代其他桁的獨立角度組合驗證。
- 84 條 main/fore ratlines 靜態對 body 與十桁碰觸全 0。四條最低階 .065 新比例也逐條驗過；mizzen 的另外 42 條 ratlines 未新增全檢。
- 實際遊戲 meshOcc/yardNear：所有上述 standing/ratline 端點都沒有被誤認為桁；8 lifts、10 新 braces 都只有正確的臂端被認領，固定桅端均未被認領。兩 robbands 兩端都正確隨 mizzen topsail 桁轉。此處沒有修改 ropeYards 的純幾何 fallback 程式。
- main shroud 新下端只碰 Z128 的舷牆固定格，接觸沿繩 ≤1.103 格；main backstay 下端只碰固定那 1 格，沿繩 ≤0.839 格。先前 Z133..135 的 shroud 次生碰觸及 Z138..140 的 backstay 穿欄，均已消失。上端 shroud 接桅 ≤2.403 格。
- 原 final_rig 的 main/fore backstay 中央 truck 綁法，上端分別沿桅末 **6.551／5.419 格** 接觸。這些接觸已經以下列最終增量縮短；此舊讀數保留供追溯。

## final_heads 增量後驗

逐欄比較 final_rig：只有 4 條 backstay 的 `pts`、`ends` 改變；其他繩、全部 sails/models/meshes 完全相同。4 條增量重新做 body 精測、十桁全部取樣與 own square yards 連續 strip；全部未見中段穿越。main 上端附著末段縮至 ≤**2.936 格**、fore ≤**2.427 格**；main 下端舷牆附著 ≤0.839 格，沒有 Z138..140 的舊穿欄。全體 standing own-yard 連續下界仍為 **1.692607648 格**。

after_robbands／final_rig／final_heads 三份 VXK 去除 header 後的 chunk 座標與 voxel payload SHA256 完全相同，因此 body 的逐格逐色一致，cloth/sheet/robband 的靜態證據可直接沿用。結果見 `body_payloads.json`、`heads_audit.json`、`heads_sweep.json`。

## 帆與附著

`mizzen-topsail` 完整 front/back triangles 均對 body 及十桁作 triangle/cube 嚴格內部多邊形裁切；正面積穿入全 0，舊 `(207,120,336)` 擦桅已消失。這份輸出是指定模擬時間的完整靜態檢查，不是自由布連續動態證明。

兩 sheet 對 body 全 0，只碰 crossjack 的原本附著端：P 末 1.920 格、S 末 1.931 格。兩 robbands 對 body 全 0，只碰 topsail 原 earing 根部：P 首 1.626 格、S 首 1.625 格；未穿其他桁。

`after_robbands` 到 `final_rig` 逐欄比對：302 條 rope 數量不變，只 50 條的 `pts` 改動（8 main standing＋42 main ratlines）；所有 sails、models、mesh 幾何完全相同。沒有新增／刪除 rope。因此上述 cloth/sheet/robband 靜態幾何證據可沿用；body payload 一致性另見增量讀數。

## 負向對照與修正過程

測試不是只會印 0。獨立讀回舊 source_after.vxk，確實重現：main-course.lift-P 穿 main topsail；main-topsail.lift-P 穿 main topgallant；main-shroud-P0 穿 main course。

舊 cloth 對當前相同桅身作同一嚴格內部裁切，亦重現原 `(207,120,336)` 第 96 三角片的 **0.0123890263 格²** 擦桅。`negative_cloth.json` 還列出原 head 附著區的其他接觸，不能把那些數字合併宣稱都是自由內片缺陷。新帆對整個 body 的正面積讀數全 0。

本輪第一次 standing 修法的四最低 ratlines 也被實測抓到真中段穿欄：main P/S 於弧長 19.67..21.93/38.59 格，fore P/S 於4.58..26.83/38.41 格。提高第一階至 .065 後讀數為 0。main 初版下端沿欄 Z128..135 和 backstay Z138..140 穿越也有具體格證據，平移足點後消失。這些不是根據繩名推測。

## 讀數與重跑

已凍結十桁 source cells/pivot/at/r0/meta 與每個來源事件、placement 檔的 SHA256；已凍結當時完整遊戲 meshOcc/yardNear/ropeYards/yardRopes/braceYards 原始檔與常數、來源路徑／SHA256；最終 VXK 及負向、增量所需 VXK 原件亦保存在 snapshots。`VERIFY_FROZEN=1` 配 `VERIFY_VXK` 可完全跳過活作品事件與遊戲目錄重跑，步驟見 **RERUN.md**。check.py/bind.js/cloth.py 的 frozen 核心重跑已實際執行：results.json 與 cloth.json 皆為最終 final_heads SHA，118 條繩範圍與完整靜態布檢查結果一致；frozen_run.log、frozen_cloth.log 保留執行結果。來源與各檔完整性見遞迴 MANIFEST.json。freeze.py 是建置快照工具，不是重跑驗證入口。

- `results.json`：主要 final_rig 118 條繩的 body/yard 接觸，角度、格座標與弧長區間。
- `final_audit.json`：逐欄增量、standing 接觸每格端距、own-yard 連續 strip 下界、舊索具負向對照。
- `cloth.json`：完整帆內片及 sheet/robband/四最低階靜態讀數。
- `bindings.json`：實際當前遊戲函式產生的綁端結果。
- `heads_audit.json`、`heads_sweep.json`、`body_payloads.json`：最終 4 backstay 增量、十桁取樣、逐格 payload 證明。
- `negative_cloth.json`：舊布面負向對照，含原第 96 三角片微小擦桅。
- `after_braces_results.json`：尚未修四最低階與 main 足點時的負向實測記錄。
- `check.py`、`final_audit.py`、`cloth.py`、`bind.js`：獨立檢查程式。依賴 Python/numpy、Node，原作品事件及遊戲原函式。

尚未驗證：全部 302 條繩的 model-aware 動態完整掃掠、全部帆自由布連續動態、非同步不同桁的全部角度組合、繩對全部非 yard 模型與彼此碰撞、木料或索具的工程承載能力。上述有限範圍不應寫成「全船全帆索驗收通過」。
