# 餘燼號（The Ember）—— 奇幻風帆戰艦，魔改憲法號（0.1 m／格）—— 建造筆記

委託：Tim 2026-10-12（TASK-0519 傘）：「開另一個帆船作品，魔改憲法號做為另一艘船（由妳自由創作，炮的數量可以增加 1.5 倍，另外可以有船頭、船尾炮），可以走一點奇幻風（參考加勒比海盜）」。
空間 1024×320×800，座標約定同憲法號（X 船長、船頭 +X；Y 船寬、中線 160；Z 高度、z 0 ＝ 護龍骨底面；P ＝ y < 160）。造船規格見 Senate `Docs/Workflows/Sculpture_Shipbuilding.md`。

## 設計方向（設計決定，2026-10-12）
- **兩層砲甲板**：憲法號長度不動，在 gun deck 砲門上面插一段船身（research agent：英國 74 砲砲甲板 168 ft、憲法號 175 ft —— 長度差不多；74 比較寬、艙深多 5–6 ft）。
- 砲 82 門（憲法號 54 的 1.52 倍）：下層 28 門 32 磅長砲＋船頭 2＋船尾 2、上層 28 門 24 磅＋船頭 2＋船尾 2、上甲板 18 門 carronade —— 跟 Bellona 級 74（28×32、28×18、QD＋FC 18）同一個形狀。
- 奇幻（⛔ 不抄任何電影船的造型與名字）：黑船殼、暗金雕飾、更高的船尾與 poop deck、quarter galleries、船尾燈籠、原創船首像、深灰帆。之後各一張圖紙。

## 階段一 新圖紙 01：側面、橫剖面、甲板高度、砲位表（2026-10-12 晚，wake #132）
設計 `design/plan.json`；產生 `design/draft_profile.py` ⇒ `sheet01_profile_v1.png`、`sheet02_sections_v1.png`、`masks/band/{band_layer,entry_fill}.vox.txt`、`verify_profile.json`。
- 切口 **z 109**、插 **23** 格（＝ 憲法號 gun deck → spar deck 的間距 83 → 106）：先量了憲法號船殼每一層的組成 —— z 88–103 有砲門開口，白帶上緣船中 97、兩頭跟著舷弧升到 107，z 100–105 有 clamp（136），z 105 起有 entry port 的 9 欄缺口；**z 108–110 只有外板 36、肋骨 141、內板 177**（加中線 173 ×25、104 ×5）⇒ 插入段每層 ＝ z 108 的複製（entry port 缺口用 x 373 那一欄補）。
- 甲板：orlop、berth、下層砲甲板（＝ 憲法號 gun deck 82–88）不動；**上層砲甲板 ＝ 憲法號 spar deck 的位置（105–110，在切口下面）**；上甲板 ＝ spar deck ＋ 23（128–133）。三層間距都是 23。
- 砲門：下層 ＝ 憲法號已開的 15 個／舷；上層 ＝ 下層 ＋ 23（同一欄、上下對齊）—— 15／15 個框整個落在插入段裡；上甲板 ＝ 憲法號 spar deck 砲門 ＋ 23（12 個／舷，放 9 門，哪幾個等 poop deck 的設計）。
- 水線照憲法號 62.86（奇幻船，不照多一層甲板的排水量重算）。插入段是直的（不再往內收），要更多 tumblehome 之後再說。
- 讀數（verify_profile.json）：憲法號船殼 821,491（478 個事件，最後 2026-10-12/151329_081_052c44.json）；插入段一層 5,014（＝ z 108 的 4,942 ＋ 補缺口 72）× 23 ＝ 115,322；entry port 切口下那一截補 288；**餘燼號船殼 937,101**、1 元件、空腔 0；最高 z 159（憲法號 136）。
  反向對照：不補 entry port 缺口 ⇒ 來源層沒有格的欄 18（補了 9）—— 差正好是那 9 欄。
- 圖紙第一版有字型缺字（≈、⇒、⚠ 印成方塊）、表格兩欄疊字 ⇒ 改文字重產。

## 階段二 船殼落格（2026-10-12 晚）
- `work sub=assemble source_work=basecamp-frigate-constitution-01m at=0,0,0`（821,491 格，Credit 1）→ `work sub=move region=0..1023,0..319,109..799 delta=0,0,23`（回報 160,487 格變動 —— 憲法號 z ≥ 109 有 80,538 格；變動數的算法沒去查，結果帳對上）→ `stampvox band_layer.vox.txt` at 0,0,109..131 各一次（23 次，每次 placed 5,014）→ `stampvox entry_fill.vox.txt`（placed 288）。
- **結果帳**：作品匯出 vs 產生程式算的餘燼號 —— 937,101／937,101、缺 0、多 0、色差 0；1 元件、空腔 0。
- 標記：`船殼:begin` 是在 assemble＋move **之後**才打的（空作品打標記 exit 2）⇒ 它指的是「抬高之後、插入段落格之前」；`船殼:end` ＝ 插入段＋補缺口之後。
- 過程圖：`overlays/stage1_hull_{side,bowq,sternq}.png`、`stage1_constitution_side_compare.png`（同角度的憲法號船殼）。
- ⚠ 看得到的：插入段是黑的（複製 z 108 的外板色）、上層砲門還沒開；船頭在插入段那 23 層是直的、上面再接回憲法號的斜度（船頭有一個小折角）；船尾窗還在下層。

## 階段三 上層砲門＋塗裝 —— 新圖紙 03（2026-10-12 晚）
設計 plan.json `ports_upper`、`paint`；產生 `design/draft_ports.py`（讀標記 `船殼:end`）⇒ `masks/ports/upper_carve.vox.txt`、`masks/paint/paint.vox.txt`、`verify_ports.json`、`sheet03_ports_paint_v1.png`。
- 上層開口 ＝ 下層開口往上 23：下層開口從船殼量（憲法號 source_ports.json 每個框外擴 2 格裡、|dy| ≥ 10 沒有任何格的 (x, z)；船頭那個用憲法號 v1.2 的外框 643..651、96..103）⇒ S 1,311、P 1,311、兩舷差 0，每個砲門跟下層同大（99／88／…／船頭 72）。
- 插入段的牆是實心 4 格（177／141／141／36）⇒ 不補 141 包邊（憲法號那時是為了肋骨之間的縫）。
- 塗裝（奇幻：黑、暗紅、金；設計決定）：下層白帶 → 暗紅 128；同一組 (x, z＋23) 的外緣 → 暗紅（上層帶跟下層同一條舷弧）；兩條帶每一欄上下各一格外緣 → 金 248；下層白帶裡不在外緣的白（砲門側面）也換紅。船尾 x < 125 不動（白 154 格留給船尾那張圖紙）。
- 讀數：刻 10,512（外板 2,638、肋骨 5,188、內板 2,686；z 111–126，全在插入段裡）、換色 22,184（36 → 13,164、255 → 9,020；變成暗紅 17,808、金 4,376）；船側剩白 0。
- 落格：標記 `上層砲門:begin` → carvevox（顏色守門、10,512）→ stampvox overwrite=1（placed 22,184）→ `上層砲門:end`。
- **結果帳**：926,589 vs 設計 926,589，缺 0、多 0、色差 0；1 元件、空腔 0；上層開口裡 |dy| ≥ 10 剩下的實心 0（看得穿）。
- 過程圖：`overlays/stage3_ports_paint_{bowq,side,sternq}.png`。
- ⚠ 看得到的：船尾左下那塊白（船尾窗的白線，下一階段）；帶子在斜面上有一條條的明暗（tumblehome 的階梯，憲法號的白帶也這樣）。

## 階段四a 船尾：poop 加高、三層船尾窗、四個船尾砲門、船尾塗裝 —— 新圖紙 04a（2026-10-12 晚）
設計 plan.json `stern`；產生 `design/draft_stern.py`（讀標記 `上層砲門:end`）⇒ `masks/stern/{poop_add,openings_carve,paint}.vox.txt`、`verify_stern.json`、`sheet04_stern_v1.png`。
- 先量：船尾面是一整片平的 transom（同一個 z 每個 dy 的 x 都一樣；z 108–131 在 x 104、往上每 z 往後約 0.4）；船尾的頂 z 149–151（舊 cap rail）。z 146–152 沒有乾淨的一層（146–147 被上甲板砲門上緣切開、148–151 是 cap rail）⇒ poop **不插層、往上補**（憲法號階段十二的做法）。
- poop（設計決定）：x ≤ 215（上甲板第 3、4 個砲門之間、後桅後面）的每一欄照 z 146 的牆組成往上疊到 z 159、z 160 一層 cap 104（內外各多 1）；119 欄裡 19 欄碰到砲門開口、借最近一欄；舊 cap rail 留著當線腳。之後 poop deck 放約 z 148。
- 窗（dy 照憲法號船尾窗：中 ≤ 5、窄 8–11、側 14–24、外 27–33）：下層原本就開著（不刻、只畫金框）；**下層船尾砲門** ＝ 側窗往下開到 z 90（砲軸約 83 ＋ 11）；上層 ＝ 下層 ＋ 23（窗 118–124、側窗整個是砲門 113–124）；poop 底下的後甲板艙一列高窗 135–145。船尾面往船頭刻到碰到空氣（最多 8 格）—— 刻不穿 0。
- 塗裝：兩條砲門帶繞到船尾（帶高取 x 125 那一欄：91–101、114–124）、上下緣金；剩下的白（船尾窗台與 counter 那兩條）→ 金；每個窗與砲門外一圈 → 金框（窗之間 1–2 格的柱子整根變金）。
- 讀數：poop 加 12,765、刻 3,078（外板 1,228、肋骨 136、內板 1,714）、換色 2,644（暗紅 1,372、金 1,272，其中金框 658）；白剩 0；鏡像差 0。
- 落格：`船尾:begin` → stampvox poop（placed 12,765）→ carvevox 窗與砲門（顏色守門 3,078）→ stampvox overwrite 塗裝（placed 2,644）→ `船尾:end`。
- **結果帳**：936,276 vs 設計 936,276，缺 0、多 0、色差 0；1 元件、空腔 0。
- 過程圖：`overlays/stage4_before_astern.png`（改之前）、`stage4_stern_astern.png`、`stage4_stern_quarter.png`。
- ⚠ 看得到的：船尾頂端兩角舊 taffrail 的翹角從正後方看像兩隻角（4b 的 quarter galleries 會包住）；poop 前緣 x 215 是牆的斷面（之後放 poop 的 breastwork 與欄杆）。

