# 持火號（Pyrphoros）—— 拜占庭 dromon（10 世紀、100 槳雙層、希臘火）建造筆記（0.1 m／格）

委託：Tim 2026-10-18（Claude Code 對話，/scp-shipbuilding；TASK-0693）：
「找一艘經典的拜占庭裝備希臘火的獎帆船來建造吧 參考歷史資料與圖紙 最後由妳繪製圖紙並建造(資訊不足的部分由妳設計)」
「獎的部分可以先不做 等獎動力系統確認規格再加」「武器部分套用大炮規格 不過之後會需要新增彈種 希臘火」「除了希臘火也可以裝上其他武器(之後擴充大炮系統支援)」。

## 範圍
- 做了：船殼、主甲板、艙底走道、艏樓（pseudopation）、兩座木塔（xylokastra）＋木橋、雙桅三角帆（lateen）、兩支舷側舵、siphon＋3 弩砲＋1 投石機、希臘火藥庫、錨、艉旗、給遊戲的 meta。
- 槳（2026-10-18 下午，Tim：「可以加槳了 參考皇家號的配置」）：雙層 98 支 —— 下層每舷 25 支從外板槳口伸出去（槳手站艙底走道）、上層每舷 24 支從舷牆槳口伸出去（槳手站主甲板）、每支 1 人；上層第 18 位讓給投石機。做法寫進造船規格 §9.10.2。
- 武器（2026-10-18 更新，Blockside 分支 `erina/greekfire`，未合併）：
  - siphon：`kind=gun gun=siphon weapon=siphon ammo=greekfire safe=1` —— 遊戲新砲種「希臘火 siphon」（射程約 30 m、直接傷害＋噴火演出；Tim：點燃要搭配滅火，之後再設計）。
  - 弩砲 ×3（2026-10-18 晚，Tim：「弩炮目前我想直接做成換皮大炮(只是彈藥不同)」「弩炮可以給一定的轉動空間(參考維吉尼亞號的前後炮)」）：`kind=gun gun=ballista weapon=toxoballistra ammo=bolt mount=pivot`，
    船頭 `ports=0,35,-35`（±40 擦到艏樓欄杆 9 格、±45 9／20 格）、木塔 `ports=0,45,-45`；每個停靠角度零碰撞。遊戲：砲種表 ballista、彈種弩箭（照實心彈飛、畫成箭）。
  - 投石機：機制還在想 ⇒ 沒有 kind，只留 `weapon=manganikon ammo=stone mount=pivot ports=0,180` 當標記。

## 史料（references/dromon_research.md；研究 agent 2026-10-18，Google Books 片段＋開放論文）
- Pryor & Jeffreys《The Age of the ΔΡΟΜΩΝ》（2006）的復原：全長 31.25 m、寬 3.80 m（直舷）／4.46 m（下層槳口以上外張）、甲板離水線 ≥ 0.95–1.0 m、下層槳口下緣離水線 0.36 m、槳距 ~1.0 m、每舷上下各 25 槳。
- 前桅較大（11.85 m、前傾 13°、帆桁 20.17 m）、中桅 8.3 m（帆桁 15.43 m）；lateen 沒有前後支索。
- siphon 在艏、上面是 pseudopation（Leo VI《Taktika》）；木塔在中桅旁、中線兩側各一座、中間留走道（Pryor）；兩支舷側舵；艏部有吊錨架（periboloi）。
- Yenikapı YK16（Archaeonautica 2021）：龍骨 16×14 cm、肋骨 20–24 cm 一站、有 keelson。
- 顏色：瀝青（黑船殼）、Skylitzes 插畫的赭色桅桁與金圓飾、Anna Komnene 的鍍金獅頭噴口（11 世紀末）。
- ⚠ Pryor 的書只讀到搜尋片段（沒逐頁讀）；吃水、舷弧、桅位、舵與木塔的尺寸都沒查到 ⇒ 設計決定（design/plan.json provenance 每一條都標了）。

## 座標與比例
- 0.1 m／格；框 416 × 129 × 256；x 船頭朝 +x、中線格 y 64（格 y ↔ 128 − y）、z 0 ＝ 龍骨底。水線 z 11（吃水 1.1 m）、主甲板面 z 21（船中）。
- 組裝件 `erina-dromon-01m-assembly`（主作品「持火號」）；船殼 `erina-dromon-01m`（任務作品、tags sub）；子作品都用整船的框、關聯 at 0,0,0（帆桁、武器除外）。全部記了 meters_per_voxel。

