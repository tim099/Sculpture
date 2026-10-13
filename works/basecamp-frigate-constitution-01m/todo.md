## 階段四 TASK-0484（2026-10-11 雕完）
- [x] 59 片底肋（facing=x+，先貼 f+00 驗軸向）＋ keelson；兩處設計不一致已修（底肋讓出 keelson 180 格、keelson 座位補 20 格），讀數見 notes.md「階段四」
- [x] 驗收：結果帳 0 差、接合沒洞、側面／橫剖面疊新圖紙 03、反向對照偏 3 報 3、船中 vs 15 號 ≤ 0.73 格
- [x] 製作筆記 `journal/`（心路歷程，連 `overlays/` 的圖）

## 階段五 TASK-0485（2026-10-11 雕完）
- [x] 新圖紙 04 肋骨圖 v1 ＋ 雙肋 132 片（f −40..+25，futtocks・top timbers，全部同色 141），讀數見 notes.md「階段五」、心得 `journal/stage5.md`

## 下次從這裡接
- [ ] 階段六：**船頭與船尾**（TASK-0486）—— ✅ 讀圖（10-11 凌晨）→ ✅ 新圖紙 03 v2 船殼延伸、04 v2 兩頭骨架（10-11 存檔點，**還沒雕**；讀數見 notes.md「階段六」、心得 `journal/stage6.md`）
  - [x] `stampvox`（TASK-0487）提交＋出廠（SCP_Core e1869a1、Senate 463ed65；2026-10-11 出廠）
  - [x] 雕之前修（2026-10-11 wake #130；做法與讀數見 notes.md「階段六 雕之前修」）：
    - [x] 船尾 Z 126 以上 nan：根因是 9 號站本身在 126.1 以上就算不出值（1–9 號站的樣條跨站），`_taper` 只是其中一處 ⇒ ztop9 夾到有效高度
    - [x] 船尾 B 水線改用 B 自己的描線（本 session 沿線追蹤）；同時船尾 g_end 1.6 → 2.5、接縫補正只攤 16 格 ⇒ 六條水線 vs 原圖最大 ≤ 0.58
    - [x] 高度換算改成一致的形式，重算 counter／船尾面（同一個 z 的 X 差 −0.71..+0.75）
    - [x] 窗台、窗楣、taffrail、wing transom 從 dy 0 起
    - [x] 艉柱 head_z 88 → 81、內艉柱 82 → 75（雕刻時先刻 370 格）
    - [x] 懸出部側面：雙片的方 quarter timbers（X 122–127、115–120、108–113、101–106）
    - [x] knighthead dy [5,8]＋dy 3–4 的 chock；hawse 4 根各 4 格；船頭 cant 雙片 6 對（弧長等分）
    - [x] transoms 改成連續的水平帶子（Z 70–74…49–54）；針孔、夾縫、碎塊照 fill 規則
    - [x] 文字（cant 22.5°、wing transom 27.9 ft、hawse、transoms、counter 寬度）；verify 報「計畫 vs 清單」的 x／z／dy 不符
    - [x] 重產 → 再派 verifier（第二輪，3 個：木料帳 fail、船殼 fail、美觀 pass_with_minor）→ 照它們的讀數修完，本小姐自己量（同一對 cant 的缺口 0、舷頂接縫無台階、接縫的縫 1 格、從船尾看的洞只剩窗位）。第三輪沒派 —— Tim：「細節放上去之後再細修，不用一次到位」
  - [x] 雕（2026-10-11）：先刻柱頭 4 盒 370 格 → 51 根逐根 stampvox，每根 placed ＝ 清單格數、總數差 ＝ 清單格數；363,037 → 435,561
  - [x] 雕完：結果帳 0 差（`design/tools/ledger_stage6.py`）、1 元件、空腔 0、匯出 87,698 面、過程圖 `overlays/stage6_*`
    - ⚠ 沒做「疊新圖紙 04 v2」與它的反向對照：04 v2 是從同一批清單畫出來的，拿作品去比它只會證明作品＝清單（結果帳已經證明了），是同源的證人。設計＝原圖那本帳在船殼（03 v2 vs 11 號，兩位 verifier 量過）
  - [x] 驗收那格「延伸段 vs 11 號 ≤ 1 格」：Tim 2026-10-11 接受船頭的誤差（已簽）；船尾 B 改用自己的描線之後 ≤ 0.54
  - [ ] **放上去之後再細修**（Tim 2026-10-11：「細節可以實際放置上去後再細修，不用一次到位」；讀數見 notes.md「階段六 雕之前修＋雕刻」）：
    - [ ] 艏柱頭後面中線的槽（dy 0–2、X 665–671、夾在兩根 chock 之間，約 11 格深）—— 做 bowsprit 時決定要填還是當 bowsprit 座
    - [ ] S-counter-timber-35 在 Z 81 多 3 格 dy 34（舷邊那根的碎塊歸過來的）
    - [x] 上層船尾窗（Z 113.6–123.8、hb 18.25–28.22）被 dy 25–26 的 counter timber 穿過 —— 階段十四決定不開（照現代照片，那裡放鷹與星），timber 留在外板裡面看不到
    - [ ] 船頭 cant 根部擠在一起、後片沒碰到 deadwood／apron（只靠鄰片撐）
    - [ ] 高度換算的 LWL 用直線擬合，船尾那段可能偏高 0.6–0.9 格（verifier minor，證據兩邊都有）—— 砲門那段（X 185–625）量過不影響（≤ 0.26 格，階段七）；只剩船尾 X < 185 的 counter／船尾面
    - [ ] 階段二 gripe 在 Z 66–67 伸出艏柱前面一塊平台 —— knee of the head 子作品時處理
    - [ ] 階段五的方肋頂沒照 sheer_points 起翹（船頭幾乎沒有 sheer 上揚）—— ⚠ 鋪了外板之後這條線變得很顯眼（`overlays/stage7_view_side.png`：白帶照 sheer 往船頭翹，舷頂幾乎是直的，兩條線不平行 ⇒ 船頭看起來往下垂）
      - **拍板（Tim 2026-10-11 交給本小姐、美觀為主）：照 sheer_points 起翹**；在肋骨頂與外板上面往上補（不用拆），跟舷牆（spar deck 那一層）一起做
