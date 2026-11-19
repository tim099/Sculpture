# 星辰號（al-Najm，النجم）—— 1666 阿曼亞魯巴艦隊的武裝巴格拉

委託：Tim（Paperclip FAR-75）；Senate TASK-0019。船殼＝任務作品 `claude-baghlah-01m`，組裝件 `claude-baghlah-01m-assembly`（主作品，名稱「星辰號」）。

## 步驟 2 開工前（2026-11-18）

### 座標、比例、方向
- 一格 0.1 m（船殼、組裝件都記了 meters_per_voxel=0.1；子作品建立時也要記）。
- 框暫定 480 × 160 × 400（48 × 16 × 40 m）：步驟 3 定主尺寸後再調（調尺寸免費）。
- X 船長、船頭朝 +X；Y 船寬，中線 y=80（P 舷 y < 80、S 舷 y > 80）；Z 高度，z=0＝龍骨底面。
- 鏡像：格 y ↔ 160 − y（80 那一格是自己）；一舷子作品的另一舷關聯 mirror=y、at.y＝161 − at.y − 高。
- 固定點只收整數格；繩端要精準就寫小數。

### 作品怎麼拆
- 船殼（任務作品，tags=sub）：龍骨、艏艉柱、肋骨、外板、舷牆、砲口、方形船尾與船尾窗。
- 組裝件（主作品）：只放關聯與外部模型；船殼關聯 at 0,0,0（已建）。
- 子作品（parent_work 指船殼、tags=sub、記 0.1）：每層甲板一件、每根桅一件、每根三角帆桁一件＋外部模型、舵、船尾雕花板與艏柱頭（個性裝飾，自己做）。
- 一舷的東西只做一舷，另一舷 mirror=y。

### 打算引用的現有元件（sub=components 查過；步驟 9–11 再定 scale 與擺法）
| 用途 | 元件 | 一格 | 備註 |
|---|---|---|---|
| 迴旋砲 | `apex-one-reale-01m-gun-pierrier`＋`-mount` | 0.05 | gun:pierrier，17 世紀叉架後膛砲，21 件在用 |
| 舷牆輕砲 | `pinnacle-patache-01m-gun-4l`（或 `ridge-two-centurion-01m-gun-8l`） | 0.05 | gun:4l／8l，步驟 3 查武裝再定 |
| 錨 | `kotoko-fusta-01m-anchor-grapnel`（或憲法號 bower 縮小） | 0.05 | 印度洋 dhow 用四爪錨與有桿錨都有，步驟 11 定 |
| 火藥桶 | `basecamp-frigate-constitution-01m-powder-barrel` | 0.02 | meta powder |
| 絞盤 | `basecamp-ember-01m-capstan` | 0.02 | 升三角帆桁的 halyard |
| 小艇 | `basecamp-ember-01m-boat` | 0.05 | 縮成 dhow 拖的小艇 |
| 羅經櫃 | `summit-night-falcon-01m-binnacle` | 0.02 | |
| 燈 | `gura-tridente-01m-lantern` | 0.05 | 船尾燈 |
| 灶 | `kaguya-gloire-01m-galley` 或 `gura-pinas-01m-galley` | 0.05 | dhow 常是甲板上的沙箱灶，步驟 10 看要不要自己做 |
| 舵柄 | `apex-one-tartane-01m-tiller` 等 | 0.1 | 1666 年的巴格拉多半是舵柄＋操舵索，步驟 11 定 |

自己做的：方形船尾雕花板、五扇船尾窗、艏柱頭、船名、旗、三角帆桁（參考塔爾塔納、收穫號、康塞普西翁號的 lateen 帆桁）。

## 步驟 3 找資料與新圖紙（2026-11-18）

- 主圖：Pâris 1843 Pl. 2 fig. 7–9（Edye 實測的巴格拉，1:100，附公尺比例尺）；船尾正面看 Pl. 3。檔案與正文規格整理在 `references/README.md`。
- 已讀文件：Sculpture_Blueprint_Build §1–§4、Ship_Setup §3、Ship_Ends。
- 方向（設計決定，待步驟 3 讀完圖再定數字）：照 fig. 7 的線形放大到「平均以上」的大小（Pâris：大船寬 11.5 m、是 fig. 7 的近兩倍；一般 200–250 噸）；露天主甲板每舷 10–12 門砲、高船尾樓上放迴旋砲；兩桅三角帆＋船首柱上的三角帆；舵柄操舵（不用舵輪）；起錨用滑車組＋錨纜橫樑（Pâris：沒有絞盤 ⇒ 不放 capstan）。

### 讀圖與校準（`references/pl02_readings.json`）
- 比例尺：Pl. 2 y 3028 那條，0→10 m ＝ 729.5 px、0→5 m ＝ 365 px ⇒ **73.0 px/m**（1:100）。只有橫的比例尺 ⇒ 直的假設一樣（fig. 8 與 fig. 9 量到的半寬 212／211 px 互相對得上）。
- fig. 7（船頭在左）：龍骨底 py 1427、龍骨長 12.56 m；艏柱是直線，龍骨前端 px 905 → 艏柱頭 (235, 1072)，離水平 27.9°；艉柱是兩條平行線夾的帶，後緣 (1820,1428)→(1898,1165) 往後倒 16.5°（v1 量成 12.5° 是錯的，見下面 verifier）；taffrail (2020,1002)；主甲板 3.73 m、水線 2.73 m、船中舷頂 4.48 m；船尾樓前緣 px 1345、上層 px 1515。
- fig. 8：船寬 5.81 m（半寬 212 px）；最寬處 px 1164–1252。fig. 9：船中剖面 v2 共 21 點（去背景後逐列掃，兩半平均；z 2.6 m 以上外緣碰到框線，取 verifier 的 210／213 px）：V 形船底、圓舭、兩舷直到舷頂。
- 讀圖程式與放大圖在 Paperclip 工作目錄 `.work/FAR-75/read/`（不進作品）。
- verifier（子代理，被叫去重量、推翻；拿得到原圖）：比例尺、龍骨、艏柱、taffrail、舷頂、水線、fig. 8 都 holds（±4 px）。**抓到兩個錯**：① 艉柱我把後緣的腳配上前緣的頂，傾角 12.5° 應為 16.6° ⇒ `sternpost_rake_deg` 改 16.23、counter 21 → 14.5；② fig. 9 圓舭那段我用眼睛讀窄了 6–8 px ⇒ 整條重掃（v2），船底四個參數重新格點搜尋。另外：舵在艉柱後面（後緣 (1897,1428)→(1929,1165)，約 7°，步驟 11 用）；taffrail 後面還有一根細桿伸到 (2073, 992)，不算船長；上層船尾樓從 px 1507 起（我讀 1515，差 1.6 格，沒改）。

### 新圖紙 01：線形（`design/`）
- 程式：`lines.py`、`draft_lines.py`（抄康塞普西翁號 `apex-two-galeon-01m/design/`，檔頭寫出處與改了什麼）；參數全在 `plan.json`，每個數字有 `src`（P2 讀數／PT 正文／TIM／設計決定）。
- 縮放（TIM：寬 9～10 m、長 32～36 m）：長 sx 1.4724（艏柱頭到 taffrail 36.0 m）、寬 sy 1.638（9.5 m；Pâris 說大船比較胖）、高 sz 1.5。
- 跟康塞普西翁號不同：艏柱直線（`stem_run_per_z`）、counter 用直線（`shape: ramp`，艉柱頂 z 54 → taffrail z 87 外伸 21 格）、舷頂節點之間直線、只有兩個落差走 smoothstep（`top_curve.smooth`）。
- 讀數（`verify_lines.json`，v2）：全長 35.8 m（艏柱頭那格的尖到 x 378；艏柱頭裝飾步驟 6 補）、甲板長 30.6 m、龍骨 18.5 m、寬 9.5 m、水線寬 9.5 m、排水量 409 t（PT：大的近 400 噸）；牆 155,029 格（4 色）；**1 元件、空腔 0、鏡像差 0**。
- 跟 Pâris 對照（`paris_check`，原圖讀數 × 縮放）：寬 95／95.2、龍骨 184.9／184.9、艏柱頭 x 380.1／380.0、taffrail x 20.1／20.1；船中剖面（x 184）21 個高度差 ≤ 1.8 格（線形本身 ≤ 1.04，其餘是取整）；俯視外緣 33 點平均差 0.90 格、最差 4.8（艏柱頭往後 1 m 內 fig. 8 是凹的，沒做凹線 —— 設計決定，裝飾會蓋住）。
- 擬合過的參數：船底 plan_half／astilla／bilge_pow／max_breadth_z 格點搜尋 192 組 ⇒ 20／9／1.7／44；bow_pow_high（1.7–2.2）⇒ 1.9；aft_pow＋transom_ratio ⇒ 2.2／0.52。
- 反向對照（`--probe`，不寫檔；v2 重跑）：half_beam +3 ⇒ 量到的寬 101（＋6 ＝ 兩舷各 3）、船中差 1.8 → 2.8；sternpost_rake_deg +3 ⇒ taffrail x 20.1 → 15.0（87 × Δtan ＝ 5.1）；forefoot_x +3 ⇒ 龍骨 ＋3、艏柱頭 ＋3；stem_run_per_z +0.05 ⇒ 艏柱頭 ＋3.7、俯視最差 7.8；plan_half +3 ⇒ 船中差 2.0。尺會說話。
- 重跑：兩次輸出 `verify_lines.json`、`sheet01_lines_v1.png`、`masks/hull/hull_01.vox.txt` 的 sha256 一樣（v2：f234a198…、31f37468…、cac24a1c…）。圖紙的字用英文、Pillow 內建字型 ⇒ 換一台機器也逐位元組相同。
- 舊 id grep：只有檔頭的出處行和「跟康塞普西翁號不同」的說明提到來源船。

### 甲板、砲門、桅帆、船尾（`plan.json` 的 decks／ports／masts／gear／stern，步驟 4–11 照這些做）
- 甲板：hold platform z 36（x 120–290）、主甲板 z 56（x 250→290 抬 2）、船頭水槽（PT：往船頭降 0.70 m ⇒ x 280→292 降 7 格，0.7 m 照實寸）、舵手台（半層甲板）z 68（x 124–158）、船尾樓 z 74（x 158 以後到 124，底下艙房 18 格高）。
- 砲：主甲板每舷 11 門 4 磅（x 80–316，砲門 5×5、sill 3）＋船尾樓每舷 3 門、船頭每舷 1 門迴旋砲 ⇒ 30 門（PT：30 甚至 50 門）。
- 桅：主桅 x 191、直立（PT：大船直立）、長 28 m、直徑 0.75 m、三角帆桁 34 m、支索每舷 5；後桅 x 108、平行、腳在 hold platform、長 17 m、帆桁 20 m、支索每舷 3；foc 的桿子綁在錨纜橫樑 x 296、從艏柱頭伸出。
- 裝備：⛔ 不放絞盤（PT：用滑車組起錨）⇒ 上面元件表的 capstan 那一列作廢；錨纜橫樑 x 296、艏柱兩個滾輪、舵柄（不用舵輪）、不放幫浦。
- 船尾：艙房一排 5 扇窗（z 62–69）；兩舷側廊 x 29–71、z 58–73（3 扇窗）＋底下雕花托架，步驟 6 做。

## 步驟 4 船殼落格、砲門、塗裝、船尾窗（2026-11-18）

- 已讀：Sculpture_Blueprint_Build §5–§8。
- 作品框：480 × 160 × 400 → **420 × 160 × 120**（船殼 x 21..378、y 33..127、z 0..86；艏柱頭裝飾、桅、帆桁都是子作品 ⇒ 船殼框不用高）。組裝件維持 480 × 160 × 400。
- 程式：`design/layout.py`（甲板面 deck_z、砲門、排水孔、船尾窗；抄康塞普西翁號 layout.py 的寫法）、`design/draft_ports.py`（新圖紙 02）、`design/verify_step4.py`（結果帳）。
  - 跟康塞普西翁號不同：它是船殼先雕好再 carvevox 刻砲門、stampvox overwrite 換色；星辰號還沒落格 ⇒ **一張清單一次落完**（開口直接不放、顏色直接是塗好的）。
  - 甲板面 deck_z ＝ 站人的那一格（甲板板在它下面一格）；主甲板 56、x 250→290 直線抬 2、水槽 x 280→292 smoothstep 降 7（水槽面 51）。
- plan 改了三處（都寫在 src）：
  - 砲門 x_to 316 → **276**：v1 最後兩門落在水槽裡（甲板低 7 格）又壓在錨纜橫樑 x 296 底下。現在 11 門 x 80..275、中心間距 19.1 格，z 59–63（第 11 門在舷弧上，60–64）。
  - 船尾窗寬 6 → **5**（奇數才對中線對稱）、間距 9 ⇒ dy ±20.5 以內；z 62–69；窗洞整段刻穿到艙裡，玻璃與窗框留給步驟 6。
  - 新增 `ports.scuppers`：水槽兩舷 x 300、316 各一個排水孔（寬 3 高 1，z 51）；新增 `paint`：舷頂黑、主甲板面下 3 格起 2 格黑帶（照舷弧、不跟水槽下凹）、砲門外一圈白、船尾 counter 面（艉柱線後、z ≥ 55）黑底；黑 36、白 182。
