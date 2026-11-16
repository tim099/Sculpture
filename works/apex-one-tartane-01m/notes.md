# 塔爾塔納（Tartane de négoce，約 1666，《露琪亞號 Lucia》）建造筆記

- **任務單**：`TASK-1299`（母單 `TASK-1211` 地中海船③：利佛諾－拉古萊特）
- **作者**：`apex-one`｜**完成日期**：2026-11-16
- **比例**：`0.1 m/格`（空間 `360 × 192 × 320`，對稱中線 `y = 96`，船頭 `+X`，船尾 `-X`，龍骨底 `z = 0`）
- **主作品（組裝件）**：`apex-one-tartane-01m-assembly`「塔爾塔納（雙桅商用 tartane，約 1666）」
- **船殼任務作品**：`apex-one-tartane-01m`「塔爾塔納 船殼（Tartane de négoce 1666）」（`tags=sub`）

---

## 一、雙桅商用型（*tartane de négoce*）vs 單桅漁用型（*tartane de pêche*）原型差異

1. **桅帆配置**：商用雙桅（Jean Jouve 1679 Pl. 19–20；H. Botcazou *Archaeonautica* 21, 2021）於舯設近垂直主桅 **mestre**（16.0 m，主斜桁 18.4 m），船首設前傾 23° 之前桅 **trinquet**（12.2 m，斜桁 10.4 m）並配前伸斜桅 **bout-dehors**（8.2 m，15° 仰角）張三角首帆 **foc**；單桅漁用型（Jouve Pl. 16）僅設單根舯主桅與單面大拉丁帆以利少數漁民操帆曳網。
2. **主尺度與貨載**：1621 年突尼斯 300-cantars（≈ 14.3–15.0 公噸）沿岸貨運契約搭配 Stefano de Zuanne（1686，42 威尼斯尺龍骨 = 14.58 m）與 Paragan 1 沉船等比例取中小型商船級距：
   - 龍骨底長 `13.60 m`（136 格，`x=90..226`）、船殼甲板長 `17.831 m`（`x=87..267`）、含斜桅與主斜桁全長 `~24.4 m`
   - 最大船寬 / 水線寬 `5.10 m`（51 格，`y=71..121`），長寬比 `3.496`
   - 平底（floor 半寬 11 格、起翹 astilla 2 格）圓舭淺吃水商船體
   - 全通封閉主甲板 *pont* ＋ 大面積主貨艙口（`1.9 × 1.3 m`，附格柵防水艙蓋）＋ 貨艙底板 *cale* ＋ 艉部下沉船長室 *chambre* ＋ 短尾樓 *dunette*
   - 無艦載舷砲（純風帆商船，`guns = 0`）

---

## 二、滿載吃水、利佛諾泊位與拉古萊特外港靠離泊實測

### 1. Blockside `disp` 與 `shipcheck` 實測讀數
- **設計水線 `waterline_z = 16`（`1.60 m`）**（與外板防污白牛脂漆 *spalmé* 上緣 `bottom_top_z = 16` 一致）：
  - **空載重量（格＋砲＋桶）**：`42.7 t`（橡木 60,868 格 = 42.6 t ＋ 窗玻璃 45 格 = 0.1 t；無火藥、無砲），空船浮高 `+0.30 m`
  - **標準排水量**：`47 t`（含固定壓艙 `4 t`）
  - **滿載排水量**：`62 t`（總壓艙空間 `19.5 t`，**貨物載重 `15 t` / 24%** 足額容納 1621 契約之 300 cantars 貨載而不增加吃水；每 cm `0.66 t`）
  - **最深吃水極限**：水線以上 `+3.90 m`（`200.9 t`；`leakcheck` 至露天主甲板進水需再多載 `113 t` / `+1.60 m`）
- **`hullLoa`**：船殼長 `17.83 m`（`wl` 水線長 `16.3 m`）