## 階段七 TASK-0489（2026-10-11 雕完）
- [x] 讀圖：11 號 gun deck 砲門 14 個（`design/source_ports.json`）＋ Humphreys 1794 規格（wales、black strakes、船底板、砲門）
- [x] 新圖紙 05 外板與塗裝 v1（`design/draft_planking.py`、`sheet05_planking_v1.png`）：dubbing（overwrite 蓋掉凸出 molded 線的 3,698 格）、外板 1 格、wales 2 格、銅／黑／白帶、結構露在外面的那層上色
- [x] 雕：8 刀 stampvox，435,561 → 593,700；結果帳 0 差、不漏水、反向對照會叫、1 元件；過程圖 `overlays/stage7_*`、心得 `journal/stage7.md`
- [x] LWL 那題對砲門不影響（直線擬合 vs 圖上畫的 LWL ≤ 0.26 格）

## 階段八 TASK-0490（2026-10-11 雕完）
- [x] 船頭那個砲門（平行四邊形）讀圖；新圖紙 06（`design/draft_ports.py`、`sheet06_ports_v1.png`）；44 刀 carve ＋ 砲門框 416 格；593,700 → 586,192；結果帳 0 差、透光、框沒有縫、1 元件、反向對照會叫（`design/tools/check_ports.py`）；標記 `砲門:begin／end`
- [x] 雕完派的 3 個 verifier（原圖幾何／帳與結構／外觀）：無 blocker；第 4 個砲門白帶、船頭砲門後壁的縫、兩個單格空腔 ⇒ 細修 v1.1 已修（586,200）；讀數見 notes.md「階段八」
- [x] 階段七外板封住的封閉空腔 ⇒ 2026-10-11 補實（Tim：「用鄰近 voxel 顏色填滿」）：2,200 個／5,602 格、`design/tools/fill_cavities.py after_stage8`、標記 `補空腔:begin／end`；591,668、空腔 0、匯出 120,832 → 107,225 面（notes.md「補空腔」）
  - [ ] ⚠ 之後每鋪一層封得住空氣的東西（內板、甲板…）都會封出新空腔 ⇒ 那一階段收尾時再跑一次 `fill_cavities.py <名稱>`
- [x] 白帶補漆的兩角（第 4 個左上角 (283, 99) 等）⇒ v1.2 一起補（第 4／13／14 個共 10 格）
- [x] `check_ports.py` 砲門框量不到 cant 那一帶 ⇒ v1.2 加「牆不能有洞」那一格（從產物量；反向對照會叫）
- [x] 船頭那個砲門斜看有鋸齒（格子表現斜邊）—— Tim 目視檢查過砲門：「沒問題的」（2026-10-11）
- [x] **v1.2 船頭砲門改垂直**（Tim 2026-10-11 稍晚：「船頭的炮窗 試著雕刻成垂直的吧」＋示意圖 ＝ 平行四邊形的外框 X 643..651）：草稿（刻 138／補 4／補漆 16）→ Tim「套用吧 GO」→ apply；586,066；`砲門:end` 已移（notes.md「階段八 v1.2」）

## 階段九 TASK-0496（2026-10-11 雕完）
- [x] 讀圖＋資料（04／15 號、Humphreys、Martin《Close Up》、1816 Waldo、1931 inboard profile）；新圖紙 07（`design/draft_interior.py`、`sheet07_interior_v1.png`）；甲板高度定案（分段平整、高低差在艙壁；Tim「甲板大致平整」）
- [x] 內板、limber、clamps／stringer／spirketting、斜肋 6 對、hooks、舷頂封口、中線換色、補空腔 ⇒ 817,010；v1.1 橫向 rider 14 根 ⇒ **821,444**；標記 `船殼內部:begin／end`；`check_interior.py` 全過、反向對照會叫（notes.md「階段九」）
- [x] keelson 兩側那道 1 格縫：內板蓋掉
- [x] 甲板高度那題 ⇒ 定案在 plan.json `interior.decks`（砲門那邊＋15 號 ＋2）；~~甲板跟著 sheer 走（每個 X 一個值）~~ ⇒ Tim 要大致平整，改成分段平、折在艙壁

## 階段十 甲板子作品（2026-10-11 套用）
- [x] 新圖紙 08（`design/draft_decks.py`、`sheet08_decks_v1.png`、`verify_decks.json`；設計與出處在 plan.json `deckworks`）
- [x] 建子作品（parent_work ＝ 本作品，免費）：`-deck-orlop／-deck-berth／-deck-gun／-deck-spar`，尺寸 ＝ 船殼
- [x] 組裝件 `basecamp-frigate-constitution-01m-assembly`「憲法號（組裝）」—— Tim：「開一個作品來組裝憲法號，目前的作品就作為船殼部分」「另一個作品本身只做組裝工作」⇒ 一格都不雕、只有關聯：船殼＋四層甲板（at=0,0,0）；⛔ 甲板不關聯進船殼
- [x] 四層草稿 stampvox（52,858／108,018／132,734／110,983，placed ＝ 清單）；組裝件 draft=1 匯出 1,226,037 ＝ 821,444 ＋ 404,593、link_overlap 0、甲板格逐格對上
- [x] Tim「可以套用草稿了」⇒ 四件 apply（changed ＝ 清單、apply_mismatch 0）；notes.md「階段十」；過程圖 `overlays/stage10_*`
- [ ] journal（stage10–13 一起）
- 甲板板 250、桅孔現在就開：Tim 預覽後沒有要改（2026-10-11 套用）
- Tim 2026-10-11：組裝件「測試 ok」；觀測頁開關關聯 ⇒ 開 TASK-0499（toggle，先不用做）

