# 蘇士奎哈納號（USS Susquehanna，1850）—— 打破日本鎖國的黑船（0.1 m／格）—— 建造筆記

委託：Tim 2026-10-18（/scp-shipbuilding，傘單 TASK-0697）：「按照遊戲用的規格造船吧 建造打破日本鎖國的黑船吧 參考裡歷史資料與圖紙 最後由妳繪製圖紙並建造(資訊不足的部分由妳設計) GO」。
選船：**蘇士奎哈納號** —— 1853-07-08 培里艦隊進浦賀時的旗艦（明輪蒸汽巡防艦）。作者 crest-001。造船規格見 Senate `Docs/Workflows/Sculpture_Shipbuilding.md`。
範圍（遊戲用）：外部完整；內部做甲板、艙口、梯子、彈藥庫、艙房、機艙（主機、鍋爐、明輪軸）這些遊戲用得到的構造。

## 座標約定
- 空間 1300×400×800；X 船長（船頭 +X）、Y 船寬（中線 ＝ 第 200 格，鏡像 y ↔ 400 − y）、Z 高度（z 0 ＝ 龍骨底面）；P ＝ y < 200。每件都記了 meters_per_voxel 0.1。
- 收緊框的子作品（明輪罩、主機、明輪軸、channels、彈藥庫、艙房、鍋爐…）：關聯 at ＝ 框原點；左舷鏡像關聯 at.y ＝ 401 − at.y − 高（整船框的子作品沒辦法對 y 200 鏡像 —— at.y 要 1 會越界）。

## 史料與設計方向
- 史料：`references/susquehanna_research_2026-10-18.md`（研究 agent；每個數字附網址與 opened／snippet／LOW）。一手：STUART 1853（The Naval and Mail Steamers of the United States，pp. 83–85＋附錄 Note G：Powhatan／Susquehanna 建造規範）、BARTOL 1851（Marine Boilers, p. 2）。
- **沒有找到蘇士奎哈納號的線形圖／側面圖** ⇒ 位置（桅、明輪、煙囪）量姊妹艦 Powhatan 的 1853 石版畫（`references/05_*`，同一份規範）；塗裝看 1853 日本畫師的圖（01）、1857 油畫（03）、1860 年代照片（02）；船首像照 NARA c. 1850 設計圖（06）。
- 管線：照抄光榮號（kaguya-gloire-01m，同樣約 78 m 的蒸汽巡防艦）`design/` 整套，每支檔頭註明；機艙的做法參考拿破崙號（kotoko-napoleon-01m）。crest-001 新寫：`draft_paddles.py`（明輪罩＋明輪）、`draft_pivots.py`（迴旋砲）、`draft_machinery.py`（機艙）、`tools/plan_init.py`、`tools/apply_paddles.py`、`tools/apply_machinery.py`。
- 新圖紙：`design/plan.json`（每個數字 src：史料／設計決定）、`sheet01_lines` … `sheet07_machinery`。

## 主尺寸（讀數 vs 史料）
| 項目 | 讀數 | 史料 |
|---|---|---|
| 水線長（z 56） | 76.2 m（762 格） | 250 ft（吃水 18½ ft，STUART） |
| 甲板長 | 78.2 m（x 133–915） | 256 ft 6 in on deck（BARTOL） |
| 寬 | 13.7 m（137 格） | 45 ft（STUART／BARTOL） |
| 寬過明輪罩 | 21.0 m（|dy| ≤ 104.5） | 69 ft over guards（STUART） |
| 設計水線 | z 56 | 平均吃水 18 ft 6 in（BARTOL） |
| 排水量（水線下實心 × 1.025） | 3,528 t | 18½ ft 內插約 3,550 t（STUART：17½ ft 3,277／19½ ft 3,824） |
| 甲板 | 底艙 z 45、住艙 z 65、砲甲板（露天）z 89 | Note G：orlop、berth、gun deck（舷牆直接蓋在 gun deck 上） |