## 設計（design/；每支重跑逐位元組相同）
| 程式 | 產出 |
|---|---|
| `dro.py`＋`plan.json` | 連續幾何：龍骨線（rocker）、艏艉柱弧、舷弧、船中剖面（圓舭 → 直舷 → 外張 → 直立舷牆）、豐滿度（水線下尖、水線上豐滿） |
| `draft_lines.py` | 新圖紙 01 線形 `sheet01_lines.png`、讀數 `verify_lines.json` |
| `draft_hull.py` | 船殼（殼厚 2、舷牆 0.8 m、肋骨每 1 m、keelson、艏艉柱、spur、塗裝帶、槳口（下層外板、上層舷牆，真的開洞）、siphon 噴口）、主甲板（板＋橫樑、兩個艙口）、艙底走道（兩舷留排水縫） |
| `draft_upper.py` | 艏樓、木塔＋木橋、舵橫樑與舵箱、吊錨架、帆腳繫柱、艉旗桿、藥庫隔艙壁、五座梯子 |
| `draft_steer.py` | 舷側舵（S；P 用鏡像） |
| `draft_rig.py` | 兩根桅（桅頂滑車箱＋小金十字）、兩根三角帆桁（兩截搭接、三道綁繩） |
| `draft_weapons.py` | siphon、弩砲、投石機（0.05 m 元件）＋ `sheetW_weapons.png` |
| `placements.py` | 所有外部模型的擺法＋零碰撞讀數 `verify_models.json`（迴旋的每個停靠角度也量） |
| `draft_sheet.py` | 總圖 `sheet00_general.png` |
| `apply_all.py`／`apply_rig.py`／`apply_weapons.py`／`restamp.py` | 落地（每刀讀回 placed；改清單只落差分、讀回缺 0／多 0／色差 0） |

## 讀數（2026-10-18）
- 線形：水線長 28.0 m、水線寬 3.59 m、吃水 1.1 m、排水量約 58 t、Cb 0.51。
- 格子（開槳口後）：船殼 43,500；主甲板 11,684；艙底 2,872；艏樓 1,668；木塔 3,370；吊架 858；藥庫 847；梯子 296；前桅 1,820；中桅 1,053（合計 67,968；桅穿過甲板重疊 156 ⇒ 引擎 view 67,812／67,812）。
- 設計讀數：部件互不重疊、全船 1 個元件、封閉空腔 0、船殼與甲板兩舷鏡像差 0。
- 模型 17：siphon、弩砲 ×3、投石機、舵 ×2、帆桁 ×2、火藥桶 ×6、錨 ×2 —— 零碰撞（格心＋八角）全部 0；投石機 0°／180° 兩個停靠角也 0。siphon 原本設 ±20° 迴旋，獅頭會掃進艏部舷牆（~200 格）⇒ 改固定朝前（史料是噴嘴會轉，之後擴充）。
- 帆 3（前帆、中帆、艉旗）、繩 16；引擎 view：models_broken 0、ropes_broken 0、sails_broken 0。
- Blockside 匯入檢查（2026-10-18 晚，分支 `erina/greekfire`：geo、船員已填、弩砲與投石機不算砲）：**✗ 0、⚠ 0**；第一次（暫存 worktree，`references/shipcheck_dromon_2026-10-18.md`）：✗ 0、⚠ 5；砲 5 門 0 缺人、取用點 4、4／5 門走得到取用點、錨 ×2 認成模型＋ring＋hawse、甲板 4、梯子 4。
  - ⚠ 全是遊戲設定檔那側：geo 沒填；船員預設（軍官 0／4、陸戰隊 0／12、桅頂水手 0／8、送藥手 3／4）照大型風帆戰艦排 —— 三角帆船沒有桅頂平台。

## 給遊戲那側（ame）填 geo 用的高度
- 水線 z 11；主甲板面（第一層空氣）船中 z 21、艏 z 24–25、艉 z 28–32；艙底走道 z 5；艏樓平台 z 41；木塔平台 z 39。
- siphon 噴口 z ≈ 31（離水線 2.0 m；Pryor 要 ≤ 1.5 m —— 管在藥槽頂上，照實記）；弩砲砲口：艏樓 z ≈ 48、木塔 z ≈ 44。
- 前桅頂 z 117、中桅頂 z 86；前帆尖 z 218、中帆尖 z 161。船殼 x 38（艉柱頭）～ 353（艏柱頭）、spur 到 x 396。
- 史料航速沒查；雙層 100 槳的 dromon 槳速一般估 7–10 節（⚠ 沒查證）⇒ `cfg.base` 7（Blockside 分支 `erina/dromon-oars`，未合併）。

## 踩過的坑（這次）
- 甲板上的砲要有**火藥取用點**：那一層要有 9×9 平地（頭上 8 格空、不碰砲）—— 艏樓與木塔一開始太擠 ⇒ ✗；艏樓加長、塔上的弩砲挪位。
- **送藥手**只在砲口 x、離中線 ±9 格、半徑 4 格內找站位，而砲外框外 1 格不能站（40_crew.js blocked）⇒ 兩舷的塔上弩砲內端要退到離中線 9 格、兩塔之間要有木橋。
- **砲班站位**照砲外框排（砲尾兩側往外 3 格、往船內 10 格）⇒ 平台邊太窄就少人；艏樓平台往外挑到 ±10 格。
- 遊戲會**照名字退路**認錨：關聯叫「舵橫樑與錨架」被當成格子錨 ⇒ 改名「舵橫樑與吊架」＋掛真的錨模型。
- `meta` 批次檔不收 null ⇒ 要清 meta 的繩一條一條 `meta=none`。
- `view region=` 只裁格子、模型帆繩照畫 ⇒ 特寫用 `target=`＋`zoom=`。