## 階段十一 房間子作品（2026-10-11 套用）
- [x] 新圖紙 09（`design/draft_rooms.py`、`sheet09_rooms_v1.png`、`verify_rooms.json`；設計在 plan.json `rooms`）：orlop／berth／gun 的艙壁與艙房，門不放、留門洞；牆 1 格（板 177、框 136）
- 六件：三件全寬艙壁（whole，at=0,0,0）＋ 三件舷側艙房（side，只做 y > 160 那一舷、自己的座標；另一舷 mirror=y、at.y ＝ 321 − y0 − h）；都關聯進各自的甲板子作品
- 讀數：43,798 格（含鏡像那一舷）、跟船殼／甲板重疊 0、鏡像差 0、封閉空腔 0
- [x] Tim「GO 建房間子作品」「房間可以做為甲板的子作品」⇒ 六件 parent_work ＝ 各自的甲板子作品（root 仍是本作品，免費）；草稿 stampvox（placed ＝ 清單）；關聯進甲板：艙壁 at=0,0,0、艙房（照原樣）＋ 艙房-鏡像（mirror=y）
- [x] 組裝件 draft=1 匯出 1,269,835 ＝ 1,226,037 ＋ 43,798、link_overlap 0；房間格（含鏡像那一舷，自己用 320 − y 手算對拍）逐格對上、舊格一格沒變
- [x] 六件 apply（changed ＝ 清單、apply_mismatch 0；berth-bulkheads 是避開桅孔之後的 7,248）
- ⚠ berth seam 587 在前桅上 ⇒ 矮檻蓋高低差、sick bay 艙壁移到 596；gun deck seam 570（3 格台階）留給 riding bitts
- Tim 2026-10-11：「房間可以做為所在甲板的子模組嗎（隱藏甲板同時會隱藏對應房間）」⇒ 已經是：拿掉 甲板-gun 匯出 1,131,019 ＝ 1,269,835 − 132,734 − 3,888 − 1,097×2（links_used 沒有 甲板-gun/…）

## 階段十二 舷牆與舷弧起翹（2026-10-11 套用；船殼本身）
- [x] 新圖紙 10（`design/draft_bulwark.py`、`sheet10_bulwark_v1.png`、`verify_bulwark.json`；設計在 plan.json `bulwark`）：舷頂 ＝ 白帶上緣（三次擬合，殘差 ≤ 0.66）＋ 25、只往上補（x 493 起，船頭最多 +9）；補的格照肋骨頂那一列（36／141／177，牆中間的空格當 141）；全長 cap rail 104（內外各多 1 格）
- 讀數：rise 6,406、cap 6,995、跟現有重疊 0、鏡像差 0、1 元件、空腔 0（補 16 格）；新格 z 122–133（甲板最高 110，不相干）
- [x] Tim「GO 舷牆落草稿」⇒ 標記 `舷牆:begin`（＝ 船殼內部:end，第 473 個事件）；船殼草稿 stampvox rise 6,406 ＋ cap 6,995；船殼＋草稿 834,845、新格逐格對上；組裝件 1,283,236、link_overlap 0
- [x] apply（跟 bowsprit 開口拆成兩筆：丟掉混在一起的草稿、重落同樣兩份清單）⇒ 13,401、標記 `舷牆:end`（第 474 個事件）

## 階段十三 桅杆（2026-10-11 套用）
- [x] 新圖紙 11（`design/draft_masts.py`、`sheet11_masts_v1.png`、`verify_masts.json`；設計在 plan.json `masts`，軸照 `deckworks.masts`）：三根桅（下桅、masthead、cap、top、trestletrees／crosstrees、topmast、topgallant／royal、truck）＋ bowsprit／jibboom／flying jibboom；讀組裝件 draft=1 的現況
- 讀數：main 27,484／fore 21,732／mizzen 11,692／bowsprit 11,394（72,302）；鏡像差 0；碰到甲板／房間 0；底艙 step 的腳碰到船殼 58／26 格（讓開）；top z 285／262／240、truck 648／600／511；bowsprit 斜度 15.4°、flying jibboom 尖端 x 958
- ⚠ 房間的 berth seam 587 矮檻原本橫過前桅孔（房間比桅杆早產生）⇒ draft_rooms 改成避開桅孔，berth-bulkheads 7,266 → 7,248、草稿丟掉重落（其他五件逐位元組不變）
- ⚠ 後桅 1801 年 92 ft 照放 top 會比前桅高（跟在 deadwood 上）⇒ 設計決定 82 ft
- [x] 四件子作品（parent ＝ 船殼）→ 草稿 → 關聯進組裝件 → apply；船殼刻 33 格（顏色守門）、標記 `艏斜桅開口:begin／end`（834,812）
- [x] v1.1 主桅 top 浮空 ⇒ trestletrees 緊貼 masthead（刻 144 補 144）；組裝件 1 元件、空腔 0、1,355,487
- [ ] 之後：yards、gaffs、spanker boom、dolphin striker、channels、索具與帆（Tim：先不做）
- 之後：吊床網架與欄杆（11 號 quarterdeck 130–135／forecastle 127–130 那幾條）、spar deck 砲門 ⇒ 配件

## 階段十四 船尾窗與船尾裝飾（2026-10-11 套用）
- [x] Tim 給兩張實船照片：「可以加上裝飾線條（參考現實照片 由你設計）」「其實可以重新設計（例如嘗試開船尾窗）」；quarter gallery「好像不用改，那是模型自己改的」⇒ 這次不做（⚠ 1927 年 11 號圖其實有標 QUARTER GALLERY，比模型扁很多 —— 已跟 Tim 講）
- [x] 新圖紙 12（`design/draft_stern.py`、`sheet12_stern_v1.png`、`verify_stern.json`；設計在 plan.json `stern`）
- [x] 船殼開窗 7 扇（gun deck 主窗列 z 95–101，counter timbers 之間）：carvevox 帶顏色守門 1,165 格；標記 `船尾窗:begin／end` ⇒ 833,647
- [x] 子作品 `-stern-deco`「憲法號 船尾裝飾」（parent ＝ 船殼）＋ 組裝件關聯 `船尾裝飾`：1,676 格（窗格、pilasters、拱線、星、鷹、船名、白線）
- [x] 組裝件 1,355,998、link_overlap 0、1 元件、空腔 0；產生程式讀 `船尾窗:begin` 重產兩份清單逐位元組相同
- 草稿期間改掉的：船名在引擎裡反了（從船尾看觀者左手邊 ＝ −y）、白窗格像柵欄 ⇒ 黑、星星像小烏龜、拱線圓角糊成一團、拱線細化左右差 12 格 ⇒ 只算半邊再鏡射
- [x] Tim 在 Unity 看船名是不是正著讀 —— Tim 2026-10-11：「船名 ok」
- [ ] 之後：quarter galleries（子作品，掛在 fashion pieces 外面）、上層船尾窗（1927 有三扇；這次照照片放鷹與星）、舵、船尾燈籠、davits 與小艇