- v1 → v2（落格前）：舷頂的判斷「上面一格不在船裡」把船尾樓往裡收的舷側台階也塗成黑點 ⇒ 加「離那一欄最高格不到 2 格」。
- 雕刻表：先貼船中 x 180–189 一片（stampvox 5,188 ⇒ placed 5,188），切 x 184 剖面看形狀對了，再貼其他 147,443（placed 147,443）。兩刀都 `expect_pixels`、免費。
- 讀數：
  - 結果帳（`verify_step4.jsonl`，events 重播 vs 設計）：152,631 ／ 152,631，**缺 0、多 0、色差 0**；正向對照（設計第一格 (21,62,86) 色 36，重播也是 36）。
  - 結構（在重播出來的格子上算）：**1 元件、空腔 0、鏡像差 0**；5 色（36: 5,623、136: 18,155、141: 46,967、177: 55,603、182: 26,283）。
  - 砲門 11／11 兩舷打穿、每舷每門刻 75 格（5 × 5 × 3）；從格子量砲門位置 vs plan 最差 0 格；船尾窗 5／5 刻穿（每扇 140 格）；排水孔每舷 11、13 格（船頭牆斜、比 9 多）。
  - 反向對照：砲門整排挪 +3 ⇒ 量到的砲門位置報 3；結果帳報缺 990／多 990（22 門 × 3 欄 × 5 列 × 3 厚）、色差 1,452。尺會說話。
  - 重跑 draft_ports 兩次，清單、圖紙、verify_ports.json 的 sha256 一樣（清單 c00d3f4e…）；步驟 3 的三個輸出 sha256 沒變。
- 過程圖：`overlays/stage4_profile_port.png`（側面）、`stage4_stern_from_aft.png`（船尾正面）、`stage4_section_port4.png`（x 139 剖面，砲門兩舷打穿）。⚠ 這台沒有 GPU：`op=view` 被擋（GLFW 找不到平台，引擎沒寫圖），3D 全景留到有 GPU 的機器補。
- 獨立 verifier（子代理，唯讀、不 import 作者的檢查程式，只用 layout.py／lines.py 算期望框；在重播的格子上量）：8 條全 holds（排水孔「貼甲板面」等步驟 5 才驗得到）。它多量了作者沒量的：整個砲門框（不只中心一格）、z 範圍、框外一圈厚度、全船有沒有計畫外的穿孔（兩舷各 13 個洞 ＝ 11 砲門 ＋ 2 排水孔）；埋 3 個塗錯的格也都抓到。報告：Paperclip 工作目錄 `.work/FAR-75/verifier4/report.md`。
- 照實留著的（§7.0 右欄，放上去之後再細修，寫進 todo）：① 舷頂內緣露出內板 177 的頂面（x 232–371 每站每舷約 1 格、船尾欄內側 x 24 z 85、船頭 x 372–373 z 71），只從上面／船內看得到；② 船尾窗洞的切面是木色（141／177），步驟 6 的窗框蓋掉；③ tumblehome ⇒ 從正上方看得到砲門白圈的窗台（幾何本來就這樣）。

## 步驟 5 甲板、梯子（2026-11-18）

- 已讀：Ship_Decks（§9.2 空艙房、§9.3 甲板與通道、樓梯自檢 ①–⑦、第一人稱爬得出來）。
- 程式：`design/draft_decks.py`（新圖紙 03；結構照收穫號 `calli-cosecha-01m/design/draft_decks.py`）、`design/tools/build_decks.py`（建子作品、貼、梯子固定點、關聯、甲板 meta）、`design/tools/check_decks.py`（結果帳）。參數在 `plan.json` 的 `decks_build`。
  - 跟收穫號不同：本船 `layout.deck_z` 是站人那一格（板在下面一格）；主甲板的板照舷弧／水槽一欄一欄走，相鄰兩欄差 2 格以上補 riser（板不留縫）；梯井只開「頭會撞到」那一段到梯頂（Ship_Decks「開梯口的做法」），梯頂最後一階貼著上一層的邊（④）；head 在邊內 2 格。
- plan 改了四處（都寫在 src）：
  - 舵手台甲板面 68 → **70**、不放樑：v1 板 67 ⇒ 底下 56..66 ＝ 11 格，遊戲走路要 12 格 ⇒ 主甲板在 x 125–158 被切斷、船尾艙走不到、砲門 4 的砲沒人走得到。現在 13 格。舷牆剩 5 格（舷頂 75），步驟 6 補欄杆／舷牆布。
  - 舵手台 x 124–158 → **125–150**：從格子量舷頂，x 125–149 是 75、x 150 起往船頭斜下去（153: 70、156: 67），70 的甲板鋪不過去。x 124 是船尾艙前壁。
  - 底艙平台 x_from 120 → **96**：後桅（heel_deck ＝ orlop）x 108 的腳要踩在平台上。
  - 新增 `bow_from_x` 320：水槽板只鋪得到 x 332，前面斜艏柱內側的楔形空間（約 15 m²）v1 被算成沒有梯子的艙底 ⇒ 主甲板的板順著楔形底一欄一欄往上鋪到 x 373。
- 遊戲甲板 3 層（子作品各一件，組裝件關聯 `甲板-<層>` at 0,0,0，meta kind=deck）：
  | 層 | level | floor（第一層空氣） | thick | 內容 |
  |---|---|---|---|---|
  | `orlop` 底艙平台 | 0 | 96:36 – 290:36 | 3 | 板 177、樑 2 深；主桅孔、hold 梯井 |
  | `main` 主甲板 | 1 | 46:56 … 舷弧 58 … 水槽 51 … 艏柱內側到 373:73 | 4 | 板 209、樑 3 深；主艙口 x 233–251、主桅與後桅孔、orlop 梯井 |
  | `poop` 船尾樓＋舵手台 | 2 | 33:74 – 124:74、125–127 台階 72、128:70 – 150:70 | 3 | 船尾樓板 z 73、樑 2 深；舵手台板 z 69；x 124 船尾艙前壁（門 0.9 × 1.3 m）；x 150 胸牆（梯子留口）；後桅孔 |
- 梯子 4 座（每 3 格一階、每階 2 格、踏板 7 寬；`ladder_points.json`、固定點在梯子子作品上；關聯 `甲板-<上層>/梯子` meta kind=ladders，跨甲板的那幾座寫 `<梯名>.decks`）：
  - `hold`：貨艙底 → 底艙平台，x 165→143、9 階（Ship_Decks ⑥ 的補法）；梯腳 z 8（艙底寬到 |dy| ≤ 5 的那一層），底下 x 162–168 鋪艙底板（verifier 修正，見下）。
  - `orlop`：底艙平台 → 主甲板，x 205→221、6 階，`decks=orlop,main`。
  - `quarter-P`／`quarter-S`：主甲板 → 舵手台，x 160→148、dy ∓12、4 階，`decks=main,poop`（|dy| 8–16，讓開砲 5 的後座）。
- 沒做的（文件寫「要的話」）：空艙房（§9.2）。船尾艙（x 46–123、主甲板 56 到船尾樓板 73）是現成的候選，Blockside 不在這台、`rooms.py` 量不到 ⇒ 留到步驟 14 跟遊戲那側一起看。
- 讀數：
  - 設計（`verify_decks.json`）：每件跟船殼重疊 0、在船殼外 0、彼此重疊 0、鏡像差 0；組起來 1 元件、空腔 0（只有 x 47 船尾一個 22 格的小空腔，填成樑色歸主甲板）；梯子點全部「空氣、腳下實心、頭上 14 格空」；④ 梯頂到 head 空 0 柱；砲門往艙裡 8 格內 0 格；排水孔 z 51 ＝ 水槽甲板面 51（步驟 4 verifier 驗不到的那半句）。
  - 走路格（自己量，規則照 Ship_Decks：頭上 12 格、一步 ≤ 3 格、不踩梯子；每層先各自切塊、只靠梯子接；貨艙用 0.6 m 一步）：orlop 148.32 m² 全接到；main 229.23 m²（接到 228.89）；poop 80.49 m²（79.80）；貨艙 115.01 m²（107.50；沒接到的只有平台前緣底下 3.56 m² 一塊，< 10 m²）。
  - 反向對照（`--probe`，不寫檔）：拿掉 `orlop` 梯子 ⇒ orlop 0、貨艙 0；拿掉 `hold` ⇒ 貨艙 0；拿掉兩座 `quarter` ⇒ poop 0；舵手台改回 68 ⇒ main 只接到 152.83／207.19、poop 18.86、④ 報空 2 柱。v1 的走路格沒照「每層各自切塊」⇒ 拿掉 hold 梯子貨艙照樣接得到（沿船底弧面一階一階走下去），反向對照抓到後改掉。
  - 重跑兩次，8 個輸出的 sha256 一樣；步驟 3、4 的輸出 sha 沒變（c00d3f4e…、cac24a1c…、8de0dcc0…、f234a198…）。
- 落格（`tools/build_decks.py`，每一步 exit 0）：6 件子作品（parent_work 船殼、tags=sub、0.1 m／格、框 420 × 160 × 120），每件一刀 stampvox 帶 expect_pixels（v1：orlop 16,844、main 27,573、poop 11,641、梯子 300／208／296），placed 全對；16 個梯子固定點；組裝件 3 條甲板關聯＋3 條梯子關聯；甲板 meta 用 `sub=meta file=decks_meta.tsv`。
- 結果帳（`tools/check_decks.py` ⇒ `design/verify_step5.json`，events 重播）：6 件缺 0、多 0、色差 0，跟船殼與彼此重疊 0；船殼＋6 件組起來 209,653 格（修正後）、1 元件、空腔 0、鏡像差 0；梯子點在組好的格子上全 OK；固定點 16／16 跟設計一樣；組裝件的甲板 meta 跟 tsv 一樣。反向對照：設計清單整片抬 1 格 ⇒ 報 89,912 個問題、每件都報缺／多。
- 過程圖：`overlays/stage5_long_y80.png`（中線縱剖面）、`stage5_long_y68.png`（左舷梯子那一條）、`stage5_section_x140.png`（舵手台底下、砲門 4）、`stage5_section_x242.png`（主艙口）；圖紙 `design/sheet03_decks_v1.png`。3D 全景照舊等有 GPU 的機器。
- ⚠ 組裝件「船殼」那條關聯顯示「尺寸變過（加關聯時 480,160,400、現在 420,160,120）」：步驟 4 縮框留下的；at 0,0,0、沒有 turn／mirror，格子位置不受影響。步驟 14 匯出前再看要不要重掛。
- 獨立 verifier（子代理，唯讀、自己寫 events 重播、不 import 作者的檢查程式）：8 條全部推翻不了；報告存在 Paperclip 工作目錄 `.work/FAR-75/verifier5/report.md`。它抓到作者沒量的：**hold 梯子兩側斜樑有 4 格（162–163, y 76／84, z 3）穿出 V 形船底**（水線下看得到）；梯腳站在龍骨旁 1 格寬的槽裡、最下一階只有 5 格寬。
- 修正（`plan.decks_build.ladders.sole_*`，`draft_decks.py` 加 `parts_outside_inside` 讀數）：梯子的格一律只留在艙裡（`~inside` 也刪）；hold 梯腳改在艙底寬到 |dy| ≤ 5 的第一層（z 8），x 162–168 底下鋪艙底板（141）；9 階、梯井 x 146–157。落格只補差：deck-orlop carvevox 74（帶顏色守門）＋stampvox 104；ladders-orlop carvevox 278＋stampvox 104→408＋overwrite 14；hold 四個固定點 unanchor 後重設。全部 exit 0、placed 跟清單一樣。
  - 修正後讀數：結果帳 6 件缺 0、多 0、色差 0（deck-orlop 16,874、ladders-orlop 430）；組起來 209,653 格、1 元件、空腔 0、鏡像差 0；梯子點全 OK、固定點 16／16；6 件子作品在艙外的格 0；verifier 點名的 4 格不在了；重跑逐位元組相同；反向對照（拿掉 hold ⇒ 貨艙 0、拿掉 orlop ⇒ orlop 與貨艙 0、拿掉兩座 quarter ⇒ poop 0、舵手台 68 ⇒ main 152.83）照舊報得出來。