## 船身拉長（2026-10-12 晚，Tim：「可以嘗試拉長船體嗎（船體中段複製拉伸）」＋截圖紅圈在船中）
設計 plan.json `stretch`；產生 `design/draft_stretch.py`（讀標記 `船尾:end`）⇒ `masks/stretch/block.vox.txt`、`verify_stretch.json`。
- 量接縫再挑段：接縫兩邊兩欄的右舷外緣逐 z 比 —— 66 格一段的（x 439、406、472 起）兩端船寬本來就差 1–3 格（439 起：z 70–100 差到 2、舷頂差 1；406 起：水線以上 −1 一整條、舷牆 −2，還多封 2 個空腔）；**33 格一段的 x 439..471 最平（每個 z 最多差 1、舷頂差 0）**⇒ 這一段**複製兩份**接在它後面（第 8／9 個砲門之間的中點到第 9／10 個之間的中點，含第 9 個砲門、兩層都有）。
- 落格：`拉長:begin` → `work sub=move region=472..1023,… delta=66,0,0` → stampvox block（59,065）at 33,0,0 與 66,0,0 → `拉長:end`。
- **結果帳**：1,054,406 vs 設計 1,054,406，缺 0、多 0、色差 0；1 元件、空腔 0；兩道接縫每個 z 外緣差 ≤ 1；船殼最前 x 742（以前 676）。
- 每舷砲門 15 → 17（兩層）⇒ 砲 82 → **90**（兩層各 32 門舷側＋船頭 2＋船尾 2、上甲板 18；憲法號的 1.67 倍）—— plan.json guns 已改。
- ⚠ 從上往下看（還沒鋪甲板）：船艙底的斜肋被複製成兩段斷開的斜線（鋸齒），鋪了甲板就看不到；之後照憲法號座標做的部件：x ≥ 472 ＋66、x 439..471 那一段再複製兩份。
- 過程圖：`overlays/stage_stretch_{side,top,bowq}.png`。

## 階段四b 船尾裝飾 —— 新圖紙 05（2026-10-12 晚）
設計 plan.json `stern_deco`；產生 `design/draft_stern_deco.py`（讀標記 `拉長:end`）⇒ `masks/deco/{quarter_gallery,stern_walk,stern_deco,lantern}.vox.txt`、`deco_placement.json`、`verify_stern_deco.json`、`sheet05_stern_deco_v1.png`。
- **組裝件** `basecamp-ember-01m-assembly`「餘燼號（組裝）」（0.1 m、1024×320×800）：關聯 `船殼`、`後廊-S`／`後廊-P`（mirror=y，at.y ＝ 321 − 203 − 11 ＝ 107）、`船尾陽台`、`船尾名牌`；模型 `lantern-C／S／P`。
- 子作品（parent 船殼、tags sub）：
  - `-quarter-gallery`（右舷一件、0.1 m、26×11×73、7,542 格）：貼船側外緣（y 203–206、x 103–125，收在上甲板第 1 個砲門 x 128 之前）；z 96–105 垂飾（往下收、金箍）、106–129 第一層（窗 114–124 琥珀 245＋金框、暗紅板 108–112）、130–132 金腰帶、133–149 第二層（窗 135–145）、150–160 暗紅冠＋金邊、金尖頂到 z 166。
  - `-stern-walk`（0.1 m、1,395 格）：後甲板艙那列窗外的陽台，平台 z 131–132、從船尾面 x 104 往後 6 格、|dy| ≤ 42、金欄杆每 3 格一根、扶手 z 139、5 個托架（z 126–130）；船尾角往前彎，平台邊緣 6 格碰到船殼 ⇒ 不放。
  - `-stern-deco`（0.1 m、170 格）：poop 那段船尾面寫 **EMBER**（5×7 字、金、z 151–157、凸 1；從船尾看觀者左手邊 ＝ −y ⇒ 字從 −y 往 +y 寫）＋兩邊火焰（橘 240、金、亮黃 252，|dy| 27）。
  - `-lantern`（**0.02 m**、41×41×80、57,284 格）：八角、琥珀玻璃、金框金箍、暗紅頂、金尖；左右對稱差 0。模型 scale 0.2 ⇒ 約 0.8 m 寬、1.6 m 高；3 盞站在 poop 頂 cap（z 160）上：中間、|dy| 36；meta `kind=lantern, light=amber`。
- 量：每件跟船殼重疊 0（stern walk 扣掉 6 格之後）、6 連通接到船殼、左舷鏡過去也不撞；組裝件 **1,071,055**、1 元件、空腔 0、link_overlap 0；**結果帳**（組裝件匯出 links=all vs 設計）缺 0、多 0、色差 0；models_broken 0。
- 圖紙第一版：gallery 的冠頂設到 z 161，船側只到 160 ⇒ 貼不上（KeyError 當場擋下）⇒ 冠 150–160。
- ⚠ plan.json 這一輪用 json.dump 整份重寫了（憲法號階段十的坑：之後只在尾巴接新段）—— 量過 git diff：刪 15 行、加 276 行（幾乎都是新段落，排版只動到 guns 那幾行）；內容沒丟（重跑產生程式結果帳都對得上）。
- 過程圖：`overlays/stage4b_stern_{astern,quarter}.png`、`stage4b_ship_sternq.png`。
- ⚠ 看得到的：船尾頂端兩角的舊 taffrail 翹角還在 gallery 冠旁邊露一點；燈籠是網格模型、觀測頁的光源不會從燈籠發光（只是琥珀色）。

## 階段五 甲板 —— 新圖紙 06（2026-10-12 晚）
設計 plan.json `decks_build`；產生 `design/draft_decks.py`（讀標記 `拉長:end`＋憲法號四件甲板子作品 links=none）⇒ `masks/decks/<層>.vox.txt`（世界座標）、`verify_decks.json`、`sheet06_decks_v1.png`。
- 做法：憲法號的甲板照船殼同一套換算搬過來（拉長：x 439..471 原地＋複製到 +33／+66、x ≥ 472 推 66）——
  orlop／berth／**下層砲甲板** ＝ 憲法號 orlop／berth／gun deck；**上層砲甲板** ＝ 憲法號 spar deck（高度不動，橫樑擱在船殼原有的 spar clamp 上）；**上甲板** ＝ 憲法號 spar deck ＋23；**poop deck** 新做。
  桅孔：之後桅也照 z 109 插 23 ⇒ 上層／上甲板的桅孔都對得上（不用重開）。房間（艙壁、艙房）這一階段不搬。
- 上甲板船腰打開（設計決定，74 砲的樣子）：x 372–580、|dy| < 36 拿掉（26,268 格），只留兩側 gangway（約 19 格寬）；開口兩側 104 欄杆（每 3 格一根、高 8）、quarterdeck 前緣與 forecastle 後緣 breastwork 頂金（共 1,894 格）。甲板面從甲板板量（船腰那段 z 127）。
- poop deck：z 148 甲板板（250）、橫樑每 16 格（136、2 寬 3 深）＋前緣一根；後桅孔 (203.25, 160) r 4（憲法號後桅 x_gun 206、傾 3.5°，餘燼號 z 148 ↔ 憲法號 z 125）；前緣欄杆 |dy| ≤ 5 留梯口。
- **第一版抓到的兩個錯**（都在落格前後由量測擋下）：
  ① 上甲板抬 23 之後，懸肘（104、z 114–123）貼的是憲法號 z 91–101 的牆，那段比插入段寬 4–5 格 ⇒ 5,434 格撞到船殼、**54 格露到船外** ⇒ 懸肘每格往內挪「原本那層外緣 − 現在這層外緣」（4,106 格挪了），之後露到船外 0；仍有 3,634 格（懸肘與橫樑端頭）嵌進牆、不放。驗證加了「露到船外」那一格。
  ② poop 前緣欄杆用 z 148 的空氣判斷可以放，但 z 149 以上是舊 cap rail／poop 牆 ⇒ **14 格插進船殼**；組裝件 stats 報 link_overlap 14 才發現（我的驗證只比了甲板對甲板）⇒ 引擎匯出每件子作品兩兩比、找到是 hull×poop ⇒ 產生程式不放撞船殼的格、驗證加「跟船殼重疊」，落了一刀 carvevox 刻掉那 14 格（顏色守門）。
- 子作品（parent 船殼、tags sub、0.1 m、1024×320×800、at 0,0,0）：`-deck-orlop` 52,858、`-deck-berth` 125,644、`-deck-lower` 151,440、`-deck-upper` 124,017、`-deck-spar` 96,023、`-deck-poop` 13,163；組裝件關聯 `甲板-orlop／berth／lower／upper／spar／poop`。
- 讀數：六層彼此重疊 0、跟船殼重疊 0、露到船外 0、鏡像差 0、每層都接到船殼；**每件子作品匯出 vs 清單逐格相同**（缺 0、多 0、色差 0）；組裝件 **1,634,200**、1 元件、空腔 0、link_overlap 0。
- 過程圖：`overlays/stage5_decks_{top,bowq,waist}.png`；新圖紙 `design/sheet06_decks_v1.png`。
- ⚠ 看得到的：上甲板橫樑在插入段的牆上沒有 clamp（直接靠內板）；房間、梯子、格柵還沒有。

## 補漆：船頭與轉角的帶子（2026-10-12 晚，Tim：「船頭可以補噴漆（有發現縫）」＋兩張截圖）
設計 plan.json `paint_fix`；產生 `design/draft_paint_fix.py`（讀標記 `拉長:end`）⇒ `masks/paint/paint_fix.vox.txt`、`verify_paint_fix.json`。
- 原因（我的錯）：階段三只塗「每個 (x, z) 往外最遠那一格」—— 船側對，船頭朝前（+x）的面看得到的是每個 (y, z) 最前面那一格，沒塗到 ⇒ 帶子被一條條黑直條切開。
- 改法：x ≥ 125 的黑外板（36）只要有一面貼著船外的空氣（外框外擴 1 格、從角落 flood）就算表面；帶的上下緣照每一欄已塗紅的高度（兩條帶各自；船頭最尖那 3 欄借鄰欄）⇒ 帶內 → 暗紅、上下各一格 → 金。260 格（暗紅 172、金 88；x 700 以上 228）、鏡像差 0。
- 先量了一次「從正前方看帶子高度裡的黑」：在它那一欄帶子範圍內、朝前的黑格 100 個 ⇒ 都在這 260 格裡。
- 落格：`補漆:begin` → stampvox overwrite（placed 260）→ `補漆:end`；**結果帳** 1,054,406 vs 設計，缺 0、多 0、色差 0。過程圖 `overlays/paintfix_bow_{before,after}.png`（正前方）、`paintfix_bowside_after.png`。
- ⚠ 中線那根艏柱沒塗（兩條帶在那裡斷開）：之後做船頭的 knee 與 cheeks 會包住它，帶子接到 cheeks 上。