## 階段十五 船頭（2026-10-11 套用）
- [x] 資料 workflow（歷史、讀圖、現況、外部盤點＋兩位推翻者）；Tim「不用太過追求史實……追求美觀就好」
- [x] 新圖紙 13（`design/draft_head.py`、`sheet13_head_v1.png`、`verify_head.json`；設計在 plan.json `head`）
- [x] 子作品 `-head-knee`（中線整件）＋ `-head-side`（一舷、固定框）＋ 組裝件三條關聯（船頭-knee、船頭裝飾、船頭裝飾-鏡像 mirror=y）
- [x] Tim 預覽「測試ok 可以套用了」⇒ apply（6,131＋2,925，mismatch 0）；組裝件 1,367,979、1 元件、空腔 0；重產逐位元組相同
- [x] ~~審查 workflow（美觀＋幾何）~~ Tim：「審美妳決定後，我再看一次就好，不用額外派 agent 審核」⇒ 停掉（他已經預覽、套用了）
- [ ] 之後：head deck／gratings、bobstay 孔與 gammoning（繩索固定點）、真的 hawse 孔（刻船殼）、錨、fore-tack bumpkin

## 階段十六 帆桁（2026-10-11 套用）
- [x] 資料 workflow（尺寸＋桅的量測＋推翻者）；新圖紙 14（`design/draft_yards.py`、`sheet14_yards_v1.png`、`verify_yards.json`；設計在 plan.json `yards`）
- [x] 12 根橫桁＋spanker gaff／boom（後桅）＋spritsail yard（艏斜桅）貼進四件桅杆子作品；固定點 320 個（`design/rig_points_yards.json`）
- [x] Tim「測試ok 可以套用了」⇒ 四件各打 `帆桁:begin` → apply（mismatch 0）→ `帆桁:end`；組裝件 1,386,789、1 元件、空腔 0；重產逐位元組相同
- [ ] 固定點清單照 TASK-0502／0503 定下來的格式轉（`work sub=anchor`；`design/tools/register_anchors.py <rig_points 檔>`）—— 已登記：channels S 舷 deadeye 31（靜索試掛）、繫繩點 125（階段十九）；**帆桁的 320 個還沒**（掛帆時再登記，名字照 rig_points_yards.json）
- [ ] 想要「停泊」的樣子時：topsail／topgallant yard 改用 `z_lowered`（plan.json yards）

## 階段十七 舵（2026-10-11 套用）
- [x] 新圖紙 15（`design/draft_rudder.py`、`sheet15_rudder_v1.png`）；子作品 `-rudder`＋關聯「舵」；3,950 格；Tim「舵我確認ok」⇒ apply；組裝件 1,390,739
- [ ] 之後：helm port 與舵頭在船裡那段、tiller、rudder pendant chains（繩索）

## 階段十八 channels（2026-10-11 套用）
- [x] 新圖紙 16（`design/draft_channels.py`、`sheet16_channels_v1.png`、`rig_points_channels.json`）；子作品 `-channels`（一舷）＋關聯 channels／channels-鏡像；一舷 6,506 格；Tim「測試ok 可以套用了」⇒ apply；組裝件 1,403,751
- [x] chain plates 長短不一（10 根在白帶上緣收住）—— Tim 2026-10-11「由你決定」⇒ 不改（只有穿過白帶那段看得到；統一變短會全拿掉、統一變長會蓋砲門；notes.md 階段十九）
- [x] shrouds／backstays 試掛（繩，2026-10-11；notes.md「靜索試掛」）
- [x] 上 deadeyes、lanyards（階段二十五，繩當圓盤）
- [ ] 之後：backstay stools、channel 下的支撐肘

## 靜索試掛（2026-10-11；繩，不是 voxel）
- [x] Tim：「可以先試著掛一些跟帆沒有連接的繩子測試」⇒ 固定點 134、繩 133（shrouds、backstays、futtock、topmast／topgallant shrouds、stays、bobstays），ropes_broken 0；工具 `design/tools/rig_standing_{plan,apply}.py`、清單 `design/rig_standing.json`
- [x] ratlines 340 道（階段二十二；`tools/ratlines.py`）
- [x] lanyards 與上 deadeyes（階段二十五）
- [ ] 之後：catharpins；動索（braces、sheets、halliards…）等帆 —— 下端綁 `rig_points_belaying.json` 的 pins

## 掛帆試試（2026-10-11；帆，不是 voxel）
- [x] Tim「掛帆試試吧」「可以調整風力試試」⇒ 帆 15 面＋帆腳索 32 條；組裝件 meters_per_voxel 補 0.1；預設風 4.5,−1.5,0、4 秒（notes.md「掛帆試試」）
- [ ] 帆桁轉角度（brace）：現在是正橫擺，正側面只看得到帆的側緣 —— 要「航行中」的樣子就轉 yard（帆桁在桅杆子作品裡是 voxel ⇒ 要重產帆桁）或至少讓帆角跟著 braces 走
- [ ] course 的 sheet／tack 現在穿過舷牆直接綁到 pin（實船從船側的 sheave 進來）；三角帆 sheet 綁在 x 609 的 pin，離 clew 很遠 —— 之後加 sheet 的導點（船側 sheave、cathead、bumpkin）
- [ ] 收帆（furled）／縮帆（reef）等引擎支援；spritsail、studding sails 沒掛