- verifier 另外列的（不推翻宣稱，寫進 todo）：orlop 梯井 x 207 照 14 格頭高算多開 1 欄（照 12 格走路量要從 211 開）；船尾 x 24–32 外伸斜坡 3.41 m² 走得上去、不在任何 floor 範圍（< 10 m²）；主甲板 x 280–281 比前後高 1 格；桅還沒做 ⇒ 桅孔現在掉得下去（步驟 7 補）。

## 步驟 6 裝飾（2026-11-18）

- 已讀：Ship_Fittings §9.9（裝飾 deco=1 只有外部模型能標；有功能的、有東西掛在上面的不能標）、Ship_Materials「窗的玻璃」（material=glass 獨立關聯、1 格厚、6 連通、後面空）、Ship_Ends §3–§5（窗洞 6 連通距離、欄杆 rail_h ≥ 7、柱子間 2 格）。
- 程式：`design/draft_deco.py`（新圖紙 04；出處收穫號 draft_deco、憲法號 draft_stern_glass、Ship_Ends 的窗洞距離）⇒ `masks/step6/`（船殼換色、窗格）、`masks/deco/`（6 件）、`verify_deco.json`、`sheet04_deco_v1.png`；落格 `design/tools/build_deco.py`（hull／parts／links 三段）；結果帳 `design/tools/check_deco.py` ⇒ `design/verify_step6.json`。參數在 `plan.json` 的 `deco`（每一段都有 src）。設計讀的是船殼的**設計**（draft_ports.build）＋步驟 5 的清單，不讀作品 ⇒ 落格之後重跑清單一樣。
- 做了什麼：
  | 件 | 怎麼掛 | 格 | 內容 |
  |---|---|---|---|
  | 船殼（改） | — | 換色 719、加 60 | 五扇窗洞旁的切面全白（窗框，步驟 4 露出的 141／177 蓋掉）；窗格（中間一直、z 66 一橫）白；舷頂內緣露出的 177 改黑 36（步驟 4 todo，289 格） |
  | `-stern-glass` 船尾窗玻璃 | 組裝件關聯 `船尾窗玻璃` meta material=glass | 140 | 窗洞裡離船外 6 連通距離 2 的那一層（距離 1 空著 ＝ 窗框凹 1 格），後面通艙裡 |
  | `-quarter-gallery` 船尾側廊 | 組裝件關聯 `側廊-P` at 0,30,0、`側廊-S` at 0,91,0 mirror=y | 4,381（一舷） | P2 fig. 7：x 30–72、z 58–74，伸出船側 6 格；三扇窗（共用窗框、每扇 3 欄 × 2 排窗格）、黑身白框、上下白線腳、黑頂；底下雕花托架（白底黑槽，x 49–65、z 50–56）；窗外 1 格凹、第 2 格玻璃、後面實心暗色 37 |
  | `-quarter-gallery-glass` | 側廊作品裡的關聯 `窗玻璃` meta material=glass | 108（一舷） | 側廊三扇窗的玻璃 |
  | `-quarter-rail` 舵手台欄杆 | 組裝件關聯 `舵手台欄杆` | 529 | PT：兩舷 x 122–150 舷頂上紅色舷牆布（160）＋黑柱每 4 格＋黑扶手 z 80；前緣胸牆（x 150）上白色小柱每 3 格（從中線對稱）＋黑扶手 z 80；梯子口 y 64–72、88–96 不擋；兩個前角補黑柱接上扶手（v2） |
  | `-stern-carving` 船尾雕花 | 組裝件外部模型 `船尾雕花` meta deco=1 | 529 | P3：窗框上的尖拱與頂飾、窗框之間的短柱、外側兩根壁柱、窗下方格板（十字花＋四點）、z 75 線腳、沿船尾外緣的拱形邊、正中八角星（船名 al-Najm ＝ 星，設計決定）、兩朵十字花；貼在船尾面外 1 格，只放在黑底（或白窗框）前面（v2） |
  | `-stem-head` 艏柱頭 | 組裝件外部模型 `艏柱頭` meta deco=1 | 233 | P2 fig. 7 g：艏柱照斜度（每格 1.85）伸出 6 格、頂上瓜形頂飾（半徑 3，白、一圈黑頸；v1 八瓣黑白相間從船頭看像骷髏） |
- 讀數（設計，`verify_deco.json`）：各件跟船、彼此重疊 0；關聯組起來 219,360 格（v2）、1 元件、空腔 0、鏡像差 0；兩個模型 0 格浮空（每個連通塊都碰到船）、鏡像差 0、沒蓋到窗洞；窗洞旁還是木色的切面 0；舷頂 177 修完剩 0；梯子點 16 個全 OK；迴旋砲位（v2 的量法，見下）、砲門前 0 格；走路格少 69 格 ＝ 剛好是胸牆（4 格高的矮牆）頂上那一排，不是甲板。
  - 玻璃封不封得住（每扇窗一個盒子、從船外灌）：五扇都 0 漏；反向對照每扇抽掉 1 格玻璃 ⇒ 五扇都漏（40 格）。
  - 重跑兩次：10 個輸出 sha256 一樣；步驟 3–5 的清單 sha 沒變。
- 落格（每一步 exit 0、placed 跟清單一樣）：船殼 stampvox overwrite 719 ＋ stampvox 60；6 件子作品各一刀（0.1 m／格）；關聯 4 條＋側廊裡 1 條；模型 2 個（at 0,0,0、pivot 0、scale 1）。
  - ⚠ 側廊第一次建成整個船寬的框（420×160×120）、清單照絕對座標貼 ⇒ 右舷 mirror 的關聯放 y 1 超出組裝件 1 格被擋。建置程式寫了 ok=(0, 2) ⇒ 被擋也印 ✓（看關聯樹少一條才發現）。改：兩件 `work move delta=0,-30,0`（8,762／216 格變動 ＝ 4,381／108 × 2）、`update size=420,40,120`（側廊裡的玻璃關聯記著舊尺寸會擋縮框 ⇒ 先 unlink、縮、再接回）、關聯重接在 y 30／91。`plan.deco.quarter_gallery.frame` 記下來，清單改寫框內座標，建置程式改成直接這樣建、關聯只認 exit 0。
- 結果帳（`tools/check_deco.py`，events 重播，認得 workedit／move）：7 件（6 件＋船殼）缺 0、多 0、色差 0；**引擎組出來的組裝件**（export format=list）跟設計手組的逐格比 219,360 格（v2）缺 0、多 0、色差 0（右舷鏡像、巢狀玻璃都由引擎放）；那份 export 上 1 元件、空腔 0、鏡像差 0；關聯 meta、模型 meta 回讀都對；`export format=parts` 的模型外框跟清單的外框一模一樣（v1 的船尾雕花 [21,51,55]–[52,110,85]、艏柱頭 [378,77,73]–[395,84,83]）。反向對照：設計裡側廊放 y 31 ⇒ 報 3,352 個差。
- 過程圖：`overlays/stage6_stern_aft.png`（船尾正面）、`stage6_port_quarter.png`（左舷船尾）、`stage6_bow_head.png`（艏柱頭）、`stage6_helm_rail_top.png`（舵手台俯視）；圖紙 `design/sheet04_deco_v1.png`。3D 全景照舊等有 GPU 的機器（觀測頁、CLI view 也不畫玻璃透明，只有遊戲裡看得到）。
- v1 → v2（落格前）：v1 窗間壁柱 2 格寬，把窗框之間填滿 ⇒ 整排窗是一整塊白、尖拱糊成一團（圖紙一看就知道，讀數全過）。v2 窗框當分隔、窗框之間留黑。
- 沒做的：
  - 船名板（阿拉伯文）：P3 看不出有沒有；要的話之後補。
  - 船尾艙前壁（x 124）門框雕花：todo 寫「可以加」，這次沒做。
  - 旗桿（taffrail 後面那根細桿）：步驟 8 做旗時一起。
  - ⚠ 步驟 7 的 foc 桿子：腳在 x 296、仰角 12°，到 x 380 約 z 69–70，會穿過艏柱頂 ⇒ 要偏 y 放在艏柱旁邊、不碰頂飾。
- 獨立 verifier（子代理，唯讀、自己寫 events 重播與組裝、不 import 作者的程式；報告 Paperclip 工作目錄 `.work/FAR-75/verifier6/report.md`）：8 條 6 條推翻不了、**第 8 條推翻**：雕花上面那道邊在 x 36–44、z 83 有 22 格貼著 x 40 的迴旋砲位（船尾窄、船側在 y 55）；作者的檢查寫死 y ≤ 45／≥ 115，船尾根本沒量到。另外抓到：64 格白雕花貼在褐色舷側板上（船尾兩個上角的白弧）、艏柱頭黑白瓣像骷髏、欄杆兩個前角空一欄、雕花在將來舵頭上方（步驟 11 量）。
- v2 修正（同一輪）：
  - 迴旋砲檢查照那個 x 的船側算（舷頂下 3 格起、船側往裡 6 格內）；v1 雕花跑 ⇒ x 40 報 22（反向對照），v2 ⇒ 40／75／110 都 0。砲門前也改成照船側算，0。
  - 雕花只放在船尾面黑（或白窗框）的格前面，拱形邊照黑底外緣往裡 2 格 ⇒ 貼在非黑白上的格 v1 90（作者的量法；verifier 量 64）→ v2 0。雕花 617 → 529。
  - 艏柱頭改白＋一圈黑頸；欄杆兩個前角補黑柱（每角 6 格）。
  - 落格只補差（`tools/delta_apply.py`：events 重播 vs 清單）：雕花 carvevox 110（帶顏色守門）＋ stampvox 22；欄杆 stampvox 12；艏柱頭 stampvox overwrite 80。每刀 exit 0、格數對上。
  - 修完讀數：結果帳 7 件缺 0、多 0、色差 0；引擎 export 219,360 格 ＝ 設計、1 元件、空腔 0、鏡像差 0；重跑 10 個輸出逐位元組相同；抽玻璃反向對照五扇都漏 40 格；側廊挪 1 格反向對照報 3,352；兩個模型 0 格浮空、鏡像差 0。過程圖重畫。

## 步驟 7 桅與帆桁（2026-11-18）

- 已讀：Ship_Masts §5（桅的綁定 kind=mast＋mast、帆桁子作品＋外部模型、三角帆桁 yard=gaff＋rig=lateen＋固定點 fore、匯入檢查「桅的格在帆桁轉軸往下 10–40 格、中線 ±4」）。PT 第 84–140 行：主桅一整根柚木、直徑可到 0.75 m、大船直立；後桅跟主桅平行、穿過船尾樓前緣、大船腳下到 entre-pont；帆桁幾乎＝船長、兩段綁成、常在上端再接一段往上翹；兩條 itague 穿過桅頂的 clans 吊起帆桁；帆前緣 ＝ 後緣的一半；foc 的桿子綁在船頭與錨纜橫樑上。
- 做法照收穫號（`calli-cosecha-01m/design/draft_masts.py`）：三角帆桁在自己的框裡就做成斜的（前端低、後端高）、模型 rotate 0、pivot 在吊點那一格、放在桅的左舷側不穿過桅。⛔ 沒用塔爾塔納那種 rotate_y：Ship_Masts 只寫了繞 z；收穫號那套 ame 確認過遊戲畫得出來（酒館 seq 24919）。
- 程式：`design/draft_masts.py`（新圖紙 05）⇒ `masks/masts/`（main、mizzen、jibboom、cable_beam）、`masks/yards/`（lateen-main、lateen-mizzen）、`yards_lateen.json`、`yards_placement.json`、`verify_masts.json`、`sheet05_masts_v1.png`；參數 `plan.json` 的 `rig_build`（每一段都有 src）。設計讀的是前面每一步的**設計清單**（ship_cells；跟引擎 export 逐格一樣），不讀作品 ⇒ 落格之後重跑一樣。落格 `design/tools/build_masts.py`（parts／yards／links）；結果帳 `design/tools/check_masts.py` ⇒ `design/verify_step7.json`。`draft_decks.py` 加了 `--probe=with_later=1`（把後面步驟的件全放進船再算走路，不寫檔）。
- 做了什麼：
  | 件 | 怎麼掛 | 格 | 內容 |
  |---|---|---|---|
  | `-mast-main` 主桅 | 組裝件關聯 `主桅` meta kind=mast, mast=main | 9,556（v2） | x 191、腳 z 4（龍骨上，切掉 V 形船底邊上 14 格碎片）到 z 283（28 m）；z ≤ 57 截面 ＝ 甲板桅孔那個半徑 4 的整數圓盤（v2；v1 到 61）、z 56–57 多出來那圈 68 當桅領；往上收到 2.6；hounds z 250–251 一圈綁紮 68；桅頂 z 253–283 方 5×5、兩道滑輪槽黑；頂 2 格黑帽 |
  | `-mast-mizzen` 後桅 | `後桅` meta kind=mast, mast=mizzen | 2,839 | x 108、腳在底艙平台面 z 36、頂 z 206（17 m）；z ≤ 77 截面 ＝ 半徑 2.5 的桅孔圓盤；桅頂 3×3、一道滑輪槽 |
  | `-jibboom` foc 的桿子 | `foc桿` meta kind=mast, mast=bowsprit | 817（v2） | 腳躺在錨纜橫樑頂上（x 294、軸 z 70.6）、偏右舷 y 87（避開艏柱頭頂飾 y 77–83）、長 11.5 m、仰角 2.45°（v2；v1 3.15°；解出來的：不碰任何格的最小角 ⇒ 底面壓在船頭 x 370–377），x 373–375 與腳上兩道綁紮 |
  | `-cable-beam` 錨纜橫樑 | `錨纜橫樑` | 1,731（v2） | x 294–298、z 64–68（v2；v1 63–67）、兩頭頂到舷牆內面（y 45–115）；水槽甲板面 z 51 ⇒ 底下 13 格（1.3 m）走得過去 |
  | `-yard-main-lateen` 主三角帆桁 | 外部模型 `yard-main-lateen`，放在 `-mast-main` 裡 | 4,352（框 327×7×118） | 34 m、傾角 18°、吊點在前端往後 47%；半徑 2.75 收到 1.25；吊點前後各 3 m 每 6 格一道綁紮（兩段綁成）；後端最後 3 m 多翹 14°（第三段）；固定點 45（pivot、sling、fore、peak、jackstay-01…41） |
  | `-yard-mizzen-lateen` 後三角帆桁 | 外部模型 `yard-mizzen-lateen`，放在 `-mast-mizzen` 裡 | 1,302（框 165×7×91） | 18 m（plan 從 20 改，原因在 rig_build）、傾角 28°、吊點 40%；放在後桅右舷側 y 84（v2；v1 左舷 y 76）；固定點 25 |
  - 帆桁模型 meta：kind=yard、mast、yard=gaff、rig=lateen、sail（main-lateen／mizzen-lateen）、length_m、length_ft、diameter_in、pivot_anchor=pivot、turn_axis=z、rotate_z_deg=0。