## 階段六 桅杆 —— 新圖紙 07（2026-10-12 晚）
設計 plan.json `masts_build`；產生 `design/draft_masts.py`（憲法號四件桅杆子作品的格＋models.json＋anchors.json）⇒ `masks/masts/<桅>.vox.txt`、`masts_placement.json`、`verify_masts.json`；下 CLI `design/tools/masts_apply.py`。
- 三根桅照船殼同一套換算：x 照拉長（前桅 x 566–608 全在 472 以後 ⇒ +66）、z 109 插 23（複製 z 108 那一層：前 56／主 61／後 28 格）⇒ 下桅加長 23、上面全部抬 23。艏斜桅（x 594–958）整根 (+66, 0, +23)，對準船殼跟著抬高的開口；尖端到 x 1024 ⇒ 組裝件與艏斜桅子作品放寬到 **1100**。
- 帆桁：模型來源照舊是**憲法號的 -yard-* 子作品**（同一件做一次）；at 照換算、meta 照抄；固定點照換算（名字不變）。
- spanker boom（設計決定）：抬 23 之後 jaws z 157 會穿過船尾中間那盞燈籠（z 161–177、x 95.6–103.4）、離 poop deck 0.6 m ⇒ 再抬 6、沿 x 縮 0.48（尾端 x 110.6；長約 9 m）。模型外框 x 110.6–201.8、z 162–175。
- 子作品（parent 船殼、tags sub、0.1 m）：`-mast-fore` 23,020、`-mast-main` 28,887、`-mast-mizzen` 12,336、`-bowsprit` 11,394（1100 寬）；模型 4／4／6／1、固定點 36／34／26／6；組裝件關聯 `前桅`、`主桅`、`後桅`、`艏斜桅`。
- 讀數：四件跟組裝件現況（船殼＋甲板＋裝飾）重疊 0（每一層的桅孔都對上）、彼此重疊 0、鏡像差 0；**每件子作品匯出 vs 清單逐格相同**；帆桁模型的 309 個點 vs 憲法號同名點：剛好 (+66 或 0, 0, +23)、差 0（boom 另算）、meta 相同、狀態全 ok；組裝件 **1,709,837**、1 元件、空腔 0、link_overlap 0、models_broken 0。
- 過程圖：`overlays/stage6_masts_{side,bowq,sternq}.png`。⚠ 用 region 裁的近照不能拿來看帆桁（region 只裁格子、模型照畫）—— 那張刪了。
- ⚠ 還沒有：繩（靜索、ratlines）、帆、channels、fife rails；桅的固定點已照換算登記，繩索那一階段照名字接。

## 階段七 索具 —— 新圖紙 08（2026-10-12 晚）
設計 plan.json `rigging`；產生 `design/draft_rigging.py`（憲法號 channels／belaying-side／fiferails 子作品＋固定點、組裝件 ropes.json／sails.json、船殼固定點）⇒ `masks/rigging/{channels,belaying,fiferails}.vox.txt`、`rigging_placement.json`、`verify_rigging.json`；下 CLI `design/tools/rigging_apply.py <design> fittings|sails|ropes`。
- 換算：x 照拉長（點取原地那一份）；**channels**（掛在船殼外、chain plates 往下接）照船殼插 23（chain plates 跟著加長）；**pin rails、fife rails**（站在上甲板上）整件抬 23；繩端與帆角座標 z ≥ 109 抬 23。
- chain plates：在 z 108 避開的是下層砲門，往下複製 23 層之後從上層砲門前面穿過 —— 第一版量到 **26 個 (x, z) 欄**擋在上層開口前 ⇒ 那幾格不放（44 格），chain plate 在砲門處斷開、上下兩段都貼著船殼；之後擋在前面 0。
- 子作品（parent 船殼、tags sub、0.1 m）：`-channels`（一舷 7,355、at 150,161,70、512×80×67）、`-belaying-side`（一舷 919、at 120,161,123、579×80×40）、`-fiferails`（2,393、整件 at 0,0,0）；關聯 `channels`／`channels-鏡像`、`繫繩欄`／`繫繩欄-鏡像`（mirror=y、at.y 80）、`fife-rails`（掛在 -deck-spar 裡 ⇒ 路徑 `甲板-spar/fife-rails`，同憲法號）；固定點 31／63／56 照換算；船殼補 `mainstay-S／P`（726,170／150,155，落在實心上）。
- 繩 **739**（憲法號 901 扣：砲索 140、梯子 14、entry 4、舵輪 2 —— 那些部件還沒做；bobstays 2 —— 要船頭 knee）；帆 15（色 **#57524c 暖深灰**，設計決定）；風照憲法號 4.5,−1.5,0、4 秒。
- 量到的錯：
  ① 繩 739 條一次下，1 條（mizzen-shroud-P3.lanyard-a）IOException（檔案被佔用）⇒ 比對清單找出來補跑。
  ② **座標寫法**：第一版用 %g，憲法號寫 `118.00` 的變成 `141` ⇒ 引擎把整數當格心、多 0.5 格（跟憲法號比 18 條 lanyard 量到 +0.5）⇒ 每個分量照原本的寫法（原本帶小數 ⇒ %.2f、原本整數 ⇒ 整數），122 條字串變了、重下。
  ③ 產生程式的驗證要「加配件之前」的組裝件，套用之後重跑被斷言擋下 ⇒ 改成藏起這一階段的 5 條關聯再匯出。
- 讀數：配件跟組裝件重疊 0、彼此 0、接到船殼；組裝件 **1,728,778**、1 元件、空腔 0、link_overlap 0；繩 739、broken 0、子繩 328；帆 15、broken 0。
  **跟憲法號逐條比**（引擎讀數的兩端座標）：470 條剛好 (0, 0, +23)、264 條剛好 (+66, 0, +23)；5 條 stay（主桅 → 前桅）一端 +0 一端 +66（船拉長、長 +52～+65，預期）。帆 14 面四角剛好平移、鼓度逐位相同（main course −96.51）；spanker 下緣跟著改短的 boom（clew +92.6／+29、tack +5.2／+29），鼓度 20.35 → 20.79。
- 過程圖：`overlays/stage7_rigging_{bowq,side,sternq}.png`。
- ⚠ 還沒有：砲與砲索、梯子、entry port、舵輪、船頭（bobstays）、房間、彈藥庫。帆是整片的（破帆要引擎支援開洞）。

## 階段八a 房間、艙壁與兩座梯子 —— 新圖紙 07（2026-10-13）
設計 plan.json `rooms_build`；產生 `design/draft_rooms.py`（讀組裝件現況 links=all＋憲法號 rooms／ladders 子作品）⇒ `masks/rooms/*.vox.txt`、`rooms_placement.json`、`verify_rooms.json`、`sheet07_rooms_v1.png`；落格 `design/tools/rooms_apply.py`。
- 換算：房間與艙壁都在 z < 109、**沒有一格落在拉長那一段 x 439..471**（量過 0 格）⇒ 純平移（x < 439 不動、x ≥ 472 推 +66），不插層、不複製。
  梯子一座一座整座搬（26 連通一塊 ＝ 一座）：berth 3 座（x 223／307 不動、602 起的 +66）、下層砲甲板 4 座（307 不動、440..455 兩座**原地**（拉長那一段的照「點只取原地那一份」，另外兩份複製出來的艙口沒有梯子）、601 起的 +66）。照逐格換算的話 440..455 那兩座會變成六座。
- 沿用（Tim：子物件能重複用就重複用）：berth 與下層砲甲板的**舷側艙房整件都在 x < 439** ⇒ 換算後跟憲法號逐格相同 ⇒ 直接關聯憲法號的 `-rooms-berth-side`、`-rooms-gun-side`（艦長室那一側），不另做一份。
- 新子作品（parent 船殼、tags sub、0.1 m）：`-rooms-orlop-bulkheads` 3,260、`-rooms-orlop-side`（473×52×20，一舷）8,161、`-rooms-berth-bulkheads` 7,248、`-ladders-berth` 788、`-rooms-lower-bulkheads` 3,888、`-ladders-lower` 1,084。
  關聯掛在各層甲板子作品底下（同憲法號）：`甲板-orlop/艙壁、艙房、艙房-鏡像`；`甲板-berth/艙壁、艙房、艙房-鏡像、梯子`；`甲板-lower/艙壁、艙房、艙房-鏡像、梯子`。鏡像那一件 at.y 照憲法號（框 y 52 ⇒ 168 ↔ 101）。
- 讀數：新格 45,652；跟組裝件現況重疊 0、彼此 0、露到船外 0、鏡像差 0、都接到船殼；組裝件 **1,774,430**、1 元件、空腔 0、link_overlap 0、link_clipped 0；**結果帳**（組裝件重新匯出 vs 設計）缺 0、多 0、色差 0。
- ⚠ 第一版「露到船外」判錯 64 格（艦長室 48、梯子 16）：那幾層是砲門，牆是開通的，那一列只剩中線的柱子（|dy| 0、9）⇒ 只看同一層的外緣會把船艙裡的東西判成在船外。外緣改成上下 ±12 層裡最寬那一層（艦長室那幾格在 |dy| 24，真的船牆在 52 上下）。
- 還沒有：新梯子（上層砲甲板 → 上甲板、上甲板 → poop）、上甲板 clamps、砲具（跟砲一起）。

## 階段八b 新梯子、扶手繩、上甲板 clamps —— 新圖紙 08（2026-10-13）
設計 plan.json `ladders_build`、`clamps_build`；產生 `design/draft_ladders.py`（找位置的 edges／shape／try_one 照抄憲法號 draft_ladders.py）、`design/draft_clamps.py`；落格 `design/tools/ladders_apply.py`；空腔 `design/tools/fill_cavities_asm.py`。
- 甲板面（甲板板最上面那格 ＋1，同憲法號的定義；從甲板子作品中線量過）：上層砲甲板 106／105／108／110、上甲板 129／128／131／133（＝ 憲法號 spar ＋23）、poop 149。上層 → 上甲板的高差 23 ＝ 憲法號 gun → spar 的高差。
- **新梯子 3 座**：上層砲甲板 → 上甲板 after（x 307 → 323）、fore（683 → 667），位置剛好是憲法號 after-gun／fore-gun；上甲板 → poop（poop 前緣 x 216 → 227，前緣欄杆留的梯口 |dy| ≤ 5）。子作品 `-ladders-upper`（掛 `甲板-upper/梯子`，568 格）、`-ladders-spar`（掛 `甲板-spar/梯子`，200 格）。船腰那一對不做（上甲板船腰是開的）。
- **扶手繩**：新梯子 3 座 × 2 條；階段八a 搬來的兩件（berth、lower）補固定點與繩 —— 憲法號梯子子作品的 28 個固定點照整座平移換算，**每一個都落在那座梯子的鐵柱格上**（換算對的讀數）。共固定點 40、繩 20（組 `ladders/manropes`），20 條 ok、broken 0；8 條憲法號同名的長 22.07 ＝ 憲法號。
- **上甲板 clamps**：憲法號 spar clamp（色 136、高 2、內板往船艙裡一格；x 112–652）照 x 拉長、z ＋23 ⇒ x 112–718、z 122–128 依甲板分段。⚠ 不是複製憲法號的 clamp 格：插入段的牆是 z 108 那層複製的，位置跟憲法號 z 99–100 不一樣 ⇒ 照餘燼號自己的內板（177）重生。2,390 格（12 格撞到組裝件現有的格、不放；撞到的是哪一件沒查）、鏡像差 0、每格都貼內板。落進船殼，標記 `上甲板clamp:begin／end`。
  第一版斜接規則把 6 格補在內角（往船艙凸的疙瘩，「貼內板」那格量到 6）⇒ 斜接只補貼著內板那一側。