## 階段十九 甲板繫繩點（2026-10-11 套用）
- [x] 資料（research agent：1973 BSN 27076-B、1927 Magoun Plan X、1930 #28433／#28432、2022 照片）；新圖紙 17（`design/draft_belaying.py`、`sheet17_belaying_v1.png`、`verify_belaying.json`；設計在 plan.json `belaying`）
- [x] 子作品 `-fiferails`（parent ＝ spar deck，關聯進 `甲板-spar` 名 `fife-rails`）2,393 格；`-belaying-side`（一舷，關聯 `繫繩欄`／`繫繩欄-鏡像`）832 格
- [x] Tim「測試ok 可以套用了」⇒ apply（mismatch 0）；組裝件 1,407,808、1 元件、空腔 0；重產逐位元組相同；固定點 194（登記 125）
- [ ] 之後：kevels、timberheads、桅腳的 cleats、bowsprit bitts 的頭；舷牆內側換實船現在的深綠（要的話另開一階段）
- [ ] spar deck 砲門開的時候：pin rails 是照 gun deck 砲門的空檔放的，spar deck 的砲門若不在正上方要重排

## 階段二十 gun deck 長砲（2026-10-11 套用）
- [x] 新圖紙 18（`design/draft_guns.py`、`sheet18_guns_v1.png`、`verify_guns.json`、`guns_placement.json`；設計在 plan.json `guns`）：子作品 `-gun-24` 一門 1,125 格，關聯進 `甲板-gun` 28 條（S／P 各 14）；Tim「測試ok 可以套用了」⇒ 1,439,308、重產逐位元組相同
- [x] breeching rope、gun tackles、train tackle ＋ 船牆／甲板的環首螺栓、shot garlands ⇒ 階段二十一（2026-10-11 套用；新圖紙 19）
- [x] 第 2 門（艦長室）船頭側的環 ⇒ 釘在艙房隔牆上（階段二十二）
- [x] rammer／sponge 掛在橫樑底下（階段二十二；22 根，艦長室裡與第 3、4 門的 sponge 放不下）
- [ ] handspikes
- [ ] 第 15 個砲門（船頭）沒放砲 —— 要放就做一門短一點的 chase gun 或斜放（turn 只有 90°）
- [ ] spar deck：carronades（32 磅、slide carriage）與 bow chasers —— spar deck 的砲門要先開（現在 pin rails 是照 gun deck 砲門的空檔放的，開 spar deck 砲門時一起看）
- [ ] 砲門蓋（等可以匯入模型）

## 帆（kotoko 2026-10-11 噗浪上的兩點，2026-10-12 試過；讀數見 notes.md「掛帆試試 → kotoko 兩點」）
- [x] 兩面 course 下角被吹高、tack 垂 21–26 格 ⇒ **tack 收到 0.8**（sails_test.py 已改、已套用）：main 下角 z 161.6 → 153.4（設計 150）、tack 垂 0；fore 下角不動（153.5，sheet 撐著）、tack 垂 21 → 10–12
- [x] 鼓得偏深 ⇒ fullness **不是**主要旋鈕：1.05 → 1.02 只少 5 格、1.0（布繃平）main 仍 −84 ⇒ 鼓度主要來自風（tack 0.8／fullness 1.0 時，風減半 main −55／fore −45 ≈ 寬度兩成；無風 −17／+27 自然下垂）。fullness 維持 1.05
- [ ] 要不要讓 course 鼓淺一點：① 預設風降到約 2.4 m/s（全部帆一起變淺）② 帆腳那條邊（clew_s→clew_p）加束縛（foot rope；引擎目前帆腳是自由邊，推測是中段被吹起的主因 —— ⚠ 推論，沒驗）—— 審美題，等 Tim 預覽後選
- [x] 讀數回噗浪給 kotoko（2026-10-12，plurk 359018012547482 的回應；酒館 seq 22919）
- [ ] ⚠ brace（階段二十六）之後 course 的 tack 又不繃了（kotoko 的判準：長度 ＝ 直線才算繃住）：main S 57.88 ＝ 57.88、main P 115.89 對 112.35 垂 13.07、fore S 41.14 對 40.62 垂 11.59、fore P 54.67 對 48.64 垂 12.15 —— 帆下角轉了而 tack 還綁在原本的 pin ⇒ 兩舷分開調（slack 各自算、或換 pin）

## 階段二十三 艙口梯（2026-10-11 套用）
- [x] spar → gun 4 座（waist 一對、after、fore）、gun → berth 3 座（companion、after、fore）；扶手繩 14
- [ ] berth → orlop：三個候選都放不下（見 notes.md 階段二十三）⇒ 要的話另開一個 orlop 的梯口
- [ ] 船側 side steps 與 entry port（從小艇上船）⇒ 階段三十（草稿，見下）
- [ ] 艙口格柵（gratings；spar deck 長艙口、main／fore hatch）
- [ ] spar deck 艦長室上方的 companion（spar deck 那一格目前沒有開口）

## 階段二十四 錨（2026-10-12 套用）
- [x] 新圖紙 21（`design/draft_anchors.py`、`sheet21_anchors_v1.png`、`verify_anchors.json`；設計在 plan.json `anchors`）：old pattern bower anchor 一隻 1,140 格（shank 4.8 m、stock 4.3 m 木 172 套鐵箍、arms＋palms、ring），鐵 146
- [x] 子作品 `-anchor`（parent ＝ 船殼，47×33×58）＋ 組裝件關聯 錨-S（630,189,73）／錨-P（630,99,73，mirror=y）；草稿已蓋（placed 1,140）
- [x] 讀數：catted 在 cathead 端面正下方（掛點 653,205,130，第一個試的就過）、兩舷跟現況重疊 0、x／y 不對稱 0、1 元件、貼著 cathead 6 格、離船殼最近 1 格、最低 z 75（水線 62.86 之上）；組裝件預期 1,443,188 ＋ 2 × 1,140 ＝ 1,445,468
- [x] 草稿期間改的：stock 先沿船寬 ⇒ 靠船內那頭插進船殼 57 格 ⇒ 改沿船長；stock 46 格船尾端碰到 x 630 的黑木 2 格 ⇒ 42；ring 只靠斜角相接（7 塊）⇒ 粗 0.8；黑 36 貼黑船殼看不見 ⇒ 鑄鐵灰 146（hawse 圈同一個理由）
- [x] Tim「測試ok 可以套用了」⇒ apply（changed 1,140、mismatch 0）；組裝件 1,445,468、1 元件、空腔 0、link_overlap 0
- [x] ~~cat fall 兩舷~~ 掛過又拿掉（Tim 2026-10-12：錨不用繩子，看起來有點怪）⇒ 錨的繩一律不做
- [ ] 之後：fish 起來綁在船側（換成另一種收法，要 Tim 選）、fish tackle、錨纜與 hawse 孔、sheet／stream／kedge anchors