- 讀數（設計，`verify_masts.json`）：
  - 桅孔：主桅在底艙平台（z 35）、主甲板（z 55）各 49／49 格、後桅在主甲板、船尾樓（z 73）各 21／21 格填滿，空 0。反向對照：拿掉主桅（後桅）的孔圓盤 ⇒ 兩層各報空 49（21）。
  - 跟船、彼此重疊 0；每件 1 元件；船＋新件組起來 1 元件、空腔 0；桅、橫樑鏡像差 0。
  - 帆桁：跟任何格重疊 0、最近空 1 格；主帆桁世界範圍 x 22–343、z 207–320（吊點 191,74,257），後桅帆桁 x 13–172、z 153–239（吊點 108,76,187）；匯入檢查那一段（轉軸往下 10–40 格、中線 ±4）主桅 651 格、後桅 403 格。反向對照：主帆桁吊點往上 73 ⇒ 那一段 0 格（報）；往下 180 ⇒ 跟船重疊（報）。
  - 三角帆擺角上限（rig=lateen：asin(2.5 m ÷ 吊點到前端的水平距離)）：主 9.5°、後 23.4°。
  - PT「前緣 ＝ 後緣的一半」：前緣（帆桁前端 → 艏柱頂 380, 72.9）14.0 m、後緣（後端 → 帆腳後角 x 224, z 70）32.0 m，比 2.28（PT 2）。
  - 走路（`draft_decks.py --probe=with_later=1`）：底艙平台 148.11／148.11 m²、主甲板 228.20／228.58、船尾樓 79.80／79.80、貨艙 107.01／114.52（步驟 5 是 107.5／115.0，沒接到的那塊照舊）；梯子點 0 個問題、頂端空欄 0；砲門前 0。
  - 重跑：9 個輸出 sha256 一樣；步驟 3–6 的清單沒動。
- 落格（每一步 exit 0、placed 跟清單一樣）：4 件桅／桿／橫樑子作品（框 480×160×400；橫樑 420×160×120）各一刀；2 件帆桁子作品各一刀＋固定點 45／25；關聯 4 條；模型 2 個（host 是桅子作品）。
- 結果帳（`tools/check_masts.py`，events 重播）：6 件新作品＋13 件舊作品缺 0、多 0、色差 0（舊的沒被動到）；**引擎組出來的組裝件**（export format=list）234,356 格跟設計手組的逐格一樣、1 元件、空腔 0、鏡像差 0（foc 桿除外）；關聯 meta、模型 at／pivot／rotate／scale／meta、固定點全部回讀對上，固定點都在帆桁的實心格上；匯入檢查（帆桁 mast 對到唯一一條 kind=mast、那段有桅的格）兩根都過；引擎印的模型外框 (22,72,207)–(344,77,321)、(13,75,153)–(173,78,240) 跟設計的世界範圍一樣。反向對照：設計裡兩根桅挪 1 格 ⇒ export 比對報缺 2,633／多 2,671。
- 過程圖：`overlays/stage7_side.png`（側面：桅、帆桁、帆的輪廓虛線）、`stage7_bow_top.png`（船頭俯視：foc 桿偏右舷、艏柱頭白）、`stage7_masthead.png`（主桅頂：滑輪槽、hounds、吊點）；圖紙 `design/sheet05_masts_v1.png`。
- 獨立 verifier（子代理，唯讀、自己寫 events 重播與組裝、不 import 作者的程式；摘要在 Paperclip 工作目錄 `.work/senate/FAR-75/verifier7/report.md`）：8 條**全部推翻不了**。它另外抓到的：後桅帆桁前端（x 143–172、212 格）側面看在主帆裡、跟主帆桁（y 72–76）幾乎同一面；主桅也在主帆輪廓裡（帆前下角在中線）；錨纜橫樑底下淨高 12 格整（0 餘裕）；主桅 z 61→62 一道 9→7 格寬的台階；diameter_in 寫的比格子粗；圖紙標「PT 1:2」沒寫實際 1:2.28；PT 的桅樑＋副木沒做。
- v2 修正（同一輪）：
  - 後桅帆桁換到後桅右舷側（y_off −4 → +4，中心 y 84、格 y 83–85）：只動模型（unmodel＋model，格子不動），跟主帆分在兩邊。
  - 錨纜橫樑抬 1 格（z 64–68，底下 13 格）；foc 桿腳跟著抬，仰角重解 3.15° → 2.45°（底面照樣壓在船頭 x 370–377）。
  - 主桅桅孔圓盤只到 z 57（主甲板面＋1），甲板面上那 2 格比桅身粗的一圈塗 68 當桅領（mast coat），台階藏在甲板面上。艙裡那段 0.9 m 是甲板孔定的，比 PT 粗 —— plan 寫明。
  - diameter_in 照格子寬：19.7（5 格）、11.8（3 格）（sub=meta part=model）。圖紙標「PT 1:2, here 1:2.28」。
  - 落格只補差（`tools/delta_apply.py`）：主桅 carvevox 68＋overwrite 8；橫樑 carvevox 337＋stampvox 351；foc 桿 carvevox 147＋stampvox 148。每刀 exit 0、格數對上。
  - 修完讀數：結果帳 19 件缺 0、多 0、色差 0；引擎 export 234,303 格 ＝ 設計、1 元件、空腔 0、鏡像差 0（foc 桿除外）；模型、固定點、meta 回讀全對；匯入檢查兩根都過（651／403 格）；後桅帆桁外框 (13,83,153)–(173,86,240)；桅孔 49／49、21／21；走路（with_later）主甲板 227.97／228.31、其他層跟 v1 一樣，梯子點 0 問題、砲門前 0；反向對照（兩桅挪 1 格 ⇒ 缺 2,621／多 2,659）照樣報；重跑 9 個輸出逐位元組相同。
  - 主帆穿過主桅（帆前下角在中線）、後桅帆桁擺動時掃到主桅後支索、pivot 不在桅軸：都是步驟 8 掛帆、拉支索時要量的，寫進 todo。

## 步驟 8 索具、帆、旗（2026-11-18）

- 已讀：Ship_Rigging §6（繩的色、粗、slack；固定點量在實際的格子上）、§7（帆角綁帆桁模型、三角帆 luff 沿 stay、預設風 4.5,−1.5,0）、§9.1（帆／旗／繩的 meta、帆裝三段要排一次、國旗一定標 nation 而且要有貼圖）。PT 第 118–140 行（shroud、itague、帆、foc）；P3 重看一次（轉正後：主桅的 shroud 大多往後落在船尾樓前、前面兩條拉到船頭，桅頂下一段有滑車；船尾頂上一根短直桿）。
- 程式：`design/draft_rigging.py`（新圖紙 06；出處收穫號 draft_rigging）⇒ `masks/rigging/`（rings、stern_spars、halyard_bitt）、`rigging_plan.json`（固定點、繩、帆、meta、風、每個端點的世界座標）、`textures/ensign.png`、`verify_rigging.json`、`sheet06_rigging_v1.png`；參數 `plan.json` 的 `rigging`（每一段都有 src，v1→v4 的改法也寫在 src）。落格 `tools/build_rigging.py`（parts／anchors／ropes／sails／sailropes／wind／meta／prune）；結果帳 `tools/check_rigging.py` ⇒ `verify_step8.json`；掛好的帆布 `tools/check_sails_sim.py` ⇒ `verify_step8_sails.json`；過程圖 `tools/render_rig.py`。`draft_decks.py --probe=with_later=1` 多收 `masks/rigging/`。
- 跟收穫號不同：沒有 channels／deadeye／ratlines（PT：shroud 是單條 pantoire 加滑車、勾在船外的環上、照需要換位置；三角帆船沒有繩梯）；三角帆做成梯形 4 個角（fore、peak、clew、tack，下面兩角 free 各一條繩）；foc 掛在從 foc 桿尖端拉到主桅 hounds 的 stay 上；升降索穿過桅頂滑輪槽到大滑車再到 e。
- 做了什麼：
  | 件 | 怎麼掛 | 格／條 | 內容 |
  |---|---|---|---|
  | `-rings` 支索的環 | 組裝件關聯 `支索環` | 80 | 兩舷各 8 個（主桅 x 166、185、204、300、314；後桅 x 90、102、118），舷頂下 2 格，貼船側 1 × 1 × 3 鐵片＋往外 2 格的眼（深灰 73）；兩舷都做（換舷用），鏡像差 0 |
  | `-stern-spars` 船尾的桿 | `船尾桿` | 233 | 國旗桿：taffrail 頂中線 x 23、z 87–118（3.2 m、黑帽）；bumkin：左舷船尾角 (28,68,87) 斜斜往後往外到 (10,56,89)（P2 taffrail 後面那根細桿讀成 bumkin，後桅帆 sheet 走這裡） |
  | `-halyard-bitt` 升降索柱 e | `升降索柱` | 292 | 主甲板中線、主桅後面 x 174–178、0.5 m 見方、高 1.4 m、上面 0.4 m 收細、一道滑輪槽、一根 cabillot |
  | shroud | 組裝件的繩 | 8 組 × 4 條 | 每組：pendant（hounds → 滑車）＋滑車（一段短粗繩）＋2 條 fall（滑車 → 環）；主桅 5 組、後桅 3 組，**都拉在右舷**（兩面帆都在左舷，左舷的 shroud 一定穿過帆）；主桅前兩條 pantoire 長（滑車在 68%）、包布色 |
  | 升降索 | | 主 8、後 5 | itague 從帆桁 sling 繞到桅頂左前角、進滑輪槽、出後面到大滑車；fall 主桅 3 條到 e、後桅 2 條到船尾樓甲板中線 x 70 |
  | foc 的 stay | | 1 | foc 桿尖端 → 主桅 hounds 前面，拉直（三角帆的 luff 沿它） |
  | 帆 | | 3 | `main-lateen`（gaff）、`mizzen-lateen`（gaff、set 3）、`foc`（jib）；帆自己的繩 5 條（主帆 sheet／tack、後桅帆 sheet／tack、foc sheet）都帶 meta kind＋sail |
  | 旗 | | 2 | `ensign`（國旗桿、一整面紅、貼圖 24 × 16、nation=oman）、`pennant`（主桅頂前面、4 m 紅長旗、nation=none） |
