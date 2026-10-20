# 大競技場 1453（Hippodrome，圍城之前）—— kaguya

委託：Tim 2026-10-20「接著回到君士坦丁堡」；問先蓋哪一棟時選「大競技場 Hippodrome」（TASK-0748；放到君士坦丁堡的地圖上，城建系統的特殊建築）。

## 是什麼
- **成品**：本件 `kaguya-hippodrome-1453`，組裝件，自己一格都不雕。
- **子作品**（關聯 at 0,0,0）：
  - `-stands`：兩條長邊的看台（基座＋30 階＋外牆與一排拱室）、北端起跑門（12 個門洞）、皇帝包廂殘塊。
  - `-sphendone`：半圓端柱廊（37 個柱位留 30 根）、柱頂迴廊與女兒牆、柱間的拱。
  - `-spina`：中線矮牆、狄奧多西方尖碑、蛇柱、砌石方尖碑、兩根散柱。
- **比例與框**：0.4 m／格（同聖索菲亞）；框 325 × 1125 × 90 ＝ 130 × 450 × 36 m ＝ Blocksail 的地塊（特殊建築 `hippodrome`）。
- **方向**：y 0 ＝ 北端起跑門（正面，朝方位 38°；地塊 rot 308）；y 往西南到半圓端；x 0 ＝ 東南側（大皇宮、皇帝包廂那一側）。z 0 ＝ 跑道面。
- **跑道面不雕格子**：遊戲的地塊整平面（或高差大時的石基頂）就是跑道。半圓端坡下那十幾公尺的拱基也是由地塊的石基撐（史實是約 15 m 的連拱牆；石基只是一塊平的，看不到拱 —— 照實記著）。
- **固定點**：`lot-0` 0,0,0；`gate` 162,0,0（起跑門正中）；`obelisk-theodosius-top`、`serpent-top`、`obelisk-walled-top`、`colonnade-mid`。
- **meta**（看台那條關聯）：kind=building、use=hippodrome、style=roman、lot=130,450、base=0、variant=a。

## 設計與圖紙（design/）
- `plan.json`：全部參數；`provenance` 分「參考資料」與「設計決定」。研究整理在 kaguya 的暫存區（`scratchpad/hip/research_hippodrome_1453.md`，28 列建模數字表），重點都抄進了 plan.json。
- `hippo.py`：照參數產格子（numpy、決定論）；量體先當實心 ⇒ 只留離空氣 2 格（0.8 m）內的格（底面當地面）。殘破照種子：長邊每 20 m 一段（種子 1453）、柱位（種子 1403）、起跑門上緣（種子 1204）。
- `draft.py`：圖紙 `sheets/blueprint.png`（平面、看台橫剖面、碑柱立面、圖框；⛔ 不從格子拍）。
- `build.py`：遮罩、manifest、讀數 `verify.json`、格子的立面與俯視 `sheets/voxel_views.png`。
- `apply.py`：抄聖索菲亞那一支（create／stamp／anchors／links／check）。

```bash
python -I -X utf8 -B build.py . && python -I -X utf8 -B draft.py .
python -I -X utf8 -B apply.py . create|stamp|anchors|links|check
```

## 依據
- Gilles《The Antiquities of Constantinople》（1540 年代實測）：半圓端柱廊剩 17 根、柱高 28 呎、柱徑約 1 m、柱距 11 呎；拱基頂跟跑道同高、從坡下 50 呎；兩座方尖碑的台階與底座尺寸。
- Clavijo 1403：37 根柱、頂上用拱相連可以走、有齊胸女兒牆；看台高、下有拱室；蛇柱三個頭都在。La Broquière 1432、Tafur 1437：已荒廢、作比武與騎射場。
- Wikipedia（Hippodrome、Obelisk of Theodosius、Serpent Column）；OSM 半圓端外牆 way 321386212（擬合半徑 64.9 m）；三座碑的位置照 Blocksail 史料表。
- Panvinio 1580 版畫（公有領域）只拿來看造型。

## 設計決定（資料沒有）
- 看台剖面（基座 2 m、30 階每階 0.8 × 0.4 m、外牆 16 m）、外牆拱的尺寸、石帶間距。
- 1453 年的殘破比例（55／30／15%）、倒掉的柱位、起跑門上緣、皇帝包廂的大小與位置。
- 半圓端不做座位、柱廊立在跑道面高度（研究 §3.4 ⚠ 待查證）。
- 中線兩根散柱的位置。

## 讀數〔量過〕（build.py ⇒ verify.json；apply.py check）
- 48.5 萬格（看台 45.6 萬、半圓端柱廊 1.5 萬、中線 1.4 萬）；元件 9、浮空 0；挖空 189.6 萬格。
- 狄奧多西方尖碑頂 25.6 m（史料 25.6）、砌石方尖碑頂 32.0 m（史料 32）、蛇柱 6.8 m（史料約 6.5）、柱廊頂 12.0 m；外框 130.0 × 448.4 m（柱廊縮在框裡 1.6 m）。
- 倒掉的柱位：9、10、11、13、21、29、31。
- `apply.py check`：4 件每件缺 0 多 0 色差 0、link_overlap 0；封閉空腔是挖空的內部（不管）。
- 第一版砌石方尖碑 33.2 m（碑身多 3 格）⇒ 碑身 72 → 69 格。

## 沒做的
- 看台下的拱室內部、柱廊倒下的柱段、場邊與場內的民房（Tafur 說有）、皇帝的四柱高座（Clavijo 1403）。
- Mamboury & Wiegand 1934 的實測平面沒拿到；看台階數、起跑門門數都是低可信度。