## 階段二十六 帆桁轉角度 brace（2026-10-12 套用）
- [x] plan.json `brace`（下層 20°、往上每層 +2°；右舷那一頭往前，對著從右舷後方吹來的預設風）；`design/draft_brace.py`（刻舊的＋蓋轉過的、固定點沿轉過的軸重算、轉之前的固定點另存 rig_points_yards_square.json）
- [x] ~~⚠ 停手~~（summit 10:0x 出廠 791da4e 之後接上）：summit 的 TASK-0505（作品書卡加 tags）09:57 把 27 件子作品的書卡加了 `tags`，publish/senate.exe（1119802-dirty.20261012T014222Z）不認得 ⇒ 組裝件匯出 blocked。已在酒館跟她說（seq 22900），等她出廠再接；⛔ 那 27 個 work.json 是她的遷移，不收、不改
- [x] 接手第一步：正向對照 —— 角度全設 0 跑 draft_brace，產出的帆桁格子與固定點要跟現在逐格、逐點相同；對上了才跑真的角度
- [x] sails_test.py 的帆下角改成左舷讀左舷自己的 earing（現在 P 是 S 鏡過去 ⇒ 轉了就不對）；改完先在沒轉的狀態重跑，帆的讀數要跟現在一樣
- [x] 草稿：三件桅杆子作品各 carvevox（舊方帆桁，顏色守門）＋ stampvox（轉過的）→ 登記轉過的固定點 → sails_test --apply（讀數見 notes 階段二十六）
- [x] Tim「測試ok 可以套用了」⇒ 三件 apply（changed 9,089／14,684／4,769、mismatch 0）；組裝件 1,445,296、1 元件、空腔 0、link_overlap 0、sails／ropes broken 0
- ⚠ 要退回的話：三件 discard 草稿 ＋ `register_anchors.py . rig_points_yards_square.json` ＋ 把 rig_points_yards.json 換回 square 那份 ＋ sails_test --apply
- [ ] 之後：braces（yardarm → 船尾的動索）、lifts

## 下一階段（現實順序：內板之後是橫樑與甲板）
- **範圍（Tim 2026-10-11）：砲門與其他可動件之後另外做；甲板階段只做甲板主體＋房間，門也不放；甲板骨架跟房間開子作品**
- [ ] ⚠ 先做 TASK-0497（關聯／組裝支援鏡像）—— 兩舷對稱的肘、艙房只做一份
- [ ] 甲板子作品（每層一件，子作品尺寸 ＝ 船殼、at=0,0,0、turn=0）：橫樑（gun deck「每個砲門底下一根、之間一根」）、carlings／ledges、hanging／lodging／dagger knees、standards、waterways、deck hooks、柱子、甲板板；高度照 plan.json `interior.decks`（橫樑底 ＝ clamp 頂）
  - [ ] orlop 平台照 z 38–41 的艙內空氣裁；斜肋穿過的 x 範圍（notes.md 階段九）橫樑開槽或避開
  - [ ] seam 504（前艙口後緣）不是艙壁 ⇒ 放一道橫向的東西（艙口圍板＋隔板或梯子）蓋住 1 格的高低差
  - [ ] deck hooks（船頭 orlop／berth／gun）、berth deck 的 transom knee（船尾 Z ≈ 61）
  - [ ] 甲板做完再跑一次 `fill_cavities.py <名稱>`
- [ ] 房間子作品（關聯進甲板子作品；不放門）：1816 Waldo orlop（filling rooms、bread room／magazine、cockpit、cable tiers…）、berth deck（wardroom、steerage、sick bay）、gun deck（captain's cabin、galley）
- [ ] 舷牆、舷弧（照 sheer 起翹，見階段五那條拍板）：舷牆高度（sheer plan 船尾 rail Z 130–134、waist 約 119.6、見 source_ends_raw.json readings[1] rail_structure）；舷頂蓋板疊在階段九的封口上；spar deck 兩組砲門（船尾 X ≈ 100–371、船頭 X ≈ 515 起）⛔ 現在不開，跟可動件之後一起做
- [ ] ⚠ 重跑 `draft_interior.py` 讀標記 `船殼內部:begin` 並對 world_voxels（已設好）
- [ ] ⚠ 高度一律用 plan.json `ends.provenance.frame_of_heights` 的一致換算；⛔ 不要用舊式「− 0.01538·(439.2 − X)」
- [ ] ⚠ 重跑 `draft_ports.py` 讀 `gunports.world_upto`（階段八第一刀之前），已設好
- [ ] ⚠ 重跑 `draft_planking.py` 要讀 `planking.world_upto`（階段七第一刀之前）—— 讀現況會長出第二層外板
- [ ] `draft_frames_ends.py`（階段六）的 Ctx 也讀現況（events 重播減柱頭）⇒ 雕完重跑會讀到自己雕上去的木料、清單會變；補同一道閘（`framing_ends.world_upto` ＝ 階段六第一刀之前），重產比對事件記的 51 個 sha256
- [ ] 砲門蓋（port lids）與其他活動部件：⛔ 不用 voxel 做 —— 等 `/scp-sculpture` 擴充成可以匯入模型之後用模型做（Tim 2026-10-11）；舷牆上的 hammock netting 同上再看
- [ ] 04／15 號的 rider keelson（15"x18"）與 Humphreys 9"x24" deadwood 要不要做
- [ ] 桅檣（桅位 X：後桅 206、主桅 351、前桅 587 是站位換算，做的時候再對 02 號）
- [ ] 船首 knee of the head、head rails、trailboards（裝飾的部分做子作品）；船尾 quarter galleries（子作品，掛在 fashion pieces 外面）；艉柱頭伸出 wing transom 約 7 格 —— 做舵與 counter 外板時決定要不要削
- [x] breast hooks（hold 裡船頭 2 道、船尾 crutches 2 道 —— 階段九）；deck hooks、transom knees ⇒ 甲板子作品
- [ ] stern knee、hawse holes
- [ ] 裝飾物（大砲、舵、其他重複物件）：先開子作品（parent_work＝本作品）雕好，再 `work sub=assemble` 匯入