- 帆裝三段（Ship_Rigging §9.1 排一次）：收帆 ＝ foc；戰鬥帆 ＝ foc、main-lateen；滿帆 ＝ foc、main-lateen、mizzen-lateen。收帆、戰鬥帆都至少一面、三段分得出來。⚠ 遊戲裡（W／S 換帆裝）要等步驟 14 匯進去才驗得到。
- 前緣：後緣（PT 1:2）：主帆 13.6 : 28.7 m ＝ 1:2.12、後桅帆 7.4 : 14.1 m ＝ 1:1.90。
- 改了幾輪（都是量出來的，每一輪的原因寫在 plan 的 src）：
  - v1 → v2（落格前，設計讀數）：16 條 fall 擦過舷頂外角 ⇒ 環的眼往外伸；滑輪槽的固定點離桅頂 1 格 ⇒ 改貼著；**後桅帆桁擺到 −9.7° 時碰到主桅升降索的 fall（−0.14 格）** ⇒ e 從舵手台搬到主桅後面；後桅最前一個環 x 126 那條往後上拉會穿過 x 123 的舷頂 ⇒ 改 x 118；itague 1.4 → 1.0（出槽那段切進桅頂 0.2 格）。
  - 落格後量掛好的帆布（`check_sails_sim.py`，引擎 export obj、預設風、3 秒）：**平面讀數全過、帆布不過**：
    - 主帆：上緣釘在 fore → peak 的直線上，帆桁第三段往上翹 14° ⇒ 直線在帆桁中段浮在帆桁上面、兩條 itague 從帆布穿出 ⇒ 上緣後角改成第三段開始那一點（帆桁 local 29,3,98），第三段 3 m 不掛帆（引擎一條邊只能釘在兩角之間的直線上）。
    - 後桅帆（帆桁在右舷）：在預設風下是三角帆的「壞舷」——帆在桅的上風那側，往左舷鼓 40 格、包住後桅（6 → 75 點在桅裡）又穿過自己的 itague。試過把 clew／tack 拉向右舷、縮短 tack 繩、fullness 1.03，都沒用 ⇒ **v4 把後桅帆桁換回左舷**（步驟 7 v1 的位置；只動模型 at y 84.5 → 76.5，格子不動），帆跟主帆一樣在下風；bumkin、clew、tack 跟著換到左舷，後桅的 shroud 換到右舷。步驟 7 verifier 擔心的「主帆穿過後桅帆桁」用掛好的帆布量：主帆布離後桅帆桁、後桅帆布都 ≥ 37 格。
    - foc：帆腳是自由邊，被風吹到左舷 10 格、擦到艏柱頭頂飾（3–4 點）⇒ 在作品上試了 5 組 clew／sheet／fullness，clew 往後往上（x 290、z 98）、sheet 順著帆腳往後拉到右舷舷頂 x 266 ⇒ 離頂飾 2.8 格。fullness 1.03 反而更糟（−0.23），留 1.05。
- 讀數（設計，`verify_rigging.json`）：3 件新零件跟船重疊 0、每個連通塊都碰到船、船＋新零件 3 個元件（跟步驟 7 一樣：兩根帆桁是模型、離桅 1 格）；砲門前與後座 2 m 內 0 格、4 個迴旋砲位 0 格；固定點 34 個都在自己作品的格上或貼著（實心 21、貼著 13）；直線的繩穿過實心 0 條（最小間隙 0.0 是 itague 進出滑輪槽、foc stay 0.05）；繩對繩最近 1.25 格（後桅兩個滑車）；平面帆被繩穿過 0；帆桁擺動（主 ±9.5°、後 ±23.4°）離繩最近 6.9／6.55 格；帆自己的繩沒有 meta 0、sail 標錯 0。
- 讀數（掛好的帆布，`verify_step8_sails.json`）：5 面都只在「自己被釘住的邊」碰到格子（主帆上緣在主帆桁裡 69 點、後桅帆 79 點、foc 的 tack 角在 foc 桿尖端 2 點），別的格 0；穿過帆布的繩 0；帆跟帆最近 5.74 格（foc 對主帆）、國旗對後桅帆 27.6 格；主帆鼓 39.6 格往左舷（帆布伸到舷外 y 18，三角帆本來就這樣）。
- 走路（`draft_decks.py --probe=with_later=1`）：主甲板 227.72／228.20 m²（步驟 7：227.97／228.31，少的是 e 的 0.25 m²），其他層一樣；梯子點 0 問題、砲門後面 0 擋。
- 反向對照：`--probe=nometa=foc.sheet` ⇒ 報那一條；`--probe=side=main`（主桅 shroud 放到帆那舷）⇒ 報 5 條穿過主帆；`--probe=side=mizzen` ⇒ 報 3 條；`--probe=ring_dx=-30` ⇒ 後桅帆桁擺動報 −0.18；`check_rigging.py --probe=drop_meta=mizzen-lateen.sheet` ⇒ 報那一條；`--probe=part_dx=1` ⇒ 缺 273／多 273；`check_sails_sim.py --wind=4.5,1.5,0`（風換舷）⇒ 兩面三角帆都包住自己的桅、繩穿過帆布。尺會說話。
- 落格（每一步 exit 0）：3 件子作品（0.1 m／格、框 420 × 160 × 120）各一刀 stampvox＋關聯；固定點 34、繩 54、帆 5、帆自己的繩 5、預設風、meta 49 筆（一份批次檔）。改版只補差：船尾桿 3 次（carvevox 100＋stampvox 100、86＋59、73＋73）；後桅帆桁模型 overwrite（at y 76.5）；換舷留下的 12 條舊繩、2 個舊固定點用 prune 拿掉（只拿 note 開頭是「步驟 8」的）。
- 結果帳（`tools/check_rigging.py` ⇒ `verify_step8.json`）：22 件作品從 events 重播跟設計逐格比，缺 0、多 0、色差 0（舊的 19 件沒被動到）；引擎 export 234,908 格（步驟 7 的 234,303 ＋ 605）＝ 設計、1 元件、空腔 0、鏡像差 0（foc 桿、bumkin 除外）；3 條新關聯、兩個帆桁模型、34 個固定點回讀都對、步驟 8 留下的舊固定點 0；ropes.json 54／54、sails.json 5／5 跟 rigging_plan 每個欄位一樣；帆自己的繩 meta 5／5；國旗有 nation 也有貼圖；帆桁 meta 的 sail 都是帆名；預設風 4.5,−1.5,0、3 秒；CLI `ropes_broken 0`、`sails_broken 0`、未分組 0。`problems_total 0`。
- 重跑：draft_rigging 7 個輸出、draft_masts 的 yards_placement／verify_masts 兩次 sha256 一樣（rigging_plan eb56c209…、verify_rigging 37b7ddf0…、rings 53d65331…、stern_spars 8c1477f4…、halyard_bitt a96166a9…）。
- 過程圖：`overlays/stage8_side_port.png`（左舷看、帆布是掛好的樣子）、`stage8_top.png`（俯視：兩面帆鼓到左舷外）、`stage8_stern.png`（船尾看：帆在左、shroud 在右）；圖紙 `design/sheet06_rigging_v1.png`（平面帆的輪廓）。3D 全景照舊等有 GPU 的機器。
- 沒做的（寫進 todo）：帆桁的 drosse à palan（帶 pommes 的 parrel 滑車組）、bras 與 palans de moustache（帆桁前端往船頭兩舷拉的那兩條會穿過 foc，量過）；PT 說天氣太壞時 foc 改升到桅上（沒做第二個位置）；國旗桿上的 `flag-top` 固定點目前沒有繩用。
- 獨立 verifier（子代理，唯讀、自己寫 replay／組裝／布面取樣／帆桁旋轉、不 import 作者的程式；報告 Paperclip 工作目錄 `.work/FAR-75/verifier8/report.md`）：8 條 7 條推翻不了，**第 4 條推翻**：帆跟帆最近不是 5.74 而是 4.95 格（作者只量網格頂點，沒量三角形裡面）；foc 離頂飾也不是 2.8 而是 2.32。另外抓到：兩條主桅 fall、兩條 itague 當成管子（半徑＝粗/2）會擦到舷頂與 hounds 綁紮；foc.sheet 在頭的高度橫過右舷前甲板、穿過第 11 門砲的後座區；後桅帆腳在左舷三門迴旋砲上面只有 0.73–1.03 m；PT 是「quatre ou six」條 shroud（5 不對）；後桅 fall 綁在光板上、主桅 fall 沒進 e 的滑輪槽；帆桁沒有 drosse、離桅懸空 0.1 m；兩面旗離桿 0.47 格；只有一舷的風是乾淨的。
- v5 修正（同一輪；每一條的原因寫在 plan 的 src）：
  - 量法：`check_sails_sim.py` 改量三角形面（只把靠近東西的三角形密取樣，0.2–0.3 格），重量 v4 ⇒ 跟 verifier 一樣（4.95、2.32），還多抓到主帆腳在 x 330 左舷船頭迴旋砲上面只有 0.42 m；`draft_rigging.py` 的繩對格改成點到方塊的精確距離（減管子半徑），繩端落在自己的固定點實心格裡（環的眼、滑輪槽）那一段不算。
  - shroud：主桅 6（加 x 223）、後桅 4（x 84、96、104、118，後桅滑車放 40%）；船頭會往外張 ⇒ 環的眼伸過舷頂外張那一格再 2 格。
  - 升降索：itague 出槽後先往後下 2 格再到大滑車；主桅 fall 綁進 e 的滑輪槽那格；後桅 fall 綁在船尾樓中線一根新做的小繫索柱（kevel，x 69–71、0.3 m 見方、高 0.7 m，放在 `-halyard-bitt`）。
  - 帆：主帆 clew 抬到 z 94、後桅帆 clew／tack 抬 1.2 m（離迴旋砲遠一點）；foc 的 sheet 改綁錨纜橫樑右舷端頂上、拉直（在作品上試了兩組）。兩面三角帆的前緣：後緣都變成 1:2.03（PT 1:2）。
  - drosse：每根帆桁一條短粗繩（`<桅>-parrel`）從吊點綁到桅，把 0.1 m 的縫補起來（沒做 pommes）。
  - 旗：吊在桿前面 0.15 格（貼在面上布會鑽進桿、0.5 格又飄在旁邊）。
  - 落格只補差：環 carvevox 22＋stampvox 40；升降索柱 stampvox 63（kevel）；固定點 40、繩 67、帆 5、meta 58；prune 拿掉 6 個舊固定點。
- v5 讀數：
  - 設計（`verify_rigging.json`）：直線的繩穿過實心 0、管子碰到格子 0（最小間隙 0.43 格）；繩對繩最近 0.5（itague 對 parrel，兩條都從帆桁出來）；帆桁擺動離繩最近 6.9／6.55、後桅帆桁離主桅 shroud 13.32；三件零件 1 元件以上都碰到船、砲門前與後座 0、迴旋砲位 0。
  - 掛好的帆布（`verify_step8_sails.json`，面取樣）：主帆、後桅帆只進自己的帆桁（被釘住的上緣）、foc 只進 foc 桿尖端那一格、兩面旗 0；穿過帆布的繩 0；帆跟帆最近 4.21 格（foc 對主帆，在 x 375 艏柱旁）；foc 離頂飾 3.32 格；帆布在迴旋砲位上面：後桅帆 1.96–2.05 m、主帆在 x 330 0.97 m（主帆 tack 綁在艏柱頂，PT，再抬就離開艏柱了 —— 照實留著）。
  - 結果帳（`verify_step8.json`）：22 件 0／0／0；引擎 export 234,989 格（234,303 ＋ 環 98 ＋ 船尾桿 233 ＋ 升降索柱 355）＝ 設計、1 元件、空腔 0、鏡像差 0（foc 桿、bumkin 除外）；繩 67／67、帆 5／5、meta、模型、固定點回讀都對、舊固定點 0；`ropes_broken 0`、`sails_broken 0`。`problems_total 0`。
  - 走路：主甲板 227.72／228.20、船尾樓 79.71／79.71（kevel 0.09 m²），其他照舊。
  - 反向對照：nometa ⇒ 報 foc.sheet；side=main ⇒ 6 條穿過主帆；side=mizzen ⇒ 報；ring_dx=−30 ⇒ 後桅帆桁離主桅 shroud 13.32 → 6.75；drop_meta ⇒ 報；part_dx=1 ⇒ 缺 312／多 312；風換舷（4.5,1.5,0）⇒ 主帆進主桅 321 格、後桅帆進後桅 63 格、繩穿過帆布 3／4 條。
  - 重跑：draft_rigging 7 個輸出兩次 sha256 一樣（rigging_plan 9b23df72…、rings 4dff17a7…、halyard_bitt 32bc8e3e…）。
- ⚠ 只有一舷的風是乾淨的：預設風（往 −y）兩面帆都在下風；風換到另一舷就是三角帆的壞舷，帆布會包住桅、繩穿過帆布。遊戲的風會變、布是即時模擬的 ⇒ 步驟 14 匯進去看遊戲怎麼處理（todo）。

## 步驟 9 砲（2026-11-18）

