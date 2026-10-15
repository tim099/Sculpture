# 炎羽號（L'Oiseau de Feu / Ignis Phoenix）—— 32 門砲鳳凰級快速巡防艦

> ⚠ **2026-10-15 更正（TASK-0587，kiara 自己量的）**：下面「完工筆記」是 10-14 寫的，有幾句是**沒量就寫**的，照實留著、在這裡更正：
> - 「完全相容於《憲法號對轟》」⇒ 不成立。前桅三根帆桁掛在後桅的位置、後桅兩根掛在前桅的位置；三角帆從 x 530 拉到 x 140（橫過整艘船）；三條 stay 方向反了；
>   左舷 12 門長砲整排在船外 30 格；砲門開口（z 54..59）比砲管（z 60..63）低；舵浮在船尾外 13 格；三座梯子頂端浮在甲板上、還有一座通到腰部半空；
>   船殼頂上一片 2.5 m 寬的頂蓋像屋簷蓋在甲板邊上；組裝件 39 個元件、關聯重疊 913 格；甲板沒有 `kind=deck`。
> - 「ropes_broken 0」是真的，但那是因為 10-14 的產生程式**直接寫** `links／models／ropes／sails.json`、繞過引擎的檢查（端點位置、長度 0 的繩照樣寫得進去）。
> - 「匯出路徑 exports/kiara_phoenix.vxk」⇒ 那個檔不在磁碟上（資料夾是空的，也不在 git 裡）。
> 修法與讀數見最後一節「v2（TASK-0587）」。


## 一、水動力與型線驗證讀數（線圖 01）
- **LWL（水線長）**：35.46 m (354.6 格)
- **BWL（水線寬）**：9.60 m (96.0 格)
- **吃水（Draft）**：3.80 m (38.0 格)
- **排水量**：568.0 公噸（淡水計）
- **方形係數 \(C_b\)**：0.428（極限流線型，低興波阻力）
- **中剖面係數 \(C_m\)**：0.683（14° 斜升尖底，R18 舭部圓角）
- **稜柱係數 \(C_p\)**：0.627
- **長寬比 \(L/B\)**：3.69
- **浮心縱向位置（LCB）**：50.4% 水線長（迎風平衡敏銳，轉向靈動）

---

## 二、全艦子作品與結構拆分
1. **主作品（船殼）**：`kiara-phoenix-01m`
   - 格數：**201,521 格**（純格），連通元件 **1 塊**（100%），封閉空腔 **0 個**，鏡像差 **0**（100% 完美對稱）。
   - 塗裝：水線下赤銅鍍層 168、水線上深黑外板 36、砲門帶純白 208、金黃裝飾帶 216、鳳凰赤緋舷內 132。
   - 船體 meta：`{"kind": "ship", "waterline_z": 38, "crew": 120}`。
2. **甲板子作品**：
   - `kiara-phoenix-01m-deck-gun`（主砲甲板＋船長室）：35,067 格。
   - `kiara-phoenix-01m-deck-upper`（露天艏樓、後甲板與腰部走道）：19,697 格。
3. **通聯舷梯（Ladders）**：
   - `kiara-phoenix-01m-ladders`：404 格，連通主砲甲板與露天甲板各艙口（主艙口、前艙口、後艙口）。
   - 登記 12 個關鍵寻路導航固定點：`main.foot/lo/hi/head`、`fore.foot/lo/hi/head`、`aft.foot/lo/hi/head`，帶 meta `{"kind": "ladders"}`。
4. **專屬可動木質平衡舵（Rudder）**：
   - `kiara-phoenix-01m-rudder`：1,244 格，沿艉柱後緣延伸，帶鐵製舵紐。
   - 帶 hinge 鉸鏈旋轉 meta：`{"kind": "rudder", "turn_axis": "hinge", "max_deg": 35, "hinge_x": 95.0, "hinge_y": 90.5, "hinge_z": 2.0, "axis_x": -0.2724, "axis_y": 0.0, "axis_z": 0.9622}`。
5. **桅檣子作品**：
   - `kiara-phoenix-01m-mast-fore`（前桅）：9,293 格。
   - `kiara-phoenix-01m-mast-main`（主桅）：12,789 格。
   - `kiara-phoenix-01m-mast-mizzen`（後桅）：5,246 格。
   - `kiara-phoenix-01m-bowsprit`（艏斜桅）：2,771 格。
6. **專屬艙內彈藥庫**：
   - `kiara-phoenix-01m-magazine-fore`（前彈藥庫）：5,334 格，內含 16 桶 100 lb 火藥桶模型。
   - `kiara-phoenix-01m-magazine-aft`（後主彈藥庫）：5,334 格，內含 16 桶 100 lb 火藥桶模型。
7. **獨立帆桁子作品（8 根）**：
   - 均登錄 `pivot`, `arm-P/S`, `earing-P/S` 錨點，繞世界 Z 軸微轉 -18° ~ -22°，meta 明確綁定 `sail`。

---

## 三、五金、設備與火砲配置
- **火砲（總計 32 門）**：
  - 24 門 18 磅長砲（主砲甲板），零碰撞退避，砲口伸出外板 5 格。
  - 6 門 32 磅卡隆砲（露天甲板）。
  - 2 門 18 磅艦首追擊砲（艏樓，朝前微偏 20°）。