- **空腔**：clamp 放上去之後組裝件多了 14 個封閉空腔（32 格，1–5 格；補的顏色全是懸肘的 104 ⇒ 至少有一面是懸肘，橫樑跟 clamp 同色 136、分不出有沒有參與）—— 好幾件一起圍的，憲法號那支 fill_cavities 只量單件 ⇒ 新寫一支量組裝件的（顏色規則同那支：6 鄰居多數，同票 141）；32 格全是 104（懸肘色）、鏡像差 0，落進船殼。
- 讀數：組裝件 1,775,198（梯子）→ 1,777,588（clamp）→ **1,777,620**（補空腔）、1 元件、空腔 0、link_overlap 0。

## 階段八c 船長室（自由設計）—— 新圖紙 09（2026-10-13，Tim：「房間也自由發揮吧」）
設計 plan.json `cabin_build`；產生 `design/draft_cabin.py`（讀組裝件藏起 `甲板-spar/船長室`）⇒ `masks/cabin/great_cabin.vox.txt`、`verify_cabin.json`、`sheet09_cabin_v1.png`。子作品 `-great-cabin`（7,458 格），掛 `甲板-spar/船長室`。
- 位置：poop 底下（上甲板面 129 → poop 甲板板 148，淨高 1.9 m；半寬 4.2–4.6 m；船尾面 x 97–104；後桅 x≈203 從中間穿過）。兩舷 z 138–146 有砲門 ⇒ 不做靠舷的隔間。
- 配置（船尾 → 船頭）：船尾窗下一整排長椅（後緣貼船尾肋骨、前緣拉直）→ 大艙：長桌 x 118–148（3 m）、12 張椅子、桌子上方吊**「餘燼之心」**（金籠 5×5×7、琥珀火芯 3×3×3，金十字＋金桿把火芯、籠子、吊鍊接成一塊）→ 隔間 x 166（拱口 |dy| ≤ 9）→ 走道兩側右舷臥艙（一張床）、左舷海圖室（桌子＋攤開的海圖＋椅子），艙門 x 180–184、艙的前牆 x 193 → 玄關（後桅＋它的 fife rail）→ 前艙壁 x 215（poop 前緣橫樑底下），poop 梯子兩側各一扇門。
- 配色：同憲法號房間（177 淡木板、136 深木框、每 8 格一根壁柱、頂上一條金 248）＋暗紅 128、琥珀 245／252。
- **套用了三版**（7,522 → 6,984 → 7,458 格；每一版都是看了讀數或圖才改的；⚠ 提交 f627d7d 的訊息把長椅寫成第三版，先後錯了 —— 長椅是套用前就改的）：
  ⓪ 套用前：長椅第一版每列各自往前 3 格 ⇒ 前緣鋸齒（船尾肋骨凹凸）⇒ 前緣拉直。
  ① v1 整艘 7 塊：餘燼之心的火芯與籠子各自浮著（籠子只有稜、吊鍊掛在空氣上）；艙壁在 poop 上方露天那幾層從中線走到 70 格外，在船外長出四條（z 161–168）⇒ 加金十字與金桿；艙壁只放頭上有 poop 甲板的格。
  ② 側面圖量到走道牆在 x 195–197 頂只到 136 ⇒ 是後桅的 **fife rail**（階段七從憲法號開放的 quarterdeck 搬來，被 poop 罩在這裡，x 195–214、|dy| ≤ 15、z 129–141），v1 的前艙壁 x 213 也穿過它 ⇒ v2：艙的前牆退到 x 193、前面留玄關；前艙壁移到 x 215，門改成 poop 梯子兩側兩扇。
- 讀數：7,458 格、跟組裝件重疊 0；組裝件 **1,785,078**、1 元件、空腔 0、link_overlap 0。過程圖 `overlays/stage8c_cabin_only_{a,b,side,fwd}.png`。
- ⚠ 待決定：後桅 fife rail 在 poop 底下（船長室玄關裡）—— 實船應在 poop 甲板上。搬上去只要動它和它身上 13 個固定點：**沒有任何一條繩綁在它上面**（2026-10-13 查組裝件 ropes，mizzen-fife／mizzen-bitt 0 條）。⚠ 回報 Tim 時我說「要連帶重綁後桅動索」是推的、錯的。

## 階段九 船頭：knee、cheeks、trailboard、火焰紋章、hawse、head rails、cathead、錨、船首像 —— 新圖紙 10／10b（2026-10-13，Tim：「繼續造船吧 GO」）
設計 plan.json `head_build`；產生 `design/draft_head.py`（憲法號 draft_head.py 照換算改寫；曲線現讀憲法號 plan.json `head`）、`design/draft_figurehead.py`（原創）⇒ `masks/head/{knee,side,figurehead}.vox.txt`、`knee_anchors.json`、`anchor_pick.json`、`verify_head.json`、`verify_figurehead.json`、`verify_head_ledger.json`、`sheet10_head_v1.png`、`sheet10b_figurehead_v1.png`；落格 `design/tools/head_apply.py`、結果帳 `design/tools/head_ledger.py`。
- 換算（設計決定）：x ＋66；z ≤ 63 不動、63..131 線性拉到 63..154（×91/68）、≥ 131 ＋23 —— 船殼在 z 109 插了 23 層，knee 照搬會在插入段那 23 層變成一段直的 ⇒ 整片 knee 跟著船頭變高（比憲法號更直立）。連續、單調；cheeks、卷草、hawse、rails、cathead 的 (x, z) 都走同一個換算，貼表面的照舊從餘燼號自己的外殼算。
- 配色：憲法號的白 → 金（cheeks、卷草、rails、head timbers）；盾牌 → 火焰紋章（金框、亮黃、橘、暗紅火心，x 759、z 109）；hawse 圈 v1 照抄鐵灰 146，貼在暗紅帶上像兩個字母（圖紙量到）⇒ 金圈＋圈裡一層黑當孔。billethead 不做 ⇒ 船首像。
- **船首像「浴火的鳳凰」**（原創；kiara 的 `kiara-ember-phoenix` 是立在石台上的雕像、有台座與小燈、1 m＝32 格 ⇒ 不拿來當船首像）：身體趴在 knee 尖端（790, 154）往前上方傾、頭在艏斜桅底下（喙尖 x 813、艏斜桅底 z 175 那裡頭頂 171）、翅膀往後上方張開、尾羽是順著 cutwater 往下流的火舌（黃 → 橘 → 紅 → 暗紅，停在 bobstay 固定點上面）。每個部位是膠囊／球、|dy| 對稱。
  v1 翅膀是一把分開的羽毛棒 ⇒ 鳳凰自己散成 31 塊、浮空 48 格 ⇒ v2 改成一片羽膜（平面過肩、翼尖、後下角；外緣那圈每根羽毛中間留、兩根之間切掉 ⇒ 羽尖），脖子縮短、頭放大 ⇒ 浮空 0、鏡像差 0。撞到現況不放：身體 165（埋進 knee 頂與 rails 尖）、尾 22、翅 14。
- 錨：**直接關聯憲法號的 `-anchor`**（Tim：子物件能重複用就重複用）；掛法同憲法號（ring 頂貼 cathead 端那格正下方、兩舷都不撞）⇒ 第一個候選就過：cathead (721, 205, 152)、錨-S at 698,189,95、錨-P at 698,99,95 mirror=y（憲法號 630,189,73 ⇒ 差 (+68, 0, +22)）。
- bobstay：憲法號 knee 的 bobstay-1／2（707,96）（713,104）照換算 ⇒ knee 中線那一層最前面那格 (772,160,107)、(780,160,118)；組裝件 bobstay-1／2 → 艏斜桅同名點（長 79.26／85.8，ok）。第一次拉 bobstay-1 IOException（檔案被佔用，同階段七）⇒ 重跑工具補上。繩 761、broken 0。
- 子作品（parent 船殼、tags sub、0.1 m）：`-head-knee` 7,091（全黑）、`-head-side`（一舷，120×64×110 at 696,161,70）3,521（cheek 776、hawse 196＋孔 39、紋章 37、卷草 255、cathead 139、rail-top 418、rail-main 470、panel 1,093、timber 98）、`-figurehead` 1,717；組裝件關聯 `船頭-knee`、`船頭裝飾`、`船頭裝飾-鏡像`（at.y 96）、`船首像`、`錨-S`、`錨-P`。
- 讀數：組裝件 **1,803,208**（＝ 1,785,078 ＋ 7,091 ＋ 2×3,521 ＋ 1,717 ＋ 2×1,140）、1 元件、空腔 0、link_overlap 0、models_broken 0；鏡像差 151／955／10 跟這一階段之前一樣（船長室與 EMBER 名牌）⇒ 這一階段沒有新增不對稱；**結果帳**（組裝件匯出 vs 設計）缺 0、多 0、色差 0；產生程式套用後重跑，三份清單逐位元組相同。
- 過程圖：`overlays/stage9_head_{bowq,bowq_port,side,front}.png`、`stage9_figurehead_close.png`（ropes=0 models=0 才是真的特寫）。
- ⚠ 看得到的：hawse 金圈在暗紅帶上仍有點像字；panel（兩道 rail 之間的黑板）貼在船殼黑外板上幾乎看不見。