- 已讀：Ship_Guns（§4.1–§4.4、§4.2.1 砲身與砲座拆兩件、§2.2 缺的砲種／砲只跟同一種砲共用模型）、Ship_Turrets §4.5（迴旋砲 mount=turret 連續轉 ⇒ 整個 arc 都要量）。
- 程式：`design/draft_guns.py`（新圖紙 07；出處聖羅曼號 pinnacle-patache-01m/design/draft_guns.py＋gunsim.py，同樣是 4 磅砲＋pierrier 這兩件）⇒ `guns_placement.json`、`verify_guns.json`、`sheet07_guns_v1.png`；`design/draft_gunfittings.py`（出處藍鯊號 gura-pinas-01m，收穫號那一套）⇒ `masks/gunfittings/`、`gunfittings_points.json`、`gun_ropes.json`、`verify_gunfittings.json`；落格 `tools/build_guns.py`、`tools/build_gunfittings.py`；回讀 `tools/check_guns.py` ⇒ `verify_step9.json`；整船結果帳 `tools/check_rigging.py --extra=gunfittings:gunfittings/gunfittings` ⇒ `verify_step9_ledger.json`；過程圖 `tools/render_guns.py`。參數 `plan.json` 的 `guns_build`、`gunfittings_build`（每一段都有 src）。
  - 跟聖羅曼號不同：實心格讀的是前面每一步的**設計清單**（ship_cells＋桅＋帆桁＋步驟 8 零件），不是 CLI 匯出 ⇒ 不用開 Server、落格之後重跑逐位元組相同；元件的格子存在 `masks/guns_src/`（匯出一次，sha 記在 verify）；多量了預設後座、迴旋砲整個 arc、砲口射線、離繩多遠、梯子點、外框。
- 做了什麼（全部是外部模型，掛在所在甲板的子作品上；P 舷 mirror=y）：
  | 砲 | 掛在 | 數 | 元件、縮放 | meta |
  |---|---|---|---|---|
  | 4 磅砲 `砲M-S01..11`／`砲M-P01..11` | `-deck-main` | 22 | `pinnacle-patache-01m-gun-4l`（聖羅曼號做的通用部件）0.443、pivot 6.5,28,0 | kind=gun, gun=4l, deck, side, port |
  | 迴旋砲 `迴旋砲-S01..04`／`-P01..04` | `-deck-poop` | 8 | `apex-one-reale-01m-gun-pierrier` 0.39、pivot 5.5,18.5,0 | kind=gun, gun=pierrier, mount=turret, arc, rate=45 |
  | 叉架雙生 `迴旋砲-XNN座` | `-deck-poop` | 8 | `apex-one-reale-01m-gun-pierrier-mount`，擺法同砲 | kind=gunmount（mount_of 等步驟 14 發 id） |
  - 4 磅砲縮 0.443（照拉貝爾號、澤漢號）：`--probe=scale` 量過 0.5 ⇒ 穿過船牆那段砲管離上楣只剩 0.1 格（取樣點往裡縮 0.1 ⇒ 表面貼著）、砲口只伸出 1.75–2.75；0.55 ⇒ 22 門都穿不過砲門。
  - 迴旋砲：船尾樓舷牆頂 x 40、75、110（plan.ports.swivels 照舊）；**船頭那一對（x 330）改到舵手台欄杆 x 140**：x 330 水槽甲板面 51、舷頂 70 ⇒ 砲軸離站的地方 2.3 m 搆不到。砲軸離甲板 1.37–1.57 m。
  - **x 110 那一對只轉 ±60°**（其他 ±80°，照拉貝爾號、聖羅曼號）：夾在後桅支索環 x 104 與 x 118 中間，砲管轉到 −63° 以外、+72° 以外會穿過 shroud 的 fall（直線量；±80° 時差 −0.53／−0.63 格）。兩舷同一組、取對稱的 ±60°。
- 砲具與砲索（`-gunfittings` 子作品，組裝件關聯 `砲具` meta kind=gunfittings）：22 門 4 磅砲每門船牆兩側各一個環（鐵釘＋環 2 格）、砲架後面甲板一個環；breeching ×2、side tackle ×2、train tackle ×1 ⇒ 110 格、66 固定點、110 條繩（組 guns/breeching、guns/tackle、guns/train）。迴旋砲沒有砲架，不掛。
  - 第 3 門砲門 x 118–122 緊貼船尾艙前壁 x 124 ⇒ 船頭側的環 6–12 格都在艙壁另一邊、繩穿牆 ⇒ plan 加 offset 5／4／3，最後落在 x 123（偏 3）。反向對照 `--probe=offset=8` ⇒ 報第 3 門那一側掛不上（106 條）。
  - train tackle 的 slack 1.05 → **1.02**：引擎畫出來的繩（export obj）1.05 垂進甲板板，22 條每條 15–24 個頂點在板裡、最低 z 55.77 ⇒ 1.02 最低 56.17、0 個頂點在實心裡。
  - 沒做 shot garland 與 rammer／sponge（露天甲板上面沒有樑可以掛）。
- 讀數（設計，`verify_guns.json`）：30 門都 ok；4 磅砲往裡退 3–5 格、側挪 −1..1、dz 0、砲口伸出船殼 2.31–4.31 格、砲軸 z 62.42–63.42、砲管在砲門裡離上楣 0.56／離窗台 2.4、砲架腳下 100% 實心；砲跟砲重疊 0；兩舷對稱差 0；預設後座（4 磅砲 5.18 格、迴旋砲只退砲身 4 格）撞到 0；迴旋砲每 5° 量整個 arc 撞到 0；砲口射線（6 m）撞到自己的船 0；離直線繩最近 0.25 格（x 110 那門轉到 −60°）；梯子點在砲的外框裡 0。
  - 反向對照：`--probe=push=砲M-S05:3` ⇒ 只有那一門報 1,181 個取樣點撞到；`--probe=scale=4l:0.55` ⇒ 22 門 not_ok、砲管不在砲門裡；v1 迴旋砲站位用「那一欄最高的格」⇒ x 110 抓到後桅那一欄（砲軸離甲板 11.4 m），sweep 每個角度撞上千點（已改成只看舷牆／欄杆、外側半邊）。
  - 走路（`draft_decks.py --probe=with_later=2`：砲具＋每門砲的外框當實心，Ship_Turrets §4.6：人照模型外框往外站）：主甲板接得到的 227.26 → 216.08 m²（砲佔約 11 m²）；沒接到的只有 6 塊砲外框的頂面（z 64，各 0.84 m²，不是甲板）與 0.4 m² 碎片；梯子點 0 問題。只加砲具（with_later=1）：227.26。
- 回讀（`verify_step9.json`，`tools/check_guns.py`）：38 個模型 ＝ 設計（work、at、pivot、rotate、scale、mirror、meta 含 arc），沒有多的；CLI `sub=models` 每個都 ✓ ok、印的外框跟用那件自己的格子算的外框差 ≤ 0.045 格（CLI 印到小數一位）；反向對照：設計裡挪 1 格 ⇒ 報 box off 1.045、挪 0.2 ⇒ 0.22。砲具固定點 66／66、關聯 meta kind=gunfittings、繩 110／110 每個欄位一樣；引擎畫出來的砲索沒有頂點在實心裡、最低 z 56.17；掛好的帆布離每門砲（迴旋砲整個 arc）最近 13.84 格（國旗對 迴旋砲-S01）。
- 整船結果帳（`verify_step9_ledger.json`）：23 件作品從 events 重播跟設計逐格比缺 0、多 0、色差 0（舊的 22 件跟 verify_step8.json 一字不差）；引擎 export 235,099 格（234,989 ＋ 砲具 110）＝ 設計、1 元件、空腔 0、鏡像差 0（foc 桿、bumkin 除外）；繩 177、`ropes_broken 0`、`sails_broken 0`、未分組 0。
- 重跑：draft_guns 3 個輸出、draft_gunfittings 4 個輸出兩次 sha256 一樣（guns_placement ae020f72…、verify_guns 1e316f7f…、gun_ropes 22b410af…）；步驟 3–8 的產生程式重跑，輸出全部跟之前一樣（plan.json 只加了兩段、改了 src 字串）。
- 過程圖：`overlays/stage9_main_deck_top.png`（主甲板俯視：砲、環、砲索）、`stage9_port_section.png`（第 5 門砲門的剖面）、`stage9_poop_swivels.png`（船尾樓與舵手台：迴旋砲與砲口掃過的弧）；圖紙 `design/sheet07_guns_v1.png`。3D 全景照舊等有 GPU 的機器。
- 獨立 verifier（子代理，唯讀、自己寫轉換／重播／退砲搜尋／繩管與帆面取樣、不執行作者的程式；報告 Paperclip 工作目錄 `.work/FAR-75/verifier9/report.md`）：先拿引擎 obj 的 34,104 個砲頂點反算驗過轉換式（誤差 0）。8 條 7 條成立、**第 4 條部分成立**：x 110 那對不是「超過 ±65°」才穿過 fall，是負向 −63°、正向 +72°（實際可轉 −62…+71）；±60° 的決定對（弧內最小 0.248，引擎畫的繩管 0.468）。plan 的 arc_src 已照改。它自己的數字：帆面最近 13.90（作者 13.84 是下界）、砲索最低 56.1745、全船 235,099／1 元件／空腔 0、0.5 倍離上楣 0.100、0.55 倍砲口還在船殼裡 3.4–4.4 格。
  - 它另外記的（都照實留著）：O1 第 1 門砲架照規則（內縮 0.2）0 碰撞，但真實方塊跟船殼內側加厚 (80–81, 46／114, 56) 重疊 0.057 格，近看可能看得到；O2 第 4 門在舵手台底下淨高 1.3 m、第 1 門 1.5 m、第 2–3 門 1.7 m（船尾艙），貼牆的梁托下只剩 1.2 m —— 遊戲走路要 1.2 m，砲班站得進去但站不直，步驟 14 匯入看砲班站位；O4 第 10 門往船尾偏 1 格（置中會碰到船殼內面 (256, 41／119, 56)）。後座包絡離所有東西 ≥ 6.2 格、兩門迴旋砲最近 16.3 格。
  - 方法（O6）：引擎的直線繩一條只有 16 個頂點、長三角形可到 60 格 ⇒ 量繩管要沿長邊 ≤ 0.1 格取樣，不能只用頂點或每個三角形固定點數。

## 步驟 10 彈藥庫與甲板物件（2026-11-18）

- 已讀：Ship_Magazine §8（彈藥庫、火藥桶一定放、火藥從艙口吊上去 hoist）、Ship_Fittings §9.7（門與艙蓋）／§9.9／§9.13（廚房）／§9.14（blow）、Ship_Game §9 kind 表（magazine、powder、boat、binnacle、door、galley）。
- 程式：`design/draft_gear.py`（新圖紙 08；出處收穫號 calli-cosecha-01m/design/draft_gear.py 的彈藥庫與模型自動量 z、巴貝多商人號 apex-two-barbados-01m 的莫尼特號艙蓋分軸縮放與爐灶）⇒ `masks/gear/{magazine,skids,hearth}.vox.txt`、`gear_placement.json`、`verify_gear.json`、`sheet08_gear_v1.png`；落格 `tools/build_gear.py`（works／links／models 三段）；回讀 `tools/check_gear.py` ⇒ `verify_step10.json`；整船結果帳 `tools/check_rigging.py --extra=gunfittings:gunfittings/gunfittings,magazine:gear/magazine,boat-skids:gear/skids` ⇒ `verify_step10_ledger.json`；過程圖 `tools/render_gear.py`；走路 `draft_decks.py --probe=with_later=3 --probe=surface=1`（這次加的兩個 probe，不寫檔）。參數 `plan.json` 的 `gear_build`（每一段都有 src）。
  - 跟收穫號不同：實心格讀前面每一步的設計清單（跟 draft_guns 一樣，不開 Server、落格後重跑逐位元組相同）；元件格子存在 `masks/gear_src/`（匯出一次，sha 記在 verify）；砲用砲自己的格（不是外框）當障礙；門先擺、再當其他模型的障礙；多量了 hoist 梯腳 9×9、梯頭站位、門與開口、廚房四面、繩、梯子點、砲的外框。