## 範圍（Tim 2026-10-11）
- 玻璃等透明部分、帆、纜索：先不做（之後 /scp-sculpture 擴充成可嵌模型再處理）
- **帆與索具的做法（Tim 2026-10-11 晚）**：帆用布料模擬（綁在幾個 voxel 上固定、可以跟線綁定、風＋重力）；繩索另外做（設定綁定點、受重力與一定的物理彎曲、可設顏色與粗細），**繩索可以綁帆，也可以綁 voxel 固定點**；**yards 做進桅杆子作品裡**（gaffs／booms 同理）；帆可以設定顏色，甚至指定貼圖
  - ⇒ 之後每做一件會被繩索或帆綁到的 voxel 部件（yardarm 兩端、slings、channels／deadeyes、cleats、bitts、belaying pins、tops 邊…），設計裡要把**固定點記成有名字的座標**（plan.json 裡一份清單），不要只留在格子裡
- 砲門蓋與其他活動部件：不用 voxel 做，等可以匯入模型再做

## 待確認
- [x] keel drag：不做（2026-10-11 決定，理由見 notes.md）；~~甲板／舷弧／砲門的高度要逐站相對龍骨量~~ ⚠ 階段六更正：作品是「從水線量」的框，sheer plan（相對龍骨）的讀數要減 drag 才放得進來（見 notes.md「階段六」）
- [ ] sided（艏柱／艉柱／deadwood／apron 5 格）仍是設計決定
- [ ] 底肋頭長 3.6 m 仍是設計決定（02／15 號都沒畫）

## 階段二十九 spar deck 砲門 —— 已套用（2026-10-12）
現況：全部套用（2026-10-12 下午；讀數見 notes.md 階段二十九）。以下是套用前的紀錄：
- 草稿（已套用）：船殼（basecamp-frigate-constitution-01m，刻 10,676 格 spar deck 砲門）、-belaying-side（pin rails v2：拿掉 337、放 330）。
- 已經生效（不是草稿）：carronade 子作品砲身往前 4 格（已 apply，一筆事件，undo 一次就回去）；spar deck 子作品 models.json 24 門 carronade-S01..12／P01..12。
- notes.md 階段二十九已寫、overlays/stage29_spar_{side,deck,fwd}.png 已存。
Tim 的回饋：「這幾個被纜線擋住了」—— channel 上的 deadeye／lanyard／shroud 擋在後桅段（砲門 2、3）、主桅段（6–8）、前桅段（9–11）前面。
接下來（照順序）：
- [x] 跑 draft_channels_v2.py（2026-10-12 下午）：第一輪 SPACING 5／MARGIN 2 ⇒ 後桅最後兩個掉出子作品的框（x 145）、主桅最後一個散到 248 ⇒ 改 SPACING 4／MARGIN 1（deadeye 3 格寬、中間空 1 格）。
      結果：前桅 591,577,573,569,565,548,544,540,536,515,511；主桅 349,345,341,337,333,318,314,310,306,302,283,279；後桅 207,203,199,185,181,177,173,169；still_blocked 0（verify_channels_v2.json）。
- [x] channels 子作品草稿：carvevox 1,280（顏色守門）＋ stampvox 1,414 ⇒ 讀回 6,640 ＝ 設計。側視圖（不畫繩）overlays/stage29_channels_v2_side.png。
- [x] rig_standing.json 的 31 個 channels 固定點（`<桅>.deadeye-<i>`，只有 S 舷，P 舷靠鏡像）改成 v2 座標 —— ⚠ 只改了檔，**引擎裡還沒重新登記**。
      📌 量過：引擎登記的是這 31 個，不是 rig_points_channels.json 的 `<桅>-channel.deadeye-S／P<i>`（那份從沒登記過；舊 todo 寫錯了）。
- [x] 子繩 TASK-0511／繩分組 TASK-0512 做完（還沒提交）、出廠 12ebd95-dirty；套到船上（2026-10-12 12:3x）：
      31 個 deadeye 固定點重新登記；rig_deadeyes 重產 310 條；ratlines 改子繩 `rope:<shroud>/比例`（tools/ratlines.py），
      起點改從上 deadeye 頂往上 7 格 ⇒ 340 → 328 條（拿掉 12 條舊的）；897 條全部分進 17 組（design/tools/rope_groups.tsv 的 regex）。
      讀數：broken 0、子繩 328、組 23（含上層）、未分組 0；hide_rope_groups=standing/shrouds ⇒ 藏 218（46＋掛在上面的 lower ratlines 172）。
      圖：overlays/stage29_channels_v2_ropes.png、stage29_main_channel_ropes.png。
      ⚠ 上 deadeye／lanyards／shroud 下端仍是座標（rig_deadeyes 從固定點算的，要重跑腳本才跟）；子繩語法表達不了「往舷外偏一點」。
- [x] Tim「測試ok 套用草稿然後單層提交吧」⇒ 三份草稿套用、pin rails 固定點 68 個重新登記、unanchor pinrail-12.pin-5；繩 broken 0（SCP_Core d48e4ab、Senate 2f5cf4c）。