## 階段十 砲 90 門（全部外部模型）—— 新圖紙 11（2026-10-13，Tim：「測試ok 單層提交吧 然後繼續」）
設計 plan.json `guns_build`；新砲 `design/draft_gun32.py` ⇒ `masks/guns/long32.vox.txt`、`guns_points.json`；擺法 `design/place_guns.py` ⇒ `guns_placement.json`、`verify_guns.json`；落格 `design/tools/guns_apply.py`。
- 配置：下層砲甲板 舷側 16 門／舷 ＝ **新做的 32 磅長砲** `-gun-long32`（0.05 m、31×74×31、8,393 格；憲法號 draft_guns2.py 的 long18 照口徑放大：外徑 ×1.2、砲身 58 格 ＝ 2.9 m、carriage 1.75×1.05 m、軸離甲板 1.125 m；⚠ 推算）；上層砲甲板 舷側 16 門／舷 ＝ 憲法號 `-gun-24`；上甲板 carronade 9 門／舷 ＝ 憲法號 `-gun-carronade32`（第 4–12 個砲門；1–3 在 poop 底下的船長室，不放）；追擊砲 ＝ 憲法號 `-gun-long18`：兩層各一對船頭（第 17 個砲門）＋一對船尾（transom 的砲門）。合計 32＋32＋18＋8 ＝ **90**。
- 砲門從餘燼號船殼量（|dy| ≥ 10 沒有船殼格、上下都有牆）：下層、上層各 17／舷，上甲板 12／舷 —— 跟 plan 的數一致（程式斷言）。
- 擺法（憲法號 place_carronades／place_chase）：從舷牆外面沿砲身往裡退（每步 0.5 格），退到模型每一格的格心＋八個角都不在組裝件實心格裡；追擊砲另外搜角度。模型掛在所在甲板的子作品（`甲板-lower／upper／spar/<名>`），P 舷一律 mirror=y（eye-aft／eye-fwd 不前後對調）、S／P 各自搜。meta：32l／24l／32c／18chase。
- 擺的過程量到的錯：
  ① -gun-24 的 pivot 照憲法號寫 (0,0,0)（砲尾）⇒ 搜尋從「pivot 在舷牆外面」開始退、第一步整門砲就在船外不撞 ⇒ 幾門砲口伸出 31 格（浮在船外）⇒ pivot 改砲架前緣 (7.5, 19.5, 0)（量 -gun-24：z ≤ 4 的格 y 最大 19）。
  ② 甲板高從「船殼面往裡 d 格那一欄」取：v1 兩舷用同一個式子 ⇒ P 舷多往裡 1 格（格 y ↔ 320 − y 跟連續面差一格）⇒ 船頭 P 舷甲板讀低 1、陡的角度全撞 waterway（136）⇒ 改 S ＝ outer − d − 1、P ＝ outer ＋ d；之後 45 對兩舷 at 逐對對稱（at.y 和 ＝ 321）。
  ③ 允許抬高 1 格之後，搜尋把「砲口伸得出去」排在「貼著甲板」前面 ⇒ 16 門 carronade 浮高 1 格 ⇒ 排序改成先貼甲板；之後 90 門 dz 全 0。
- 讀數：90 門、彼此不撞、兩舷逐對對稱；退 下層 32 磅 3.5–9、上層 24 磅 4.5–6.5、carronade 5–6；**砲口伸出船殼外面** 32 磅 2–7.5、24 磅 5.5–7.5、上層追擊砲 船頭 2.81（±30°）／船尾 6.62（±80°）。
  ⚠ 沒伸出去的（照實記，都貼著甲板）：**下層船頭一對**（±15°）縮在砲門裡 3.49 —— 抬高 1 格才能到 ±35° 齊平（v1 那樣），不浮空 ⇒ 留著；**下層船尾一對**（±85°）縮 2.02 —— 船尾內板（177、141，x 117–123、z 85–91）夾住；**carronade** 齊平到縮 1 格（憲法號階段二十九也是）。
- 模型：甲板-lower 36、甲板-upper 36、甲板-spar 18；組裝件模型 108（18 ＋ 90）、models_broken 0；每門模型的 work／at／rotate／mirror／scale／pivot／meta 跟擺放表逐門比 0 不符。voxel 不變（模型不是格）。
- 套用時 IOException（無法移除要被取代的檔案）兩門、重跑又兩門（都是已寫進去的那兩門 overwrite）—— 今天第三個階段遇到，另開工作卡。
- 過程圖：`overlays/stage10_guns_{side,lower,upper,spar}.png`。
- 還沒有：砲索與砲具（breeching、tackle、train、船牆的環、rammer／sponge）—— 下一階段；彈藥庫。

## 水線抬高 z 63 → 71（2026-10-13，Tim：「船變高了 船底水線是否也要往上一點(用噴漆模式往上噴塗?)」）
設計 plan.json `waterline_raise`、`head_build.knee_copper_below`；產生 `design/draft_waterline.py`（讀標記 `上甲板clamp:end`）⇒ `masks/paint/waterline.vox.txt`、`verify_waterline.json`；knee 由 `draft_head.py` 重產 ⇒ 差異 `masks/head/knee_waterline.vox.txt`；結果帳 `design/tools/waterline_ledger.py` ⇒ `verify_waterline_ledger.json`。
- 先量：船底的銅（168）＝ 外板最外 1–2 格（跟上面的黑外板 36 同一層），z ≤ 62；水線一直照憲法號 62.86、水平。
- 設計決定 ＋8 格（0.8 m）：多一層砲甲板、拉長 66 格 ⇒ 吃水應該更深；下層砲門下緣（船中約 z 89）離水面 2.6 m → 1.8 m（74 砲約 1.5 m）。
- 做法：用換色清單（stampvox overwrite，同階段三與補漆）而不是 spray —— 清單可以逐格對結果帳。z 63–70「貼著船外空氣的黑（36）」＋同層相鄰也是 36 的那一格（外板 2 格厚處）→ 銅：19,180 格（第一格 10,670、第二格 8,510；每層 2,188–2,502，z 62 現有的銅 2,022）；鏡像缺 0；換完 z 63–70 外表剩下的黑 0。knee z 63–70 → 銅 150 格。
- 落格：`水線:begin` → stampvox overwrite（placed 19,180）→ `水線:end`；-head-knee stampvox overwrite（placed 150）。
- **結果帳**：船殼現在 vs（上甲板clamp:end ＋ 換色清單）缺 0、多 0、色差 0；knee 子作品 vs knee.vox.txt 缺 0、多 0、色差 0。組裝件 1,803,208（不變）、1 元件、空腔 0、link_overlap 0、鏡像差 151／955／10（不變）。產生程式重跑 sha256 相同。
- 過程圖：`overlays/stage11_waterline_{side,bowq}.png`（之前的樣子 ＝ `stage10_guns_side.png`）。
- ⚠ 還沒有舵（憲法號有 -rudder；餘燼號還沒做）—— 做的時候水線也照 71。

## quarter gallery 開窗（2026-10-13，Tim：「窗戶部分可以直接開孔 這樣可以看到內部結構」）
設計 plan.json `gallery_open`；產生 `design/draft_gallery_open.py` ⇒ `masks/gallery/{gallery_carve,hull_carve}.vox.txt`、`verify_gallery_open.json`、`verify_gallery_open_ledger.json`。
- 先量：船尾窗、後甲板艙那列窗本來就是開的（看得到船艙）；填滿的只有 quarter gallery 的窗 —— 琥珀玻璃（245）一層 330 格，而 gallery 子作品（7,542 格）是**實心的黑塊** ⇒ 只拿掉玻璃，看進去是黑的。
- 改法（設計決定）：① 玻璃全拿掉 ② 上下兩層掏空成小房間（只拿掉六個鄰居都是 gallery 的格、z 在那一層地板與天花板之間 ⇒ 牆留 1 格）：下層 1,845、上層 1,834 ③ 背後各開一道門（實船 quarter gallery 從船長室進去）：門 x 111–117、下層 z 107–121（通上層砲甲板船尾）、上層 z 130–144（通船長室）；gallery 的背牆 210 格 ＋ 船殼一路刻到碰到空氣 964 格（141 544、177 420；兩舷逐格對稱）。
- v1 量到的：門底那一排後面是上層砲甲板的 waterway（7 格擋住）、上層門角後面擋 1 格 ⇒ 門 15 高、下層從 107 起；下層門頂到 121（上甲板 clamp 從 122 起，不切）。第一次只刻了船殼、gallery 掏空留下的背牆還擋在門上 ⇒ 補刻背牆。之後每道門後面擋住 0。
- 落格：gallery carvevox（顏色守門）4,219；船殼 `窗廊門:begin` → carvevox 964 → `窗廊門:end`。
- **結果帳**：gallery 現在 3,323 ＋ 刻掉 4,219 ＝ 原本 7,542、兩份不重疊；船殼 vs（窗廊門:begin − 清單）缺 0、多 0、色差 0。組裝件 **1,793,806**（＝ 1,803,208 − 2×4,219 − 964）、1 元件、空腔 0、link_overlap 0、鏡像差不變。
- 過程圖：`overlays/stage12_gallery_{sternq,close,inside}.png`（inside ＝ 藏 poop 甲板從船長室看那道門）。

## 階段十二 砲具與砲索 —— 新圖紙 12（2026-10-13，Tim：「然後繼續」）
設計 plan.json `gunfittings_build`；產生 `design/draft_gunfittings.py`（憲法號 draft_gunfittings.py 改寫成兩層；import place_guns 算砲模型的格與固定點）⇒ `masks/gunfittings/{lower,upper}.vox.txt`、`gunfittings_points.json`、`gun_ropes.json`、`verify_gunfittings.json`；落格 `design/tools/gunfittings_apply.py`（IOException 自動重試 3 次）。
- 只做兩層長砲（下層 32 磅、上層 24 磅，各 16 對）；carronade 與追擊砲不掛（憲法號也只掛長砲）。45 對砲兩舷對稱 ⇒ 每層一件一舷子作品＋mirror=y 關聯（同憲法號）：`-gunfittings-lower`（590×80×26 at 160,161,78）、`-gunfittings-upper`（590×80×28 at 160,161,104），關聯 `甲板-lower|upper/砲具`、`砲具-鏡像`（at.y 80）。
- 牆從船殼量（環要釘在船殼上）；擋不擋從「組裝件 ＋ 90 門砲模型的格」量（模型不在 voxel 匯出裡 —— 不加進去的話繩會穿過隔壁的砲而量不到）。
- 讀數：下層 1,221 格（環 63、甲板環 14、garland 302＋砲彈 74、rammer 408、sponge 360）、上層 917 格（環 64、甲板環 16、garland 306＋砲彈 75、rammer 228、sponge 228）；船牆環 64 個全部 offset 8（下層第 2 門船頭側除外）；跟現況重疊 0、鏡像那一舷重疊 0、浮空 0。
  繩 316（breeching 128、tackle 128、train 60），組 guns/{breeching,tackle,train}；端點 `model:甲板-<層>/<砲>/<點>` → `甲板-<層>/砲具[-鏡像]/<環>`。