### 2. 利佛諾（`world/areas/livorno.js`）＆ 拉古萊特外港（`world/terrain.js` ＋ `TOWNS_1660S_NORTH_AFRICA.md`）適配量測
| 港口／區段 | 地點／泊位 | 實測水深 / 尺限 | 與本船比較（LOA 17.83 m、滿載吃水 1.60 m） | 結論 |
|---|---|---|---|---|
| 利佛諾 小艇泊位 | `berth-boat-1` (`10.3005, 43.5488`) | max LOA `12 m` / 深 `7.78 m`（航道 `5.09 m`） | 船殼長 `17.83 m > 12 m` | 不適用小艇泊位 |
| 利佛諾 小船泊位 | `berth-small-{1,4,6}` (`10.2999, 43.5485..43.5490`) | max LOA `36 m` / 泊深 `10.10–15.43 m`（`terrain.js -12.14 m`；航道 `8.38–8.57 m`） | 寬裕度 `18.2 m`、富餘水深 `+6.78–13.83 m` | **可自由進港靠離泊** |
| 突尼斯湖／內沙洲口 | `lon 10.2896–10.3064, lat 36.818`（`terrain.js`＋沙洲史料 ~1 m） | 海床 `-0.49` 至 `-1.28 m` | 水深不足（`-1.28 m < 1.60 m` 吃水） | **擱淺受阻**，證成必須於拉古萊特外港停泊、以小艇駁運入湖 |
| 拉古萊特 外港錨地 | `lon 10.3120–10.3344, lat 36.818`（`terrain.js`＋`ean32-13`） | 外緣 `-1.92 m` → 錨地 `-3.34` 至 `-4.92 m` | 外緣淨空 `+0.32 m`；外港錨地淨空 **`+1.74` 至 `+3.32 m`** | **外港安全靠離泊與駁運作業** |

---

## 三、給遊戲端（Blockside `config/game.json`）的高度表（`geo`）與船員設定

所有 Z 值以設計空間（`0.1 m/格`，龍骨底 `z = 0`）為基準：

- **船殼範圍**：`x = 87..267`（含舵 `79..267`、含斜桅與艏像 `79..331`），`y = 71..121`（中線 `cy = 96`），船殼最高舷牆 `z = 42`
- **各層甲板站腳地板面**：
  - `hold`（`level=0` 貨艙底板）：甲板面 `z = 6`，站腳 `z = 7`（`x=124..216`）
  - `cabin`（`level=1` 船尾艙室底板）：甲板面 `z = 19`，站腳 `z = 20`（`x=89..133`；含 `stern_cabin` `[104,87,20]–[117,105,33]` `1.40×1.90×1.40 m`）
  - `main`（`level=2` 主甲板，帶拋物線舷弧）：舯面 `z = 23`、艉起翹至 `25`、艏起翹至 `27`，站腳 `z = 24..28`（`x=135..258`）
  - `quarter`（`level=3` 艉樓後甲板）：甲板面 `z = 35`，站腳 `z = 36`（`x=88..134`，艉胸牆頂 `z = 40..42`）
- **桅與最高點**：
  - 前桅 `fore`：`z = 9..129`（高出水線 `11.3 m`），前斜桁 `yard-fore-lateen` 上梢至 `z ≈ 148`
  - 主桅 `main`：`z = 7..167`（高出水線 `15.1 m`），主斜桁 `yard-main-lateen` 上梢至 `z ≈ 214`（全船最高 `21.4 m`）
  - 船首斜桅 `bowsprit`：`x = 252..331, z = 27..54`
