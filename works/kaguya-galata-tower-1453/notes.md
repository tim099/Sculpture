# 加拉塔塔 1453（基督塔 Christea Turris，熱那亞，1348）—— kaguya

委託：Tim 2026-10-20「建造加拉塔石塔吧 參考歷史資料與圖紙 最後由妳繪製圖紙並建造(資訊不足的部分由妳設計) 建造後在放到地圖上」（TASK-0748）

## 是什麼
- **成品**：本件 `kaguya-galata-tower-1453`。它是組裝件，自己一格都不雕。
- **子作品**（關聯 at 0,0,0）：
  - `-body`：塔身、樓板、門、1452 年外堡。
  - `-roof`：鉛皮圓錐頂、旗杆、熱那亞旗、帶十字的金球。
- **比例與框**：0.2 m／格；框 160 × 160 × 250 等於 32 × 32 × 50 m，就是 Blocksail 加拉塔那塊地塊。
- **方向**：正面（y 0）朝城外（北），門在背面（南、城裡）。地塊 rot 270。
- **固定點**：
  - `lot-0`：0,0,0
  - `door`：80,126,0（門外第一格）
  - `flag`：79,79,222（旗杆頂）
- **meta**（塔身那條關聯）：kind=building、use=tower、style=genoa、lot=32,32、model=galata-tower。
- **遊戲**：Blockside 把它匯入成 `galata-tower`、用途 landmark。地塊帶 `model: "galata-tower"` 才會用它，所以不會被別的 tower 地塊挑到。

## 設計與圖紙（design/）
- `plan.json`：全部參數。`provenance` 逐項寫出處，分成「參考資料」和「設計決定」。
- `draft.py`：照參數畫圖紙 `sheets/blueprint.png`。內容是南立面、南北剖面、三層平面、配置圖、圖框；畫線用參數，⛔ 不從格子拍。
- `tower.py`：照同一份參數產格子（numpy、決定論）。
- `build.py`：產遮罩、組裝清單、讀數（`verify.json`），以及格子的立面、剖面、俯視 `sheets/voxel_views.png`。
- `apply.py`：抄 `kaguya-roman-1453` 的，負責落格與組裝。用法：

```bash
python -I -X utf8 -B build.py . && python -I -X utf8 -B draft.py .
python -I -X utf8 -B apply.py . create|stamp|anchors|links|check
```

## 依據
- 外徑 16.45 m、內徑 8.95 m、牆厚 3.75 m：en.wikipedia Galata Tower。
- H. S. Sağlam, *A Reevaluation for the Genoese period of the Galata Tower*, In-Scription 3 (2021)：
  - 熱那亞時期至少 30 m。
  - 熱那亞砌體到 4 層 +21.09 m。
  - 磚層 +13.21 m、+17.17 m。
  - 射口深、窄、底斜，4 層以下不規則。
  - 3 層三個大射口。
  - 1420 年 Buondelmonti（Biblioteca Marciana）：頂層盲拱、雉堞、圓錐頂。
  - Düsseldorf 抄本（約 1485–90）：屋頂較低較寬、簷伸出雉堞外，頂上熱那亞旗。
  - 帶十字的球。
  - 粗鑿的雜色石塊夾碎磚。
  - 1452-04-01 的半圓外堡。
- 設計決定（資料沒有）：
  - 30 m 這個高度。
  - 盲拱 16 個、雉堞 24 個。
  - 簷 32 m、錐高 9 m。
  - 外堡半徑 14 m、高 5 m。
  - 門的位置；射口的位置與數量。
  - 石色比例：第一版深藍 6％、灰藍 20％，遠看像迷彩，改成 3％／13％。

## 讀數（2026-10-20）
- **格數**：71.6 萬（塔身 61.2 萬、屋頂 10.4 萬）。
- **元件**：2 個（塔、外堡），框外 0、浮空 0。
  - 第一版十字架跟金球差一層，浮空 64 格。
- **封閉空腔**：塔裡被樓板隔開的房間，照建築規格不管。
- **引擎 `apply.py check`**：3 件每件缺 0、多 0、色差 0；`link_overlap` 0、`link_clipped` 0。
- **從格子量回來**：
  - 外半徑：@10 m 8.42（參數 8.225 ＋ 不規則起伏 ＋ 半格）、牆腳 @1 m 8.81。
  - 簷 9.37（參數 9.4）。
  - 錐頂 40.6 m、最高 47.4 m。
- **遊戲裡**：加拉塔塔擺了 1 個，接在三級石牆上，h 49.68 m、石基。
  - 以前手擺地塊一疊到東西就沒有高度；Blocksail 這次修了。

## 改成特殊建築＋布旗（2026-10-20 下午）
Tim：「其實我是想說把加拉塔變成一種建築(特殊建築) 直接用城建系統蓋上去」「然後旗幟可以改成布?(參考船隻)」
- **用途**：塔身那條關聯的 meta `use` tower → `galata-tower`（Blocksail 的特殊建築就是這一種、遊戲照用途挑）；上一版的 `model` 刪掉。
  - 用 `work sub=meta part=link`（null 刪鍵）改；⚠ `apply.py links` 重下同名關聯會被擋（rc=2，要 overwrite=1），只改 meta 不走那條。
- **旗**：`tower.py` 不雕格子旗了，屋頂 104,309 → 104,232 格（刻掉 77 格）；多兩個固定點 `flag-top` 81,79,222、`flag-bottom` 81,79,215（旗杆東側、綁邊）。
  - 成品掛一面帆：`work sub=sail name=genoa-flag corners="flag-top|flag-bottom|92,79,215|92,79,222" bind=0 free=2,3 color=255`，再 `sub=meta part=sail` 加 `kind=flag`、`flag=ensign`、`pattern=genoa`（同造船規格的旗）。7 × 7 布點、72 三角形。
  - `manifest.json` 有記 `sails`，但 `apply.py` 還沒有 sails 那一步（這次手下 CLI）。
  - Blockside 匯入只記四個角，遊戲自己拉 10 × 6 的布、照風飄，圖案 genoa ＝ 白底紅十字。
- **讀數**：`apply.py check` 3 件每件缺 0、多 0、色差 0，`link_overlap` 0；總格數 716,269。
- **遊戲裡**：照用途擺了 1 個；塔頂布旗從側面看展開、幾秒內來回擺，沒有發散。

## TODO
- 樓梯廊道（牆裡 1～4 層的磚拱樓梯）沒雕。
- 外堡跟遊戲的城牆模組（三級石牆）在交接處是疊在一起的，沒有做接頭。
- 塔前的壕溝沒挖進地形。