- 沒放的（照實記）：下層第 2 門（艦長室側艙，同憲法號）船頭側的環牆上放不下 ⇒ 釘在艙房隔牆朝砲的那一面 (227, 205, 91)（憲法號是 (227, 189, 91)）；下層第 2、16 門甲板環找不到位置 ⇒ train 不掛；garland 兩層各 13 條（第 2–3、14–15 門之間放不下）；rammer／sponge 下層 26 支、上層 16 支 —— 上層第 7–12 門頭上是打開的船腰（沒有天花板可掛）、第 1、16 門頭上不平。
  第一次跑隔牆那條路丟例外（砲中線那一欄是砲門開口、沒有牆 ⇒ None）、輸出被我導到 /dev/null 沒看到、讀到的是上一次的 verify ⇒ 改取附近的牆、看 rc 再讀。
- 套用：420 筆、0 失敗、IOException 自動重試 5 次（TASK-0534 的讀數）。
- 讀數：組裝件 **1,798,082**（＝ 1,793,806 ＋ 2×(1,221＋917)）、1 元件、空腔 0、link_overlap 0、鏡像差不變；繩 1,077（761 ＋ 316）、broken 0；兩件子作品匯出 vs 清單逐格 0 差；產生程式套用後重跑，四個檔 sha256 相同。
- 過程圖：`overlays/stage12_fittings_{lower,upper}.png`（target＋zoom 才是真的近照；region 只裁格子、模型照畫）。

## 階段十三 entry port 與 side steps —— 新圖紙 13（2026-10-13，Tim：「然後繼續」⇒ todo「entry port 跟著上甲板抬高」）
設計 plan.json `entry_build`；產生 `design/draft_entry.py`（憲法號 draft_entry.py 新圖紙 23 v1.1 照換算；擋不擋含砲模型的格）⇒ `masks/entry/side.vox.txt`、`entry_anchors.json`、`entry_ropes.json`、`verify_entry.json`；落格 `design/tools/entry_apply.py`。
- 開口：船殼本來就有（憲法號的 entry port 跟著 z ≥ 109 抬 23）：x 374–382 從 z 132 開到 cap rail；z 130–131 兩層牆（72 格）留著當門檻（上甲板面 129 ⇒ 0.2 m；憲法號也是 waterway 當門檻）⇒ 不刻。
- 踏階：水線抬到 71 之後，z 74 起每 4 格一道到 126 ⇒ **14 道**（憲法號 10 道 66–102）；x 375–381、凸出 2（外面齊平、每一欄從那一欄的船殼外面貼上去：船殼外緣 y 226 → 215，船身往上收）；最下一道 x 374–382、凸出 4（v1.1：man rope 下端埋在外側兩角）。色 104。跨過兩條暗紅帶、在第 6／7 個砲門之間。
- 柱：鐵 146，立在開口兩側 cap rail 最外那一格（y 216，頂 z 146／147）上、頂 z 151（憲法號 128 ＋23）。
- man rope 每舷兩條：柱頂外面那一格 → 最下一道外側兩角；長 78.1、拉直；離實心（含砲模型）最近 0.39（在下端那一格旁）。
- 子作品 `-entry-side`（11×15×78 at 373,216,74；229 格：踏階 220、柱 9）；組裝件關聯 `舷梯`、`舷梯-鏡像`（mirror=y、at.y 90）；固定點 post-aft.top／post-fwd.top／step-1.aft／step-1.fwd；繩組 entry/manropes。
- 讀數：跟組裝件＋砲模型重疊 S 0／P 0；組裝件 **1,798,540**（＝ 1,798,082 ＋ 2×229）、1 元件、空腔 0、link_overlap 0、鏡像差不變；繩 1,081、broken 0；子作品 vs 清單 0 差；重跑 sha256 相同。
- 過程圖：`overlays/stage13_entry_{oblique,side}.png`。

## 階段十四 彈藥庫 —— 直接引用憲法號的前後兩間（2026-10-13，Tim：「繼續GO」⇒ todo「彈藥庫照兩層甲板重配（火藥桶引用憲法號的）」）
設計 plan.json `magazines_build`（沒有產生程式：只有兩條關聯）。
- 彈藥庫在 orlop 底下（z 23–41），那一層餘燼號跟憲法號一樣、只有拉長的平移 ⇒ 不重做，直接關聯憲法號的子作品（Tim：子物件能重複用就重複用）：
  `彈藥庫-後` → `basecamp-frigate-constitution-01m-magazine-aft` at 200,129,23（x 200–271 < 439，不動）；`彈藥庫-前` → `…-magazine-fore` at 587,110,26（憲法號 521 ＋66）。火藥桶模型（22／116）掛在它們裡面，一起來。meta 照憲法號：kind magazine、powder_lb 2200／11600；固定點 blast、door 跟著關聯走。
- 先量：放進餘燼號組裝件重疊 後 0／前 0、貼著現況的面 4,219／3,282（接得上）。
- 讀數：組裝件 **1,809,496**（＝ 1,798,540 ＋ 3,794 ＋ 7,162）、1 元件、空腔 0、link_overlap 0；模型 246（108 ＋ 138 個火藥桶）、broken 0。
- 鏡像差 151／955 → 1,336／1,017：多出來的 1,247 ＝ 兩間自己的鏡像缺（後 807、前 440）—— 憲法號那兩件本來就不對稱（後彈藥庫 y 129–190、中心 159.5，偏半格），不是擺錯。
- ⚠ powder_lb 是憲法號的量（桶數 × 100）；餘燼號 90 門砲沒有照比例加 —— 要不要多一間（例：74 砲的 hanging magazine）或加桶，等 Tim。
- 過程圖：`overlays/stage14_magazine_{aft,fore}.png`（船殼切在 orlop 以下）。

## 階段十五 舵（2026-10-13，Tim：「繼續GO」⇒ 水線那一階段記下的「還沒有舵」）
設計 plan.json `rudder_build`；產生 `design/draft_rudder.py` ⇒ `masks/rudder/waterline.vox.txt`、`verify_rudder.json`。
- 憲法號 -rudder（3,950 格）z 2–84 全在插層 z 109 以下、船尾不在拉長那一段 ⇒ 換算是恆等，位置照抄（at 0,0,0）；放進餘燼號組裝件重疊 0。
- 不直接關聯：水線抬到 71，那件 z 63–70 是黑 ⇒ 新子作品 `-rudder`（parent 船殼、tags sub、0.1 m）`work sub=assemble source_work=…-rudder at=0,0,0`（Credit 1，`work sub=show` 的 credit_count 讀到；Credit 是從編輯歷史產生、不寫在 work.json）→ stampvox overwrite z 63–70 的黑 → 銅 257 格（pintle 帶 136 的 68 格不動）。組裝件關聯 `舵`。
- 讀數：組裝件 **1,813,446**（＝ 1,809,496 ＋ 3,950）、1 元件、空腔 0、link_overlap 0、鏡像差不變（舵自己對稱，換色清單鏡像缺 0）；子作品 vs（憲法號的舵 ＋ 換色）逐格 0 差；重跑 sha256 相同。
- 第一次跑：產生程式要藏「舵」這條還沒掛的關聯 ⇒ 匯出被擋（hide_links 打錯名 ⇒ 擋）⇒ 先查現有關聯再藏（同其他產生程式）。
- 過程圖：`overlays/stage15_rudder_{side,quarter}.png`。

## 階段十六 軍官室（wardroom，自由設計）（2026-10-13，Tim：「接著繼續吧 GO」⇒ todo 可選項）
設計 plan.json `wardroom_build`；產生 `design/draft_wardroom.py`（擋不擋含上層砲模型的格）⇒ `masks/wardroom/wardroom.vox.txt`、`verify_wardroom.json`。子作品 `-wardroom`（4,617 格），掛 `甲板-upper/軍官室`。
- 位置：上層砲甲板船尾（地板 105、天花板 128）；先量：舷側砲架在 |dy| ≥ 23、船尾追擊砲 x 108–128、中線每 16 格的支柱（x 140／156／172／188，屬上甲板 `甲板-spar`）、後桅 x 200–206。quarter gallery 下層那道門通進這一間。
- 配置：前艙壁 x 232–233（第 2、3 門砲之間；砲索的環在 230／248，不穿），正中門 |dy| ≤ 4、高 18、136 門框；壁板 177、每 8 格 136 壁柱、頂一條金。中線長桌 x 144–184、|dy| ≤ 5、桌面 z 113（104）＋桌裙＋腳；**上甲板的支柱從桌面穿過**（撞到的 10 格不放 —— 實船的 wardroom 也是這樣）。兩側長椅 |dy| 8–9（暗紅椅墊 128、座 z 110、椅背 136 頂金）。桌子上方吊一盞小的「餘燼之心」（金籠 5×5×5＋琥珀火芯 3×3、籠頂金十字、2 格吊鍊）。
- v1 浮空 471 格（三處，都是落格前讀數擋下）：① 艙壁有幾欄頭上找不到天花板、上限當成 ＋30 ⇒ 長到上甲板上面（88）⇒ 找不到就不放、兩舷沒碰到牆也不放 ② 椅背從椅面上一層起、只有斜角相碰（312）⇒ 從椅面那一層起 ③ 吊燈籠頂正中是空的、吊鍊接不到籠子（71；船長室 v1 同一個錯）⇒ 籠頂金十字。之後浮空 0、鏡像差 0。
- 讀數：組裝件 **1,818,063**（＝ 1,813,446 ＋ 4,617）、1 元件、空腔 0、link_overlap 0、鏡像差不變；子作品 vs 清單 0 差；重跑 sha256 相同。
- 過程圖：`overlays/stage16_wardroom_{a,b,bulkhead}.png`（只畫船殼＋甲板-upper ⇒ 支柱藏起來、桌面看得到十字洞；燈從上往下看像擺在桌上，其實離桌面 0.8 m）。
- ⚠ 看得到的：艙壁頂那條金線照每一欄的天花板放 ⇒ 橫樑底下（125）跟甲板板底下（128）高低不齊、斷成兩段。

## 匯出給遊戲（2026-10-13）
- `op=export format=vxk include=rig,models,parts,meta` ⇒ `basecamp-ember-01m-assembly/exports/ember.vxk`（1.3 MB；exports/ 不進版控）：階段十五之後的組裝件 1,813,446 格、繩 1,081、帆 15、模型 246（網格 63 份）、關聯外框 49、帶 meta 248、固定點 1,465；引擎對拍「封裝回讀 ＝ 匯出的格子（逐格、逐色、checksum）」✓。⚠ 軍官室是之後才加的 ⇒ 要給 ame 前再匯一次。

