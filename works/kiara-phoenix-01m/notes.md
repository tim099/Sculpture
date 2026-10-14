# 炎羽號（L'Oiseau de Feu / Ignis Phoenix）—— 32 門砲鳳凰級快速巡防艦 完工筆記（夜隼號級細節補完版）

> 作品代號：`kiara-phoenix-01m`（主船體）／`kiara-phoenix-01m-assembly`（全艦現組組裝件）
> 比例：0.1 m / voxel (`meters_per_voxel = 0.1`)
> 規格定位：歷史真實 1782 法式 Hébé 級 32 門快速巡防艦 + 地中海謝貝克前探艏柱流線，完全相容於 ame《憲法號對轟》遊戲（.vxk 封裝）。

---

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