- 做了什麼：
  | 東西 | 作品／來源 | 掛在 | meta | 說明 |
  |---|---|---|---|---|
  | 彈藥庫 | `-magazine`（新，5,026 格） | 組裝件關聯 `彈藥庫` | kind=magazine, pos=aft, powder_lb=2400, hoist=甲板-main/梯子/orlop,甲板-poop/梯子/quarter-S | 底艙平台最後面 x 96–122、地板 z 36、頂到主甲板板底 z 54；後桅腳 x 106–110 在房間裡當柱子；前牆門 5 寬 × 1.5 m；固定點 blast (111,80,46)、door (122,80,37) |
  | 火藥桶 ×24 | 憲法號 `-powder-barrel` × 0.2 | `-magazine` | kind=powder, powder_lb=100 | 直立一層、每 4.6 格、中線 ±3 走道、兩舷成對；地板放得下 58 桶，cap 24（換算：約 1,900 磅 ＋ 兩成） |
  | 小艇架 | `-boat-skids`（新，460 格） | 組裝件關聯 `小艇架` | — | 三座橫架 x 236／253／269、樑底 z 62、立柱 dy ±12–13 落在艙蓋外的甲板 |
  | 小艇 | 餘燼號 cutter × 0.25（4.5 m） | `-deck-main` | kind=boat, boat=cutter, length_m=4.5 | 擱在小艇架上（z 64）、跨過主艙口；外框中心 x 254 正下方是中間那座架子（foot 0） |
  | 羅經櫃 | 夜隼號 binnacle × 0.2 | `-deck-poop` | kind=binnacle | 舵手台中線 x 133.7–137.3（PT：羅盤在船尾樓前面開敞的地方） |
  | 爐灶（沙箱灶） | `-hearth`（新，0.05 m、4,146 格：柚木箱、沙、三石灶、銅鍋、dallah、柴） | `-deck-main` × 0.5 | kind=galley；固定點 smoke (12,10,15) 在鍋口上 | 船頭水槽左舷 x 302–314、y 60–70；四面外 2 格都站得到人（距離 0） |
  | 艙蓋-主艙口 | 莫尼特號 hatch × (1.2353, 1.6154, 1) | `-deck-main` | kind=door, open=up | 21 × 21 蓋在圍欄頂 z 58；開口 361 格全是空、外框每邊大 1 |
  | 艙蓋-orlop梯 | 莫尼特號 hatch × (0.8235, 1, 1) | `-deck-main` | kind=door, open=up | 14 × 13 蓋在三面圍欄頂 z 58；開口 132 格 |
  | 門-船尾艙 | 藍鯊號艙壁門 × (0.5, 0.7857, 0.4062) | `-deck-main` | kind=door, open=side | 貼在船尾艙前壁 x 124 的船頭面 x 125；11 寬 × 13 高（上面 z 69 是舵手台台階的板，量到就停）；兩邊門框柱都是牆、門洞 117 格（9 × 13） |
  - ⛔ 不放絞盤：PT 寫巴格拉沒有絞盤、用大滑車組起錨（錨纜橫樑步驟 7 已做）。§9.14 blow 沒有要標的。
  - hoist（Ship_Magazine §8）：主甲板 22 門 4 磅砲 ⇒ orlop 梯（梯頭落主甲板；桶擺底艙平台梯腳旁）；船尾樓＋舵手台 8 門迴旋砲 ⇒ quarter-S（梯頭落舵手台；桶擺主甲板梯腳旁）。量到：兩座梯腳旁 4 格內都有 9×9、頭上 0.8 m 空、不碰砲與模型外框的平地，梯頭就站得到。⚠ 寫的是路徑；百夫長號記過 admin.py ids 不拆逗號清單 ⇒ 步驟 14 發 id 後改 `ladders-N#<梯名>`。
  - 彈藥庫跨在水線上：地板 z 36 在水線 z 41 下，房間空氣水線下 4 列、水線上 14 列。Ship_Magazine §8 寫憲法號在水線下；這艘再往下只剩 V 形貨艙（z 20 那層寬 55–63，放得下，但門要比貨艙底高 1.3 m）。量了艦隊：收穫號 46–61／52、聖羅曼號 13–28／24、康塞普西翁號 55–70／60 都跨在水線上 ⇒ 照舊，⚠ 被打到的機會比憲法號大，寫在 plan。
- 讀數（設計，`verify_gear.json`）：模型 30 個（桶 24、門 3、小艇、羅經櫃、爐灶）撞實心 0（樣本 ＝ 格心＋八角內縮 0.2；實心含前面每一步、砲自己的格、先擺的門）、彼此重疊 0、沒 kind 0；腳下 12 格內有實心（門以外）全部 OK；新格落在舊實心上 0、封閉空腔 0、浮空 0；彈藥庫、小艇架、火藥桶鏡像差 0；沙箱灶 1 個連通塊（v1 是 2：鍋離石頭 0.03 格，石頭往裡收一格）。
  - 反向對照（`--probe`，不寫檔）：爐灶往 x 推 30 ⇒ 撞 7,947 個樣本；羅經櫃推 −10 ⇒ 46,422；門推 −1 ⇒ 1,664、推 +1 ⇒ 離牆 1 格；主艙口艙蓋推 −2 ⇒ margin [3, −1, 1, 1]；拿掉羅經櫃的 kind ⇒ no_kind 報它；cap 60 ⇒ 第一層 58 ＋ 第二層 2、木架 74 格。v1 的推法先推再量 z ⇒ 量 z 把它抬開、什麼都報不出來，改成量完 z 才推。
  - 走路（`draft_decks.py --probe=with_later=3 --probe=surface=1`；彈藥庫、小艇架、每個非門模型的外框當實心，門是通道不算）：甲板面全部接到 —— orlop 143.99 → 137.10 m²、主甲板 196.58 → 191.15、船尾樓 77.87 → 77.52（with_later=2 對照）；梯子點 0 問題、梯頂空 0 柱、砲門前 0。
- 回讀（`verify_step10.json`，`tools/check_gear.py`）：三件新作品從 events 重播跟清單缺 0、多 0、色差 0；固定點 blast、door、smoke 一樣，莫尼特號艙蓋與藍鯊號門的 hinge-a／b 在；關聯 `彈藥庫` meta、`小艇架` at 0,0,0；30 個模型 work、at、pivot、rotate、scale、meta 跟設計一樣，CLI `sub=models` 全部 ✓ ok、外框差 ≤ 0.002；反向對照 dx 小艇 1 ⇒ box off 1.0。
- 整船結果帳（`verify_step10_ledger.json`）：25 件作品重播缺 0、多 0、色差 0（舊的 23 件跟 verify_step9_ledger.json 一字不差）；引擎 export 240,585 格 ＝ 235,099 ＋ 彈藥庫 5,026 ＋ 小艇架 460 ＝ 設計、1 元件、空腔 0、鏡像差 0（foc 桿、bumkin 除外）；繩 177、ropes_broken 0、sails_broken 0。
- 淨空：掛好的帆布離甲板模型最近 32.12 格（爐灶對 foc；verifier 的數字，作者的 33.84 用格心減半對角線、不是下界）；直線繩 ≥ 27.31 格；砲口線與後座 0 衝突。
- 重跑：draft_gear 6 個輸出兩次 sha256 一樣（magazine 2864c081…、skids fc5b6287…、hearth ba2a72d0…）；步驟 3–9 的 8 支產生程式重跑，design/ 裡 124 個檔 sha 全部沒變（第一次用 /usr/bin/time 包，這台沒有那支、一支都沒跑卻印了「一樣」，改成看每支 exit 和秒數重跑）。
- 過程圖：`overlays/stage10_magazine_x105.png`（彈藥庫橫剖面）、`stage10_well_y65.png`（水槽縱剖面、沙箱灶）、`stage10_waist_top.png`（船腰俯視）；圖紙 `design/sheet08_gear_v1.png`。圖上的中文字是方框（PIL 預設字型，sheet01–07 也一樣），列進 todo。
- 獨立 verifier（子代理，唯讀、自己寫轉換與重播；報告 Paperclip 工作目錄 `.work/FAR-75/verifier10/report.md`）：8 條 5 條成立、3 條部分成立、0 條推翻。
  - 第 2 條（水線）：房間 79% 空氣在水線上 ⇒ O1，建議請拍板的人明確同意（貨艙 z 5–34 放得下全在水線下的一間）。
  - 第 6 條：orlop 梯口艙蓋船頭那面 x 219 沒圍欄，前緣懸在甲板上 0.2 m；開口照 z 57 量是 145 格、照甲板板 z 55 是 132（O3，看 25_doors.js 取哪一層）。
  - 第 8 條：爐灶離 foc 32.12，不是 ≥ 33。
  - O4（已改）：主艙口艙蓋 scale 1.2353／1.6154 外框到 253.0001／91.0002 ⇒ 改成 21/17、21/13 往下截 7 位（1.2352941、1.6153846），只重掛那一個模型（`GEAR_ONLY`）；門的 scale z 照舊 0.4062。改後 check_gear 0 問題、draft_gear 重跑兩次一樣。
  - 照實留著：O2 主艙口艙蓋掀開會穿過小艇架與小艇（演出）；O5 彈藥庫靠後牆、後桅腳兩旁的通道只有 0.1 m（格子連通來看 24 桶都摸得到）；O6 爐灶在會積水的水槽（遊戲不模擬甲板積水）；O7 船尾樓的取用點在露天主甲板；O8 hoist 路徑寫法；O9 還沒有 kind=ship waterline_z（步驟 14）；O10 門板上緣沒壓到門楣。

## 步驟 11 舵、舵柄、錨（2026-11-18）

- 已讀：Ship_Helm §9.8（spin）、§9.8.1（舵與舵輪、操舵鏈）、Ship_Game §9 rudder／anchor 列（stock-top 8 格、hawse-S／P）；PT 第 30–40 行（多數巴格拉只用很長的舵柄、少數用歐式舵輪；舵桿一直是直的、穿過低而斜的 counter 進船裡）、第 72–86 行（沒有絞盤、錨與錨纜很小；沒有錨鏈孔，艏柱伸出來那段有一個滾輪、另一側常再釘一塊夾板 g 放第二個，P2 fig. 10；沒有吊錨架，出海時錨收上甲板）。P2 fig. 7：舵後緣 1897@1428 → 1929@1165、三道鐵箍。
- 程式：`design/draft_helm.py`（新圖紙 09；出處收穫號 calli-cosecha-01m/design/draft_rudder_anchor.py 的舵沿艉柱、前緣削、鉸鏈在艉柱後緣、錨用搜位置）⇒ `masks/helm/{rudder,tiller,fittings,rollers}.vox.txt`、`masks/step11/{hull,poop,carving}_carve.vox.txt`、`helm_placement.json`、`verify_helm.json`、`sheet09_helm_v1.png`；四爪錨格子 `masks/helm_src/`（匯出一次，sha 記在 verify）；落格 `tools/build_helm.py`（carve／works／links／models／hawse 五段，carve 先重播、已刻的跳過）；回讀 `tools/check_helm.py` ⇒ `verify_step11.json`；整船結果帳 `tools/check_rigging.py`（這次加 `--works=`（模型的子作品只重播、不進 list）與 `--carve=`（刻除清單從設計扣掉））⇒ `verify_step11_ledger.json`；步驟 10 回讀重跑 ⇒ `verify_step11_gear.json`；過程圖 `tools/render_helm.py`；走路 `draft_decks.py --probe=with_later=4 --probe=surface=1`（這次加的 4：步驟 11 的格與錨外框當實心、扣掉舵孔）。參數 `plan.json` 的 `helm_build`（每一段都有 src）。
- 做了什麼：
  | 東西 | 作品／來源 | 掛在 | meta | 說明 |
  |---|---|---|---|---|
  | 舵 | `-rudder`（新，1,832 格：舵葉 1,606＋舵桿 226） | 組裝件模型 `舵`，at ＝ pivot ＝ 鉸鏈 (60.0, 80.5, 0) | kind=rudder、hinge (60.0, 80.5, 0)、axis (−0.2795, 0, 0.9601)、max_deg 35、turn_axis=hinge、spin=rudder、spin_k 35、±35、lag 0.3 | 舵葉 z 0–52、寬 15 → 6 格（P2）、厚 3、z 42 以下白；三道鐵箍 z 7／24／41；舵桿半徑 1.5 以鉸鏈軸為中心，z 53 → 82 穿過艉柱頭與 counter、船尾艙（中間那扇船尾窗後面）、船尾樓甲板；stock-top (35, 80, 82) |
  | 舵孔 | 刻 140 格：船殼 115、船尾樓甲板 21、船尾雕花 4 | — | — | z 52–73、每層水平距離軸 2.3 格內＋舵桿轉 ±35° 會掃到的格（多 6 格，2 格在 z 52）；舵桿外一圈縫從甲板通到 counter 下面（水線上） |
  | 舵頭圈 | `-helm-fittings`（新，48 格） | 組裝件關聯 `舵頭圈` | — | 船尾樓甲板上孔邊一圈 0.2 m 高；讓 stock-top 7.0 格內有船格（板在 9 格外） |
  | 舵柄 | `-tiller`（新，399 格） | 組裝件模型 `舵柄`，at ＝ pivot ＝ 鉸鏈 | kind=tiller、spin 同舵、spin_pivot／spin_axis ＝ 舵的鉸鏈 | 船尾樓中線 x 37–88、z 79–81（甲板面 74 上 0.5–0.8 m），最後 14 格 2 格高、最後 5 格 1 格寬的黑握把；離鉸鏈軸 5.24 m |
  | 艏柱滾輪 | `-stem-rollers`（新，80 格） | 組裝件關聯 `艏柱滾輪` | — | 船頭舷頂上艏柱兩側各一塊夾板（x 368–372、y 82–83／77–78），滾輪在靠艏柱那一格的槽裡；位置由程式找（x 374–378 會擦到主帆 tack） |
  | hawse | 船殼固定點 | — | hawse-S (370, 82, 76)、hawse-P (370, 78, 76) | 滾輪頂 |
  | 錨 ×2 | 共用四爪錨 `kotoko-fusta-01m-anchor-grapnel` × 0.5（0.9 × 0.9 × 1.2 m） | `-deck-main`：錨-S (319.5, 90.5, 51)、錨-P (319.5, 70.5, 51, mirror=y) | kind=anchor、anchor=bower、hawse ＝ 滾輪頂 | 收在船頭水槽甲板上（PT：出海時錨收上甲板），靠兩舷、爐灶前面；中間留 1.1 m 走道 |
  - 為了長舵柄搬的兩樣：步驟 8 的後桅小繫索柱 x 69–71 → x 100–102（`delta_apply` 刻 63、補 63；固定點 halyard-mizzen (99, 80, 79)；大滑車跟著移到 x 104；`build_rigging.py anchors ropes` 重掛）；步驟 10 的羅經櫃 舵手台 (135.5, 80.5, 70) → 船尾樓 (93.5, 80.5, 74)（`GEAR_ONLY=羅經櫃 build_gear.py models`）。PT：羅盤和舵手在一起。
  - ⛔ 沒有舵輪：PT 寫多數巴格拉只用舵柄（Ship_Helm §9.8.1：reale、fusta、dromon、punt 也沒有舵輪；舵柄做成獨立模型 kind=tiller ⇒ 操舵鏈有操作端那一節）。Senate 驗收格寫的「舵輪＋座」照這個改。