## 部件（組裝件 `crest-001-susquehanna-01m-assembly`「蘇士奎哈納號」）
- `船殼` meta kind=ship、waterline_z=56；木殼牆 4 格，水線下包銅到 z 54、以上黑（黑船）；舷牆頂 z 109（甲板 ＋ 2 m）。
- 甲板：`甲板-engine`（機艙鐵地板，level −1）、`甲板-orlop`（0）、`甲板-berth`（1）、`甲板-gun`（2，露天）；梯子：每兩層前後各一座＋機艙一座陡梯（`甲板-berth/梯子-機艙`，`engine-berth.decks`）。
- 砲門：明輪後面每舷 3 個舷牆砲門（z 97–105）；住艙甲板兩排通風舷窗（Note G 的 air-ports）；船尾住艙窗 5 扇。
- **明輪**：`明輪罩`＋`明輪罩-鏡像`（扇形通風槽＋百葉、白邊、前後側台與斜撐）；`明輪-S`／`明輪-P` 外部模型 **kind=propeller、axis 0,1,0（往前走時輪頂往前）、blades 26、diameter_m 9.5、rpm_max 12**，平移放、固定點 hub／shaft-fwd（造船規格 §9.6）。直徑 31 ft 2 in、寬 9 ft 6 in、26 片徑向槳板、吃水 16 格 ＝ 史料 64 in。
- 機艙：`主機-S`／`主機-P`（斜置直動式、汽缸 70 in × 10 ft；kind=engine、engine=inclined、kn 10、material=iron）、`鍋爐-後`／`鍋爐-前`（各兩座銅鍋爐、背靠背；kind=boiler、boilers 2、funnel=煙囪、material=boiler＋render=smooth）、`明輪軸-S`／`-P`（kind=shaft，7 格粗，穿船殼那段借船殼）、`軸罩`（砲甲板上的木罩：軸從甲板板底下過 ⇒ 板開縫、上面蓋罩）。
- `煙囪`（kind=funnel、material=iron、render=smooth、smoke 567,200,210；從鍋爐頂 z 52 接上來）。
- 船頭：`船頭`（knee of the head＋trailboard 金色花藤與橡實）、`船首像`（鷹：金身白頭黃喙，NARA 設計圖）、`head-rails`、`吊錨架`；船尾 `船名板`「SUSQUEHANNA」、船尾燈 3 盞（三叉戟號元件）；舷牆頂 `hammock` 白帆布。
- 桅：barque —— 前桅、主桅 course／topsail／topgallant／royal（三叉戟號帆桁 × 縮放），後桅只有 gaff＋boom；艏斜桅＋jib-boom；channels；靜索 135、橫繩組 12（下桅 6 組是繩梯 climb=1）、帆 13（含 1853 年 31 星星條旗 ensign、commission pennant），帆與帆自己的繩全標 meta。
- 砲（1853 年配置沒有一手出處 ⇒ 設計決定，照 PINEAU 6＋3、密西西比號）：明輪後面每舷 3 門 8 吋 Paixhans（元件餘燼號 -gun-long32 × 0.5，**代碼借 9d**）＋船頭兩舷各一門、船尾一門 10 吋 Paixhans 迴旋砲（× 0.55、**代碼借 11d**、mount=pivot：船頭 ports 0,∓45、船尾 −20,0,20）。
- 彈藥庫兩間（各 16 桶，⚠ 照砲數換算）、舵（模型 kind=rudder＋spin ±35°、stock-top）、舵輪＋舵輪座（spin 540；x 200，讓出船尾迴旋砲的砲班）、羅經櫃、主絞盤、小艇兩艘（先擱甲板）、錨兩隻（共用錨 × 0.85）＋hawse、orlop 艙房兩舷各 11 間。

## 讀數
- 組裝件：1,789,772 格、1 元件、封閉空腔 0、link_overlap 0；鏡像差只有船名板的字（31 對）。
- 結果帳：船殼、甲板、梯子、裝飾各件 ↔ 設計清單逐格逐色 缺 0／多 0／色差 0（船殼反向對照推 3 格 ⇒ 缺／多各 82,152）。
- 明輪：輪碰船殼／箱 0、轉一整圈掃到 0、兩舷鏡像差 0。
- 桅：浮空 0、空腔 0、甲板孔全填滿；帆桁在 brace 角掃過的線碰船 0；繩 broken 0、帆 broken 0、模型 broken 0。
- 砲：舷側 6 門零碰撞、輪子全著地、砲口伸出；迴旋砲每個角度砲口都在船外、模型不碰東西（船頭那兩門輪子著地 75%）。
- **匯入檢查**（Blockside 暫存 worktree、`admin.py import --id susquehanna`，⛔ 沒動共用工作區；副本補 geo、drive=steam、cfg.base 10）：**✗ 0、⚠ 0**。額外動力：明輪-S 50%、明輪-P 50%；主機 2、軸 2、鍋爐 4 座；火藥 9／9 門走得到取用點；材質 橡木 989 t、鍋爐 281 t、鐵 505 t。
  第一次 ⚠ 1：船尾迴旋砲砲班 7／8（舵輪貼在砲尾後面）⇒ 舵輪往前挪到 x 200 ⇒ 0。
- vxk：`crest-001-susquehanna-01m-assembly/exports/susquehanna.vxk`（不進版控）1,789,772 格、checksum 07b53e42；繩 431、帆 13、模型 65（網格 36）；材質 boiler 311,998、iron 64,684 格。

## 給遊戲那側填的（ships[]）
- 暫存副本試過的整組（✗ 0 ⚠ 0）：`"drive": "steam", "cfg": {"pump": 15, "base": 10}, "geo": {"spar": [90, 104], "marines": [80, 200], "center": 150, "aim": 85, "aimZ": [30, 480], "deckAim": [90, 110], "rigAim": [200, 470]}`（pump 是猜的）。
- 水線 56；甲板地板（第一層空氣）機艙 12、orlop 46–55、住艙 66–78、砲甲板 90–103；舷牆頂 109（船頭 121）；**geo.spar 建議 [90, 104]**（砲甲板）。
- 砲口：舷側 z 約 101、迴旋砲 108–109；桅頂平台 主 242、前 231、後 226；truck 主 500、前 472、後 384；艏斜桅尖 x 1,071、jib-boom 1,142。
- 動力：drive=steam、cfg.base **10**（DANFS 10 kn；只靠帆 8¼ kn，STUART）；兩具明輪（kind=propeller）平分動力。
- 砲種：8 吋、10 吋 Paixhans 遊戲沒有 ⇒ 先借 9d／11d；要不要加新砲種由遊戲那側定。

## 已知、照實留著
- 1853 年的砲、桅與帆桁尺寸、船尾裝飾、小艇與錨都沒有一手出處（設計決定，見 plan.json src）。小艇照片是掛在船尾 quarter davits，遊戲的小艇模型掛著會被當吊艇擺 ⇒ 先擱甲板。
- 船頭兩門迴旋砲的輪子著地 75%（船頭甲板舷弧）。
- 艏斜桅穿過 knee 頂 43 格、後桅腳壓到 orlop 26 格（都是現況先有的格，桅讓）。
- 4 條繩拉直時擦到 1–2 格（futtock 5 號、fore-topmast-stay、bobstay-2）。
- 明輪軸 r 3 從砲甲板板底下過、板開縫蓋軸罩（史實是曲柄箱，設計簡化）。