## 槳（2026-10-18 下午；design/draft_oars.py、apply_oars.py、造船規格 §9.10.2）
| 項目 | 下層 | 上層 |
|---|---|---|
| 支數 | 每舷 25（槳口 x 78 + 10k、z 15–17） | 每舷 24（槳口 x 83 + 10k、甲板面 +3～+5；第 18 位 x 253 讓給投石機） |
| 元件 | `erina-dromon-01m-oar-lower`：3.85 m（裡 1.045、外 2.805）、槳葉 0.81 m、入水 12°（Pryor 11°） | `erina-dromon-01m-oar-upper`：4.7 m（裡 1.3、外 3.4）、槳葉 0.85 m、入水 28°＋照舷弧補 −2.8°～＋9.0° |
| 槳手 | 站艙底走道 z 5（甲板橫樑底 z 18 ⇒ 頭上剛好 14 格；不放划手座） | 站主甲板 |
| 槳葉中心離水 | 0 | −0.02～＋0.03 m |

- 模型 115（原 17 ＋ 槳 98，掛在船殼作品裡，名字 `oar-S-L01`…；左舷 mirror=y）；meta `kind=oar rowers=1 side stroke_deg=30 dip_deg=12 bank`。
- 讀數：碰撞 0（格子＋其他模型都算）；照遊戲排槳手 98／98；槳口旁 8 格內有船殼 98／98；左右各 49。反向對照：少一支 ⇒ 48／97；沉 3 格 ⇒ 只有那支報 10 格。
- 引擎 view：models_drawn 115、models_broken 0（overlays/final_oars.png）。
- 改動：船殼開槳口（刻 2,548、補 1,372，讀回缺 0／多 0／色差 0）；藥庫隔艙壁 x 128／146 ⇒ 130／147、火藥桶跟著挪一格（讓開下層第 6、8 位）。

## 藥庫的補給（2026-10-18 晚；design/draft_stores.py、apply_stores.py）
- Tim：「彈藥箱可以有不同外觀(但實際上都能補彈)」⇒ 憲法號的火藥桶 ×6 換成希臘火陶罐 ×4（`erina-dromon-01m-store-amphora`，377 格）＋弩箭箱 ×2（`-store-boltbox`，268 格），0.05 m、scale 0.5；meta 照舊 `kind=powder powder_lb=100`。
- 遊戲的取用點輪流擺不同樣子的桶（Blockside 23_powder.js）⇒ 一罐一箱一罐。零碰撞 0；引擎 view models_broken 0。
- 匯入檢查（Blockside 分支 erina/ammo-weapons）：砲 4 門、0 門缺人、取用點 4、✗ 0 ⚠ 2 —— ⚠ 木塔兩座弩砲的砲旁藥箱跟取用點在走路格上不連通（送藥手照直線走）。
- Blockside（分支 `erina/dromon-oars`，未合併、未提交）：`cfg.base` 7、reimport ⇒ 匯入檢查 ✗ 0 ⚠ 0、槳 98（左 49 右 49）、槳手 98／98、船員 160。無頭 Chrome（seed 3、開局 2500 m、風 0.3）：有槳 3.5–3.8 m/s、沒槳 2.8–3.2 m/s。
- 坑：模型名字不能有 `/`（造船規格範例原本寫 `槳/oar-S1`，已更正）；槳口 2 格高時槳柄往裡翹出洞頂 ⇒ 3 格高、pivot 洞底＋1；元件角度要用格子取整後的實際角度算傾角（不然上層全部高 0.33 m）。

## 弩弦（2026-10-18 晚；design/apply_bowstrings.py）
- Tim：「弩炮的弦是否可以改用繩索 並在開火時有動態」⇒ 弩砲元件拿掉格子弦（2145 → 2105 格），登記固定點 `string-a`（1,31,20）、`string-b`（29,31,20）、`nock`（15,20,17：拉滿）、`nock-fire`（15,31,20：放出去，兩弓臂尖連線上）。
- 每座弩砲兩條繩（建在艏樓／木塔子作品裡）：`<模型>-弦-a`（string-a → nock）、`-弦-b`（nock → string-b），兩端 `model:<模型>/<固定點>`、slack 1、粗 0.15、`kind=bowstring anim=gun rest=nock fire=nock-fire`。
- 遊戲（Blockside 26_gunanim.js）：放箭那一刻扣弦點彈到 nock-fire、過頭再回來，裝填時照進度拉回 nock；弩砲迴旋時弦跟著轉。量過（木塔右舷）：扣弦點 y 79.05 → 0.13 秒 83.13（過頭）→ 3.2 秒 78.95。
- 引擎 view：繩 22、ropes_broken 0、models_broken 0（overlays/ballista_string.png）。