- 讀數（設計，`verify_helm.json`）：
  - 舵：靜止時碰實心 0、碰模型 0；整件繞鉸鏈軸 −35…+35°（每 1°，樣本＝格心＋八角內縮 0.2）碰船 0。舵葉每 (y, z) 從後緣往前長到「整個轉動範圍都不碰艉柱」為止 ⇒ 前緣離軸 0.5–1.99 格（第一版前緣貼到艉柱線，±30° 以上掃進艉柱 45 點）。舵桿到船尾窗玻璃最近 1.41（格心距離，貼在中間那扇窗後面、不碰）。
  - 舵柄：整個轉動範圍碰實心 0、碰模型 0；最低點 z 76.92（格角精確量；傾斜的軸讓尖端往下約 3 格，甲板面 74）；離繩 ≥ 10.43；尖端到羅經櫃 2.7 格；鏡像差 0。
  - 滾輪：撐得住（舷頂與甲板 z 71–73）、不碰、鏡像差 0、離繩 ≥ 1.28（主帆 tack；verifier 量到表面 1.77）；錨：碰撞 0、腳下間隙 0、鏡像差 0、離爐灶 1.58（格心）、離繩 ≥ 25.13；錨纜線 hawse → 錨纜橫樑頂 7.44 m、不穿過實心、離爐灶 ≥ 16.64。
  - 一件連通：舵＋舵柄 1、舵頭圈 1、滾輪 2（兩舷各一）；梯子點 0 被擋。
  - 反向對照（`--probe`，不寫檔）：nofit ⇒ 舵掃到艉柱 45 點；noswept（只刻圓孔）⇒ 舵桿擦孔邊 5 點；舵柄 tip 96 ⇒ 撞羅經櫃 99 點、tip 101 ⇒ 261；錨 dx −6 ⇒ 錨-P 撞爐灶 468、dx +8 ⇒ 兩隻各 54。探針跑完輸出 sha 沒變。
- 回讀（`verify_step11.json`）：4 件新作品＋3 件被刻的作品重播缺 0、多 0、色差 0，刻除清單裡的格 0 格還在；stock-top、hawse-S／P 一樣；關聯 舵頭圈、艏柱滾輪 at 0,0,0；4 個模型 work／at／pivot／rotate／scale／mirror／meta 一樣、CLI `sub=models` 全部 ✓ ok、外框差 0；船尾雕花模型 ✓ ok；export format=parts：舵、舵柄都有 spin=rudder、兩隻錨都有 hawse、沒有 kind=wheel；掛好的帆布離新零件：作者寫 2.46（滾輪對主帆），verifier 量到 ≤ 2.14 ⇒ 照 2.14 寫。反向對照：錨-S 挪 1 格 ⇒ box off 1.0。
- 整船結果帳（`verify_step11_ledger.json`）：29 件作品重播缺 0、多 0、色差 0；引擎 export 240,577 格 ＝ 240,585 − 舵孔 136 − 舊繫索柱 63 ＋ 新繫索柱 63 ＋ 舵頭圈 48 ＋ 滾輪 80 ＝ 設計，1 元件、空腔 0、鏡像差 0（foc 桿、bumkin 除外）；繩 177、ropes_broken 0、sails_broken 0；繩 67／帆 5 跟 rigging_plan 一樣。
- 步驟 8、10 重跑：`check_sails_sim` 讀數跟 `verify_step8_sails.json` 一字不差；`check_gear` 0 問題（兩隻錨記成已知）、外框差 ≤ 0.002；`draft_rigging` 的 verify 只變了 mizzen 升降索那幾條（fall 離實心 0.36、在自己的繫索柱旁；block 0.51）。
- 走路：with_later=3 ⇒ 4，主甲板 191.15 → 189.37 m²、船尾樓 77.52 → 75.99 m²，全部接到；梯子點 0 問題、砲門前 0。
- 重跑：10 支產生程式跑兩次，design/ 141 個檔 sha 一樣；跟步驟 11 前的備份比，只變了預期的檔（plan、draft_rigging／draft_decks、rigging 與 gear 的輸出、sheet06／07／08，加上新的 helm 檔）。sheet07 變是因為它畫到搬走的繫索柱。
- 過程圖：`overlays/stage11_stern_starboard.png`、`stage11_poop_top.png`、`stage11_bow_starboard.png`；圖紙 `design/sheet09_helm_v1.png`（英文字，避開沒有中文字型的問題）。
- 獨立 verifier（子代理，唯讀、自己寫轉換與重播；報告 Paperclip 工作目錄 `.work/FAR-75/verifier11/report.md`）：8 條 4 條成立、4 條部分成立、0 條推翻。改了：舵柄最低點 76.92、滾輪離帆 ≤ 2.14、刻除範圍 z 52–73、算式補繫索柱、sheet09 補畫羅經櫃與標籤、plan 兩段說明。O1（舵手位置的詮釋）、O2（滾輪不在艏柱本身）問 Tim。

## 步驟 14 給遊戲的 meta 與匯入（2026-11-18）

- 已讀：Ship_Game §9／§9.4／§10／§12；Blockside `src/README.md`（import／ids／shipcheck／ladcheck）、`js/23_powder.js`（hoist 取用點）、`js/75_shipcheck.js`、`js/75_leakcheck.js`。
- Tim 在 FAR-75 卡片回答：舵柄與羅經櫃照現在（船尾樓頂）、滾輪照現在（兩塊夾板）、彈藥庫照現在的位置；Blockside ＝ Blocksail 的 submodule `external/Blockside`（`dev`）。
- meta：船殼關聯 `kind=ship, waterline_z=41`；foc桿 的 `kind=mast, mast=bowsprit` 拿掉（匯入檢查 ⚠：沒有帆桁綁 bowsprit ⇒ 遊戲不認；`tools/build_masts.py` 跟著改成清掉）。
- ropecheck（`work sub=ropecheck`，只讀）：ok 280、onrope 74，沒有 bind／snap／odd／manual／broken。
- 匯入：在 Paperclip 工作目錄另外 clone 的 Blockside `dev`（749b867）暫存副本跑，⛔ 沒提交、沒推。代號 `najm`、名字 星辰號。
  - 暫存副本的環境（只影響這份副本，不是作品的問題）：這台是 Linux、沒有 Chrome ⇒ 用 Debian chromium-headless-shell（使用者空間）；Blockside 的 Chrome 路徑只寫了 Windows 的 ⇒ 執行包裝蓋掉、`tests/render_lab/cdp.py` 加了 `BS_CHROME`；node 的 `console.log`＋`process.exit(0)` 在 Linux 的 pipe 會截在 64 KB ⇒ 包裝改用暫存檔讀；選船卡縮圖沒拍（軟體算圖要一小時、成品不提交）。
  - 艦隊其他 52 艘的 `_cache` 是從這台 Sculpture（tim099/Sculpture master）重新匯出的，54 艘指紋全部對不上（作品版本不同）、`kroon`、`tungning_trader` 的作品這台沒有 ⇒ 暫存副本裡 relock、拿掉那兩艘。只拿來跑星辰號的檢查。
- `admin.py ids`：發 100 個 id（寫回 8 件作品，persona=Claude-Ojousama，`meta_log.jsonl` 有紀錄）。它換不了逗號清單的 hoist ⇒ 手寫 `hoist=ladders-2#orlop,ladders-3#quarter-S`（plan `gear_build.hoist_ids`、`draft_gear.py` 照它寫 meta）；8 個迴旋砲座補 `mount_of=gun-23…gun-30`。
- 匯入檢查（`reports/shipcheck_najm.md`，重匯後）：**✗ 0、⚠ 14**；樓梯自檢 ✗ 0、⚠ 1、✓ 3；甲板連通 3 層＋艙底都接得到。
  - 火藥 30／30 門走得到取用點（取用點 2：主甲板走 orlop 梯、船尾樓走 quarter-S 梯；第一次匯入用路徑寫法時船尾樓那層找不到 ⇒ ✗，改 id 寫法後好了）。
  - 砲身與砲座 8／8 配到；操舵「舵令 ⇒ 舵柄 ⇒ 舵 100%」；轉動列出舵、舵柄（±35°）；錨兩隻都有模型＋ring＋hawse；廚房站得住的面 4；門 3 扇（主艙口 361 格、orlop 梯口 145 格、船尾艙門洞 117 格）。
  - 繩端綁定（`reports/ropebind_najm.md`）：177 條，格子 260、母繩 50、模型（寫明）40、帆角 4；照外框猜 0 端、不靠 0 端。
  - 材質：橡木 240,221 格 168.2 噸、玻璃 356 格 0.9 噸。
- 留著的 ⚠（看過、理由）：
  - geo 沒填、軍官 0／4、陸戰隊 0／12、桅頂水手 0／8、航海士 0／1：遊戲那側填 `ships[].geo` 與船員配置（三角帆船沒有桅頂平台，桅頂水手要遊戲那側決定）。
  - 砲班站不滿 4 門（M-P03／P04／S03／S04，1／2 人）：在舵手台底下，淨高 1.3 m（步驟 5 為了讓主甲板接得通把舵手台抬到 70 的代價；verifier 9 O2 記過）。
  - 貨艙梯子「梯腳判不出在哪一層」×2：貨艙不是一層甲板，Ship_Decks ⑥ 寫明貨艙梯子尋路不收、照報 ⚠。
  - 漏水 ×3（再吃水 1.00 m、多載 207 噸）：漏點 x 299–301／315、水位 z 51 ＝ 水槽兩舷的排水孔（plan `scuppers` x 300／316、貼著水槽甲板面 z 51）；錨纜橫樑在頭上 ⇒ 遊戲把水槽算成有蓋的艙。照 PT 做的設計，沉沒線還在 +4.2 m。
- `.vxk`（暫存副本，重匯後）：240,577 格、checksum 4232715023、繩 177、帆 5、模型 76、部件 25、owner Claude-Ojousama；指紋 `c:71aff2cc857298d7309326b3ec4361bb46b1676f`。⚠ 作品之後再改會變，正式匯入時以遊戲那側匯出的為準。
- render：火藥桶（憲法號的桶）本來就有 `render=lathe`；新做的爐灶、舵、舵柄不是繞軸對稱，不標。

### 給遊戲那側填 geo 的高度（格；0.1 m／格，z 0 ＝ 龍骨底）

| 項目 | 值 |
|---|---|
| 設計水線 | z 41（4.1 m）；水線長 x 48–321（27.4 m）、寬 y 33–127（9.5 m） |
| 船殼前後端 | x 21（taffrail）– 378（艏柱頭）；foc 桿尖 x 408.9；中線 y 80 |
| 底艙平台 | 甲板面 z 36（x 96–290） |
| 主甲板 | 甲板面 z 56（x 46–259），舷弧到 58（x 280），船頭水槽 z 51（x 290–332），往艏柱升到 73 |
| 舵手台 | z 70（x 125–150） |
| 船尾樓 | z 74（x 33–124） |
| 4 磅砲砲軸 | z 62.42（甲板 56）／63.42（甲板 57），砲口伸出船殼 2.3–4.3 格 |
| 迴旋砲砲軸 | 舵手台 z 84.7；船尾樓 z 87.7–89.7 |
| 桅頂 | 主桅 z 283、後桅 z 206（三角帆，沒有桅頂平台） |
| 帆頂 | 主帆桁頂 z 321、後桅帆桁頂 z 240；長旗 z 283 |