## 階段十七 舵輪（2026-10-13，Tim：「繼續造船吧」⇒ 對照憲法號建造順序，只剩舵輪沒做）
設計 plan.json `wheel_build`；產生 `design/draft_wheel.py` ⇒ `design/wheel_placement.json`、`verify_wheel.json`；套用 `design/tools/wheel_apply.py`。
- 子物件重複用：憲法號 -wheel（雙舵輪，0.02 m、44,456 格）當外部模型 `舵輪` 掛在 `甲板-spar`（同砲的掛法），pivot (50,52,0)、scale 0.2、轉角 0 —— 跟憲法號同一組參數。
- 位置：後桅與船長室在 poop 底下（poop 前緣 x ≈ 212），中線 x 213–227 是上 poop 的梯子 ⇒ 放在梯子前面的上甲板中線（y 160.5）。搜法同砲：x 每 0.5 格試、z ＝ 腳下甲板頂 ＋ 1、模型每格格心＋八角縮 0.2 不落在「組裝件＋甲板-spar 的 carronade 模型」實心裡。
- v1 從 x 228 搜：第一個 0 碰撞在 x 235.5，外框後緣 226.4 正好堵在梯子落腳處（梯腳 x ≈ 225）⇒ 留 1 m 走道，從 x 246 起搜 ⇒ x 246 第一個就過。
- 讀數：at (246, 160.5, 128)、外框 (236.9,150.8,128.1)–(255.1,170.2,148.7)；腳印 24 欄正下方全是甲板（z 127）、外框正上方 0 格實心；舵索 2 條（#a08458、粗 0.35、組 steering）鼓輪 → 正下方甲板面，各長 9.9（同憲法號）。繩 **1,083**、ropes_broken 0；模型 **247**、models_broken 0；組裝件格數不變 **1,818,063**（模型不是 voxel）、1 元件、空腔 0、link_overlap 0。穿過舵輪外框的繩只有它自己那 2 條（直線近似）。重跑 sha256 相同。
- 過程圖：`overlays/stage17_wheel_{deck,close}.png`（hide_rope_groups=standing、sails=0）。

## 梯子給遊戲的點（2026-10-13，ame tavern 23321：預備水手爬梯子補砲班；Tim「叮」）
- 格式（ame 定、Tim 要求在模型裡用 meta 標）：梯子所在的關聯 meta `kind=ladders`；每座 4 個固定點登記在梯子子作品，名字 `<梯名>.foot／.lo／.hi／.head`，都取「腳踩的那一格」（地板或踏板上面第一格空氣）。梯名照扶手繩固定點 `manrope-<梯名>-…`。
- 算法 `basecamp-ember-01m/design/tools/ladder_points.py`：踏板 ＝ 兩條扶手之間的格（依 z 分階、兩格寬取靠梯子中段那格）；foot／head 沿梯子軸往外走，取第一段「連續 3 欄地板一樣高、上面至少 3 格空氣」的第一欄（艙口圍欄湊不成平地 ⇒ 跨過去）。v1 用「4..20 欄最常見的地板高度」⇒ fore-berth 被梯腳外 10 欄起一塊 z 66 的東西帶走、站不住 ⇒ 改成平地。
- 餘燼號 10 座（berth 3：after-berth、companion、fore-berth；lower 4：after-gun、fore-gun、waist-P、waist-S；upper 2：after-upper、fore-upper；spar 1：poop）⇒ 固定點 40、meta 4 個關聯；`verify_ladder_points_basecamp-ember-01m-assembly.json`。
- 讀回：`export format=parts` 的 kind=ladders 部件 4、四十個點的格心逐個 ＝ 算出來的 ＋0.5、差 0；格數 1,818,063 不變。after-berth 跟 ame 手量的參考差 1 格（foot 323 vs 324、head 304 vs 303）。
- 看得到的：fore-upper 的 head 頭上 1.0 m 是艏斜桅根部（憲法號 fore-gun 同）；poop 的 foot (227,160,129) 跟舵輪外框後緣隔 10 格。沒有梯子通 orlop（兩艘船都沒有）。
- 匯出 `exports/ember.vxk`：1,818,063 格、checksum 6a04b4a8、繩 1,083、帆 15、模型 247、帶 meta 252、固定點 1,509；封裝回讀對拍 ✓（含軍官室、舵輪）。
## 可選三項的收尾（2026-10-13，Tim：「然後繼續」）
### 船艙底斜肋重畫
設計 plan.json `riders_fix`；產生 `design/draft_riders.py` ⇒ `masks/riders/{carve,stamp,over_rider,refill_limber}.vox.txt`、`verify_riders.json`；套用 `design/tools/riders_apply.py`（船殼標記 `斜肋:begin／end`）。
- 原因：拉長是「一欄一欄」搬格子（x < 439 不動、439..471 三份、≥ 472 ＋66）⇒ 憲法號 12 根斜肋（live oak 104、6 對）裡，頭在船頭那 6 根（頭 x 519／535／554、尾巴伸到 424／443／465）跨過複製段，被剪成三截鋸齒。頭在船尾那 6 根整根在 x ≤ 408，沒動到。
- 修法：整根照頭搬（頭 ≥ 472 ⇒ 整根 ＋66）。＋66 是 33 的倍數 ⇒ 搬過去的位置是同一份船中剖面。憲法號的 limber（dy 6–12、內板 177 上面一格）讓開斜肋 ⇒ 斜肋搬走的位置補回 limber、搬來的位置蓋過 limber。
- 讀數：一欄一欄的 21,102 格 vs 整根的 16,774 格，已經對的 16,372；刻 4,480、補 limber 250、落 336（全是空氣）、limber 換斜肋 66；新落的浮空 0、鏡像差 0。船殼 1,051,720；組裝件 **1,813,919**（−4,144）、1 元件、空腔 0、link_overlap 0、鏡像差不變（1336／1017／10）。重跑（讀 `斜肋:begin`，組裝件 ＝ 現況 − 船殼現況 ＋ 船殼那一刻）四份清單與 verify sha256 相同。
- 過程圖：`overlays/fix_riders_{before,after}.png`（只畫船殼、z ≤ 75 從上往下看）。兩組斜肋中間空出來的那一段 ＝ 拉長多出來的船中。
### 軍官室艙壁頂金線
- v1 照每一欄的天花板放：中段（y 141–179，甲板板底下）在 127、兩旁 4 欄在 125、外側 126–127 被別的構件佔住而**沒有金線**（筆記寫的「125／128 斷兩段」不準：量了才知道外側整段沒有）。
- v2：plan `wardroom_build.gold_z` 125（每一欄都到得了的最高層），上面壁板 ⇒ 兩層艙壁各 87 欄、z 125 一條直線。格集合不變、換色 254（`masks/wardroom/gold_v2.vox.txt`，子作品標記 `金線:begin／end`）；子作品 vs 清單 0 差；`assembly_voxels` 跟著斜肋改成 1,809,302；重跑 sha256 相同。
- 過程圖：`overlays/fix_wardroom_gold.png`（只畫軍官室，正對艙壁）。
### 船尾頂角的舊翹角
- 量：船殼在 x 80–140 最高 z 160（＝ taffrail 頂）、高過 160 的 0 格；整個船尾高過 160 的只有 gallery 設計的金尖頂 24 格（後廊-P／S 各 12，到 z 166）。正後方看兩角只剩 gallery 冠與金尖頂（`overlays/check_stern_astern_now.png`）；4b 的正後方圖裡那對金色翹角現在沒有了。⇒ 沒東西可修；哪一階段不見的沒追。
## 階段十八 羅經櫃與主絞盤（2026-10-13，Tim：「然後繼續」⇒ todo 全做完；兩艘船原本都沒有，自由設計）
設計 plan.json `fittings_build`；產生 `design/draft_fittings.py`（兩件模型）⇒ `masks/fittings/{binnacle,capstan}.vox.txt`、`verify_fittings.json`；擺放 `design/draft_fittings_place.py` ⇒ `fittings_placement.json`、`verify_fittings_place.json`；套用 `design/tools/fittings_apply.py parts|models`。
- 子作品（0.02 m、parent 船殼、tags sub，當外部模型縮 0.2 掛 `甲板-spar`，同舵輪）：
  - `-binnacle` 羅經櫃 24×48×64、46,600 格：三格木櫃（兩個羅經夾一盞燈）、朝船尾三扇琥珀窗、山形頂、黃銅頂飾。
  - `-capstan` 主絞盤 80×80×66、134,892 格：鐵底圈、鼓身＋8 條肋、絞盤頭（直徑約 1.5 m）12 個插桿孔、上下鐵箍、黃銅蓋；插桿收起來不做。
  - 兩件各 1 元件、左右差 0。尺寸照一般比例，未查證。
- 擺法（同舵輪／砲）：中線、轉角 0、x 每 0.5 格試；格心＋八角不落在「組裝件＋spar carronade＋已擺的模型」；腳印正下方要是甲板、高低差 ≤ 1；保留區：梯子在上甲板的 foot／head 前後 6、兩側 4，舵輪前 0.6 m 給舵手站。
  - 羅經櫃：舵輪正前方第一個 ⇒ at (264, 160.5, 128)，跟舵輪外框前緣隔 6.5 格。
  - 主絞盤 v1：取最靠主桅 ⇒ x 333，0 碰撞但絞盤頭貼著主桅 fife rail、後面是 after-upper 梯口（看圖才發現）⇒ 加「四周 0.5 m 甲板以上淨空」⇒ 後半段一個位置都沒有，只剩前甲板 594.5..622.5 ⇒ 取中間 at (608.5, 160.5, 128)（前桅 x ≈ 656 之後）。不行的原因：艙口 594、高低差 176、太擠 36、保留區 14。