## 階段三十 entry port 與 side steps（2026-10-12 套用；讀數見 notes.md 階段三十）
- [x] 讀圖（11 號：11 道橫條、開口兩側的柱）；新圖紙 23（`design/draft_entry.py`、`sheet23_entry_v1.png`、`verify_entry.json`；設計在 plan.json `entry`）
- [x] 子作品 `-entry-side`（一舷）＋組裝件關聯 舷梯／舷梯-鏡像；標記 `舷梯:begin`（船殼、-belaying-side）
- [x] 草稿三份：船殼 carvevox 1,480（兩舷開口）、-entry-side stampvox 151、-belaying-side carvevox 54（pinrail-6）；固定點 4、man ropes 4（組 entry/manropes）
- [x] 組裝件 draft=1 1,433,588（預期對上）、1 元件、空腔 0、link_overlap 0、ropes_broken 0
- [x] Tim「測試ok 套用草稿」⇒ 三件 apply（changed 1,480／151／54、mismatch 0）→ unanchor pinrail-6.pin-1..5 → 船殼、-belaying-side 打 `舷梯:end` → 重跑 draft_entry.py 三份 sha256 相同；組裝件 1,433,588
- [x] v1.1：man rope 下端綁在空中（Tim 2026-10-12 預覽指出）⇒ 最下一道加寬加深、繩端埋進它外側兩角（-entry-side 草稿增量 22 格）
- [x] Tim「測試ok」⇒ -entry-side apply（changed 22、mismatch 0）；組裝件 1,433,632
- [ ] 之後：entry port 的扶手欄杆、gangway 板、fenders／chesstree、quarterdeck 那段欄杆比 waist 高（11 號有畫，作品舷頂是單一高度）

## 階段三十一 主甲板砲改外部模型（2026-10-12；讀數見 notes.md 階段三十一）
- [x] 28 門 24 磅砲關聯 → 外部模型、140 條砲索重綁 model: 路徑（diff 0、broken 0）
- [x] P 舷第 15 個砲門補 chase18-P（Tim 預覽「好像缺一門炮」）
- [ ] Tim 預覽 OK ⇒ 單層提交（Sculpture）

## 彈藥庫（規劃，等 Tim 拍板；遊戲要模擬彈藥庫爆炸）
史實配置（1812 前後的 44 砲巡防艦）：火藥庫在 orlop 平台**下面**的船艙（hold），正上方是 filling room（裝藥包的房間，作品已有牆：after filling room x 167–192、forward filling room x 608–630）；旁邊有 light room（隔著玻璃點燈，火不進彈藥庫）。主彈藥庫在前、大；後彈藥庫在後、小。
量（組裝件現況，船艙中線、到 orlop 橫樑底 z 38）：
- 船尾 x 180–240：底 z 30→20、高 8–18 格、寬 9–43 格（V 形很尖）—— 後彈藥庫只放得下小的
- 船頭 x 560–615：底 z 17–24、高 14–21 格、寬 13–87 格；x 590 是前桅桅腳 —— 主彈藥庫放這段（避開桅腳）
提案：
- [ ] 先讀 02 號側面圖（1849 inboard，Pook）找 MAGAZINE／light room 的實際 x 範圍，換到作品座標（派讀圖 agent，限時、只要兩段 x 範圍與高度）
- [ ] 子作品各一件（遊戲可以分開引爆）：`-magazine-fore`、`-magazine-aft`；關聯進 -deck-orlop（跟房間同一層）
      內容：艙壁（銅皮內襯色）、地板抬高、門洞朝 filling room 那側；火藥桶（voxel 或外部模型，待定）
- [ ] 固定點給遊戲用：`blast`（爆心）、`door`、外框兩角；notes 記火藥量估值（桶數 × 每桶磅數）
- [ ] light room（可選）、shot locker（主桅附近，彈丸不會爆，⛔ 不放進彈藥庫子作品）
Tim 2026-10-12 拍板（醒來不要重問）：
- 彈藥庫照史實；史實兩個版本都有就兩個都做。
- 火藥桶要做：彈藥庫的子模組，**跟砲一樣用外部模型引用**（不是 voxel 關聯）。
- 模型要不要多帶資訊給遊戲、export 要不要搬到 C#（現在是 ArtGallery/VoxelKit/voxel_export.py）⇒ 到酒館跟遊戲那邊討論（2026-10-12 seq 24095 @ame）。

## 階段三十二 彈藥庫（2026-10-12；讀數見 notes.md 階段三十二）
- [x] 讀 02 號圖找 MAGAZINE（後 x 200–271、前 x 521–574）、1812 日誌對照（前後兩間）
- [x] 子作品 -magazine-aft／-magazine-fore（銅皮、門洞、木架）＋ -powder-barrel（0.02 m）當模型 22＋116 桶；固定點 blast／door
- [x] 組裝件 1,413,088、1 元件、空腔 0、overlap 0、模型 193、broken 0
- [x] Tim 預覽 OK ⇒ 單層提交（Sculpture；階段三十一一起）—— 366a440
- [x] meta（kind=magazine、powder_lb）等 TASK-0517；砲的 breech 固定點也在那張單 —— 818140f

## 階段三十三 帆桁改外部模型（2026-10-12 晚；讀數見 notes.md 階段三十三）
- [x] 15 件子作品 -yard-*（沒轉的帆桁、固定點＋pivot）→ 桅杆子作品裡放模型（rotate z、meta kind=yard）
- [x] 帆 12 面、sheet 18 條改 model: 路徑；sails_test.py 改產 model: 路徑
- [x] 從桅刻掉舊帆桁（刻完 ＝ 帆桁:begin 逐格相同）、拿掉 320 個舊固定點
- [x] 組裝件 1,394,450、1 元件、空腔 0、模型 208、broken 0；轉到另一舷試過、轉回來逐位元組相同
- [x] Tim 預覽 OK ⇒ 單層提交（Sculpture）—— 57e2795
- [x] 跟 ame 說：帆桁的 meta 與 pivot（遊戲跟著風轉）
- [ ] 之後可以考慮：gaff／boom 改成「直桿＋rotate y」（現在是斜的格子階梯）；course 的 sheet／tack 跟著帆桁轉

## 旗（2026-10-13，Tim：「是否可以給憲法號也加上旗幟」）
- [x] 旗桿（後桅、主桅桅冠）＋船尾旗（十五星十五條紋）＋長旗；帆 17、組裝件 1,394,513
- [x] 旗 Tim 預覽 OK ⇒ 單層提交；constitution.vxk 已重匯 fcfe34c7（給 ame）