- **建議 `geo`（已在 Blockside worktree 驗證）**：
  - `"waterline_z": 16`（`1.60 m`）
  - `"spar": [23, 37]`, `"marines": [23, 37]`, `"center": 25`, `"aim": 23`, `"aimZ": [6, 165]`, `"deckAim": [23, 37]`, `"rigAim": [45, 160]`, `"marineY": 10`, `"qx": 16`
  - `"gangway": [[165.5, 120.5, 31.5], [165.5, 71.5, 31.5]]`
  - `"role": "merchant"`, `"cargoT": 15`, `"cfg": {"pump": 4, "agile": 3.0, "upwind": 2.4}`
  - `"crew"`: `{"officers": 1, "helm": 1, "top": 0, "marines": 0, "monkeys": 0, "handsK": 0.2, "carpenter": 1, "sailmaker": 1, "surgeon": 0, "quartermaster": 0, "navigator": 1}`（開戰實站 12 人，缺 0 人）

---

## 四、帆裝三段張帆表（`Ship_Rigging §9.1`）

| 帆裝段位 | 張開之帆面（共 3 面帆） | 固定懸掛旗幟（2 面） | meta 設定 |
|---|---|---|---|
| 段 1（收帆 / 單帆） | `main-lateen` | `ensign`（托斯卡納聖斯德望十字旗）、`pennant`（紅色三角長旒） | `kind=sail, mast=main, sail=gaff, set=1` |
| 段 2（戰鬥帆） | `main-lateen`、`fore-lateen` | 同上 | `fore-lateen`: `kind=sail, mast=fore, sail=gaff, set=2` |
| 段 3（全帆） | `main-lateen`、`fore-lateen`、`foc` | 同上 | `foc`: `kind=sail, mast=bowsprit, sail=staysail, set=3` |

---

## 五、元件沿用與新造清單（`Ship_Setup §2.1`）

### 直接沿用現有共用元件（外部模型）
- `basecamp-ember-01m-boat`（`小艇`，`scale=0.19` ⇒ 3.42 m，置於腰部小艇架 `meta={"kind":"boat","boat":"cutter","length_m":3.4}`）
- `basecamp-ember-01m-capstan`（`絞盤`，`scale=0.125` ⇒ Ø 0.90 m，前甲板 `meta={"kind":"capstan"}`）
- `summit-night-falcon-01m-binnacle`（`羅經櫃`，`scale=0.20` ⇒ 1:1，艉樓甲板 `meta={"kind":"binnacle"}`）
- `gura-tridente-01m-lantern`（`尾燈-P`／`尾燈-S`，`scale=0.25`，艉樓雙角舷牆 `meta={"kind":"light","light_color":"#ff9e40"}`）
- `basecamp-frigate-constitution-01m-anchor`（`錨-S`／`錨-P`，`scale=0.28`，前舷 `meta={"kind":"anchor","anchor":"bower"}`）
- `summit-rocher-01m-barrel` ×6、`summit-rocher-01m-crate` ×8（貨艙商業橄欖油桶與貨箱，`scale=0.5`，因純商船無火藥庫，標 `meta={"deco":1}`）