- 讀數：模型 **249**、models_broken 0；組裝件格數不變 1,813,919（模型不是 voxel）；穿過兩件外框的繩 0；兩支程式重跑 sha256 相同。
- 過程圖：`overlays/stage18_{binnacle_part,capstan_part,helm,capstan}.png`。
## 階段十九 旗（2026-10-13，Tim：「遊戲用的 ⇒ 外部完成＆內部大致構造＆必要功能」⇒ 先補外觀）
設計 plan.json `flags_build`；產生 `design/draft_flags.py` ⇒ `masks/flags/{ensign,pennant}.png`、`masks/flags/pole_{mizzen,main}.vox.txt`、`verify_flags.json`；套用 `design/tools/flags_apply.py`。
- 旗是帆（貼像素圖，TASK-0530）：靠桅那條邊釘住（bind）、飛出去的角 free 給風吹；vxk 帶貼圖（遊戲那側跑布料）。
- 船尾旗 `ensign` 4 m × 2.3 m、圖 48×28：暗紅底、金邊、正中一團手畫的火（16×19；v1 用公式畫 ⇒ 芯太高、像拱門 ⇒ 改手畫）。掛處：斜桁頂端不行（spanker 張在中線、旗會疊進帆面）；後桅 tg-head 也不行（mizzen-royal 帆張到 z 525，桅冠 534–536 底下只剩 0.9 m）⇒ 桅冠上加旗桿（後桅子作品 x 187、z 537–561、頂上 3×3 白冠，34 格）、旗掛旗桿船頭側。
- 長旗 `pennant` 0.4 m × 4 m 三角、圖 64×6：靠桅 8 欄金、暗紅、尾端 10 欄燕尾。v1 8 m 直接掛主桅桅冠 ⇒ 4.7 m/s 的風吹不起來、整條垂下蓋在 main-royal 帆前面（布沒有碰撞）⇒ 主桅也加旗桿（x 341、z 673–692，29 格）、縮成 4 m、掛 z 687–691（royal 桁頂 662 以上留 25 格）⇒ 平均位移 z −5、最鼓 17.5。
- 讀數：帆 **17**（15 ＋ 2）、sails_broken 0；組裝件 **1,813,982**（＋34＋29）、1 元件、空腔 0、link_overlap 0、鏡像差不變；重跑（扣掉本階段旗桿自己的格再對格數）sha256 相同。寫入時 IOException 1 次、重試過。
- 過程圖：`overlays/stage19_flags_{ship,ensign,pennant}.png`。
- ⚠ vxk 還沒重匯（上一次 6a04b4a8 是階段十八之前）⇒ 給 ame 前再匯。
## 階段二十 小艇與艇架（2026-10-13，外觀；自由設計）
設計 plan.json `boats_build`；產生 `design/draft_boats.py` ⇒ `masks/boats/{boat,skids}.vox.txt`、`boats_placement.json`、`verify_boats.json`；套用 `design/tools/boats_apply.py`。
- 船腰開口（量過）：上甲板 x ≈ 372..583、y 125..195；兩側走道甲板 z 127，開口邊是欄杆（柱每 3 格、z 128–134，扶手 z 135、y 124／196）。
- 艇架：三根 skid beam（x 445／478／511，寬 3、高 3、y 121–199、z 136–138，色 136）擱在兩邊扶手上，落在 `甲板-spar`（標記 `艇架:begin／end`，2,133 格）。v1 擱在走道甲板 z 128–130 ⇒ 撞欄杆柱 18 格（當場擋下）⇒ 抬到扶手上。
- 小艇：子作品 `-boat`（0.05 m、180×52×27、19,266 格、左右差 0、1 元件）＝ 9 m × 2.6 m cutter：外殼黑 36、舷頂暗紅帶 128＋金線 248、舷緣 136、艇內 141、坐板 5 條 104、收著 4 支槳 177；船頭尖、船尾方。當外部模型縮 0.5 掛 `甲板-spar`：`小艇-S` at (478,177.5,139)、`小艇-P` at (478,143.5,139) mirror y ⇒ 兩舷對稱。尺寸照一般比例，未查證。
- 讀數：兩艘艇格心＋八角 0 碰撞（含 spar carronade）；艇與艇架外框穿過的繩 0；模型 **251**、models_broken 0；組裝件 **1,816,115**（＋2,133）、1 元件、空腔 0、link_overlap 0、鏡像差不變；重跑 sha256 相同。
- 過程圖：`overlays/stage20_boats_{waist,ship}.png`。
## 遊戲 meta 補齊＋vxk 重匯（2026-10-13 傍晚，BTC；自由意志：待辦）
- `甲板-spar` 五個模型補 meta：`舵輪` kind=wheel、`羅經櫃` kind=binnacle、`主絞盤` kind=capstan、`小艇-S`／`小艇-P` kind=boat、boat=cutter、length_m=9（未查證）。憲法號組裝件的 `wheel` 也補 kind=wheel（兩艘一致）。只說「這是什麼」，站位／血量由遊戲決定。
- 讀回：models.json 五筆 meta 照寫、at 不變；schema 2。
- 匯出 `exports/ember.vxk`：1,816,115 格、checksum d346d01b、繩 1,083、帆 17、模型 251、帶 meta 257（252 ＋ 5）、固定點 1,509；封裝回讀對拍 ✓。
- 憲法號 `exports/constitution.vxk`：1,394,450 格、checksum 6bf2f49c、模型 208、帶 meta 212；封裝回讀對拍 ✓。
- 造船文件 §9 表加 wheel／binnacle／capstan／boat（Senate）。
## 階段二十一 中央彈藥庫（2026-10-13 傍晚，BTC；Tim：「另做餘燼號自己的彈藥庫」「可以試試把彈藥庫放中央位置」）
設計 `design/draft_magazine_mid.py`（改自憲法號 draft_magazines.py；輸入：組裝件藏 彈藥庫-前／後 的 list 匯出）⇒ `masks/magazine_mid/magazine.vox.txt`、`magazine_mid_placement.json`、`verify_magazine_mid.json`；套用 `design/tools/magazine_mid_apply.py`。
- 先量：船中段（x 423–563）**沒有 orlop 甲板**，貨艙一路通到 berth 甲板（z 59）；艙底內面 z 17；中線每 16–17 格一根支柱（469、486、502、519、535、552，各 3 格寬、z 17–58）。主桅 x 341、前桅 ≈ 656。
- 位置：x 461–544（兩根支柱之間起、另一根之前止）＝ 兩桅中點 498.5 附近（中心 502）；⚠ 船殼全長中點是 x 560 ⇒ 比全長中點偏船尾約 5.8 m。地板 z 23（桶站 z 24）、**自己鋪天花板 z 41**（跟 orlop 板同高；松木、每 8 格一道橡木樑）、門在船尾那道艙壁。
- 桶：照 90 門換算（憲法號 54 門 138 桶 ⇒ ×90/54 ≈ 230）＝ **230 桶、23,000 磅**（地板 172＋架上 58；容量 172＋168，排到 230 停 ⇒ 架子只在船尾那半段）。火藥桶模型照舊引用憲法號 -powder-barrel（scale 0.2、meta kind=powder、powder_lb=100）。
- 組裝件：關聯 `彈藥庫-中` @461,103,22（meta kind=magazine、powder_lb=23000）；**拿掉** `彈藥庫-前／後`（憲法號那兩件子作品本身沒動）。固定點 blast (501,160,33)、door (461,160,24)（組裝件座標）。
- 改了兩版：① v1 X0 478 ⇒ 容量只有 204（架上 76）⇒ 往船尾移到 461（架上容量跳到 168 —— 起排點跟著移、桶列跟斜肋的相對位置換了；沒逐列量）。② v2 側壁銅皮把中線支柱也包了（走道在支柱那幾格剩 1 格）⇒ 中線 ±6 不包；carvevox 刻掉 510 格（帶色 168 守門），子作品回讀 ＝ 遮罩逐格相同。
- 讀數：子作品 **22,762** 格（84×115×20）；組裝件 **1,827,921**（＝ 藏彈藥庫的 1,805,159 ＋ 22,762）、反向對照：新舊相減只多出遮罩那些格、舊格 0 刪 0 換色；1 元件、空腔 0、link_overlap 0；模型 343、models_broken 0。
- 匯出 `exports/ember.vxk`：1,827,921 格、checksum aea259b4、模型 343、帶 meta 348、固定點 1,507；封裝回讀對拍 ✓。
- ⚠ 給遊戲的變化：一間 23,000 磅在船正中（以前前後兩間 2,200／11,600）⇒ 殉爆半徑會大、斷在中段；取用點只剩一間的正上方。
- ⚠ TASK-0534 IOException 這一輪 234 筆寫入重試了 29 次；這台訊息是英文（Unable to remove the file to be replaced）⇒ 套用工具的重試要中英都認（第一次只認中文就停在 door 那一筆）。
- 過程圖：`overlays/stage21_magazine_{room,section}.png`。

## berth → orlop 梯子（2026-10-14 晚，BTC；Tim：「orlop也補一下」—— ame 的配置頁 orlop 艙房標「走不到」）
- 設計（`basecamp-frigate-constitution-01m/design/draft_orlop_ladders.py`，兩艘共用；幾何、顏色、扶手照新圖紙 20）：orlop 前後兩塊平台各一座，梯口只穿 berth deck（開在兩根橫樑之間），梯子落在 orlop 中線走道靠右舷那一側（y 162–168）—— 中線有一排柱子、桅也在中線。
  新圖紙 20 當時三處都放不下（after hatch 底下是洞、fore scuttle 落進艙房、companion 正對中線柱子），所以另開。
- 子作品 `basecamp-ember-01m-ladders-orlop`「餘燼號 berth → orlop 的梯子」（parent ＝ orlop 甲板、0.1 m、sub）；關聯 `甲板-orlop/梯子`（at 0,0,0、meta kind=ladders）；berth 甲板子作品 `basecamp-ember-01m-deck-berth` 開梯口（carvevox 帶顏色，只准是甲板板 250）。
- 兩座：orlop-aft（同憲法號，X < 406 沒拉長）、orlop-fore（憲法號那座 ＋66：梯口 X 606–617、梯腳 X 618）
- 每座 band 4、cap_up 0 第一次就放得下；367 格（側板 190、踏板 105、扶手柱 72）；梯口刻 198。扶手繩 4 條（`ladders/manropes`，0.35、slack 1.02）、柱頂固定點 8 個；給遊戲的點 8 個（`tools/ladder_points.py --draft --apply`，只對這一件）。
讀數（草稿開著，等 Tim 預覽）：
- 組裝件 export list 1,827,838 ＝ 1,827,669 − 198 ＋ 367，逐格缺 0／多 0／顏色不同 0；link_overlap 0、link_clipped 0；stats 1 元件、封閉空腔 0。
- 梯子跟現況重疊 0、浮空 0；梯子每一格都不在任何一間艙房（kind=rooms 的 min／max，36 間）裡。
- 扶手繩 4 條 ok（ropes 讀回、沒有斷的）。
- `ladder_points.py` 帶齊全部梯子重算（不寫入）：舊梯子的 foot／lo／hi／head 一個都沒變，多了 orlop-aft、orlop-fore ⇒ verify_ladder_points_*.json 是完整的那一份。
  ⚠ 這支工具原本只讀作品本體 ⇒ 加了 `--draft`（讀作品＋草稿；那件沒有草稿就照舊讀作品）。
- 過程圖：`overlays/orlop_ladder_fore.png`。
- 套用（Tim「測試ok 套用草稿然後單層提交吧 然後通知ame」）：梯子 367、berth 梯口 198，changed ＝ 清單格數、apply_mismatch 0；組裝件（不開草稿）export list 1,827,838 格，跟預覽時的草稿逐行相同；stats 1 元件、空腔 0。
- ember.vxk 重匯（include=rig,models,parts,meta；封裝回讀逐格對拍 ✓）：checksum 2ee492c1（繩 1,087、帆 17、模型 343、帶 meta 361、固定點 1,595）；ropes／sails／models_broken 0。