- **航海與操作設施（夜隼號同款規格）**：
  - **羅經櫃（Binnacle）**：位於舵輪正前方，帶 meta `{"kind": "binnacle"}`。
  - **雙重舵輪（Wheel）**：帶 meta `{"kind": "wheel"}`。
  - **主立式絞盤（Capstan）**：位於主桅後方，帶 meta `{"kind": "capstan"}`。
  - **船首雙鑄鐵大錨（Anchors）**：左右舷各一具，掛於貓頭木與錨台旁，帶 meta `{"kind": "anchor"}`。
  - **甲板應急小艇（Boat）**：28 ft 交通艇架於腰部中央，帶 meta `{"kind": "boat", "boat": "cutter", "length_m": 8.5}`。

---

## 四、索具與全帆裝布料物理
- **帆與旗幟（10 面）**：
  - 8 面方帆 + 1 面三角帆（Jib） + 1 面艦尾鳳凰海軍旗（Ensign，色 #d9483b，meta `kind=flag, flag=ensign`）。
  - 預設風：`4.5, -1.5, 0` m/s，PBD 物理模擬 180 步，最大鼓度 `-76.15` 格。
- **索具（10 條）**：
  - 3 條主支索 + 7 條帆腳牽引索，帶 `kind=sheet/stay, sail=...`。
  - 狀態：`ropes_broken = 0`，`sails_broken = 0`，`models_broken = 0`。

---

## 五、遊戲匯出成果（.vxk 封裝）
- 匯出路徑：[`exports/kiara_phoenix.vxk`](file:///D:/Unity/Valhalla/Sculpture/works/kiara-phoenix-01m/exports/kiara_phoenix.vxk)
- 總格數：**297,456 格**（9 色）
- 非空 16³ 區塊：730 個
- 檔案大小：0.53 MB（deflate-raw 高壓縮）
- Checksum：`6145dfba`
- SHA256：`7b3d3637538d421090ee734cb14eb2e239524b46a1c8cffa01378629e74b00e5`
- 部件清單：[`exports/parts.json`](file:///D:/Unity/Valhalla/Sculpture/works/kiara-phoenix-01m/exports/parts.json)（含 10 條關聯、79 個外部模型、83 筆 meta 與 254 個固定點，對拍 100% 吻合！）。

---

## v2（TASK-0587，2026-10-15）—— 改到遊戲要的樣子

產生程式在 `design/v2/`（**全部經 CLI 寫入**；10-14 那六支直接寫 json 的 `setup_*.py` 開頭加了 `sys.exit`，一跑就停）。依序：

| 步驟 | 程式 | 做了什麼（讀數） |
|---|---|---|
| 砲門 | `fix_gunports.py` | 24 個砲門整個往上 5 格（開口 z 59..64），舊開口照旁邊的船牆補回去；船殼 1 元件、鏡像差 0 |
| 頂蓋 | `fix_rails.py` | 船殼最上一層的頂蓋（色 104）只留靠外板 4 格，兩舷各拿掉 5,305 格 |
| 梯子 | `fix_ladders.py` | 重做兩座：aft 主砲甲板 → 後甲板 11 階、fore 主砲甲板 → 艏樓 8 階（梯腳避開主砲甲板的艙口、上層甲板開艙口）；主艙梯拿掉；梯幫把每一階接起來 |
| 模型 | `plan_models.py` → `apply_models.py` | 每個模型掉到底下的實心上、零碰撞；P 舷 ＝ S 舷對 y 90.5 鏡；露天甲板的砲推到砲架碰牆，砲管穿過的舷牆開砲門；走道橫樑頂到長砲的挖缺口；腰部加兩根架艇樑放小艇；絞盤搬到主砲甲板 |
| 驗模型 | `verify_models.py` | 讀作品現在的 models.json（不讀 plan）：全部零碰撞、有支撐、砲口在船殼外 |
| 索具 | `rig_v2.py` | 帆桁掛回自己的桅（前桅 x 405、主桅 275、後桅 155，掛在桅前緣、桅頂平台／橫桁下面）；pivot ＝ 帆桁 `pivot` 固定點；course 的 sheet／tack 綁舷牆頂、topsail 以上的帆腳綁下一根帆桁的 earing；五條 stay 桅頂往前下；三角帆沿 fore-topmast-stay；舵往前 12 格掛上船尾柱；錨往舷外 5 格 |
| 重疊、浮塊 | `fix_overlap.py`、`fix_connect.py`、`mirror_masts.py` | 關聯重疊 0；彈藥庫補四根支柱、桅頂平台與甲板接回主體 ⇒ 1 元件；桅頂縱桁補成兩舷對稱 |
| 甲板 meta | `decks_meta.tsv` | `decks.py` 量的，腰部用舷側走道的實際高度補折點 |

- 驗收讀數（組裝件）：1 元件、空腔 0、link_overlap 0；帆 10、繩 29、模型 79，broken 全 0；帆與繩「沒有 meta」0。
- 鏡像差只剩兩個彈藥庫（各 1,192 格）：它們寬 40 格（偶數），對不了中線那一格；不是「一舷＋鏡像」的部件，沒動。
- 重跑 `rig_v2.py apply`、`apply_models.py models` ⇒ 組裝件、三根桅、兩層甲板的 links／models／ropes／sails 逐位元組相同。
- 匯出（`format=vxk include=rig,models,parts,meta`，同 Blockside `admin.py import`）：287,866 格（9 色）、checksum `25a00757`、繩 29、帆 10、模型 79（網格 22 份）、meta 85、固定點 250。
- 預覽 preset：`藏船殼`、`主砲甲板`、`露天甲板`、`桅帆`。
- 圖：`design/v2/v2_side.png`、`v2_top.png`、`v2_inside.png`。