### 新造子作品與理由（全部帶 `tags=sub`、`meters_per_voxel=0.1`）
| 子作品 ID | 用途 | 為何不沿用現有元件 |
|---|---|---|
| `apex-one-tartane-01m-deck-{hold,cabin,main,quarter}` / `-ladders-{main,quarter}` / `-rooms-cabin` | 貼合本船雙層與下沉艉艙線型之甲板、4 座梯子與空艙房框 | 甲板與梯井需隨本船龍骨與拋物線舷弧精密開孔 |
| `apex-one-tartane-01m-stern-glass` / `-deco-{beak,gallery,nameplate}` | 3 扇船尾窗玻璃（`material=glass`）、地中海弧形雕首像、艉陽台與「LUCIA」船名牌（`deco=1`） | 本船專屬船尾弧度與船名裝飾 |
| `apex-one-tartane-01m-mast-{fore,main}` / `-bowsprit` / `-yard-{fore,main}-lateen` | 前傾 23° 前桅、垂直主桅、15° 首斜桅與兩根雙截綁箍拉丁斜桁（`rig=lateen`） | 既有共用桅桁為方帆橫桁或不同尺度之拉丁桁，本船需嚴格對齊 10.4 m／18.4 m 雙桅幾何 |
| `apex-one-tartane-01m-channels` / `-flagstaff` | 對稱支索板＋deadeyes、船尾旗桿 | 需嚴格對齊本船舷側弧線與水線/艉欄 |
| `apex-one-tartane-01m-hatch-main` / `-boat-skids` | 19×13 格主貨艙口專屬防水格柵艙蓋（`kind=door, open=up, open_deg=30`）與跨艙口小艇架 | `gura-flyingfish-01m-hatch-main`（10×11）與 `meadow-venice-galea-01m-hold-hatch`（15×11）皆無法密合本船 19×13 格主貨艙口；特造 21×15×2 格蓋完全覆蓋圍板以通過防進水驗證 |
| `apex-one-tartane-01m-rudder` / `-tiller` / `-anchor-gear` | 沿 4° 艉柱至 `z=24` 之白牛脂／深橡木舵葉（`kind=rudder`）、17 世紀地中海長木舵柄（`kind=tiller`）與舷外錨架托板 | 舵需貼合本船 4° 艉柱與 `z=25` 陽台底緣；歷史年代早於舵輪普及期，故依 `Ship_Helm §9.8.1` 採實作舵柄 `tiller`（矩形無須標 `render=lathe/pole/wheel`） |

---

## 六、驗收與 Checksum 對帳（Blockside 獨立 worktree `.wt-apex-one-tartane` 分支 `apex-one/tartane-1299`）

- **總格子**：`60,913` 格（主作品 `stats structure=1`：1 元件、0 封閉空腔、0 重疊 `link_overlap=0`、`0` 超界色彩）
- **索具與帆**：`81` 條繩（`ropes_broken = 0`，162 端全綁好）、`5` 面帆/旗（`sails_broken = 0`）、`29` 件外部模型（`models_broken = 0`）、`16` 條關聯
- **出口與遊戲端比對（`VoxelKit/vxk_compare.py`）**：
  - `VoxelKit/_cache/tartane.vxk`（244,810 bytes，SHA256 `44ffa0339758eec6d59f620986ec0109dcec5dab68ff4fd0d3a9c676a3a0229d`，含 `ropebind` 預綁）
  - `Sculpture/works/apex-one-tartane-01m/exports/tartane.vxk`（258,155 bytes，checksum `02a6b9d0`，SHA256 `fa032cdb469d9eb3895c471a3958c9b795dc0f5ef38f8f7cf1d2a3daf9927d9f`）
  - `vxk_compare.py` 對拍結果：**`✓ 相同（容差內）：格子 60913、header 20 欄；繩 81、帆 5、模型 29（網格 17 份）；關聯 16`**
  - `config/vxk_lock.json` 指紋：**`c:948518df6b37552cbcd5ef3410532431bd7191bf`**
- **Blockside 全檢查結果（`src/admin.py`）**：
  - `shipcheck --id tartane`：**`✗ 0　⚠ 0 ✓ 沒有發現問題`**（修正 `75_shipcheck.js:283` 僅對有砲船檢查彈藥庫）
  - `ladcheck --id tartane`：**`✓ 4 座（✗ 0、⚠ 0）；甲板連通 4 層（✗ 0、⚠ 0）`**
  - `rooms.py check --id tartane`：**`✓ stern_cabin [104, 87, 20]–[117, 105, 33]`**
  - `disp --id tartane`：**`✓ 空載 42.7 t／標準 47 t／滿載 62 t／載重 15 t (24%)，要看的：（沒有）`**
  - `check` / `verify` / `srccheck`：全部通過（`1,698` 份網格三角形逐個對拍一致，來源指紋 `f49375059a5f76d5`）
- **產生程式確定性**：`draft_lines.py`、`draft_layout.py`、`draft_decks.py`、`draft_fit.py`、`draft_rudder_anchor.py` 雙次重跑全部逐位元組／stdout 一致。
