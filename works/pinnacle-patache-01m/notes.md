# 聖羅曼號（Santo Cristo de San Román）—— 西班牙小護航船 patache，1618 年條例 10 codos 的 navío（0.1 m／格）—— 建造筆記

委託：TASK-0970（Tim 2026-10-28「/scp-task 970 GO」；母單 TASK-0964 的 8 種候選之一）：《Blocksail》1666 加勒比船型 —— 西班牙小護航船 patache／fragata，船隊護衛、傳令（aviso）、海岸巡防。照造船規格雕刻、匯入 Blockside、接進 Blocksail 船型清單。
流程：照 `Ship_Steps` 步驟表走（貼在 TASK-0970 的驗收標準）。帆船、露天甲板舷牆砲門的輕砲＋迴旋砲、大帆船式的船頭、全木 ⇒ 刪步驟 12（砲門蓋板）、13（動力與材質）。

## 方向
- 船名：Armada de Barlovento（加勒比的向風艦隊，海岸巡防）1690 年有一艘 patache「el Santo Cristo de San Román」（Sigüenza y Góngora 1691〔查〕）⇒ 借它的名字 **聖羅曼號**；尺寸、帆裝、砲照 1618 年條例 10 codos 那一級（沒有這艘船自己的數字）。
- Tim 2026-10-28：「3 或 4 磅 請另外做炮(炮只有同型號共用模型)」⇒ 步驟 9 的輕砲做新的通用部件，⛔ 不拿 6 磅縮。
- ⚠ 步驟 14 回頭改過（遊戲的走路格與取用點，細節在步驟 14 那一節）：船腰砲門 x 132–212 → **132–204**、**沒有主艙口**、迴旋砲 **8 門全在船腰舷牆頂**（x 133／168／189／211），舵輪 x 89；下面步驟 3–11 那幾節寫的是當時的版本，現況以 plan.json 與步驟 14 為準。

## 座標約定（照康塞普西翁號／收穫號，產生程式也從它抄來）
- 空間 400×320×260；X 船長（船頭 +X）、Y 船寬（中線 ＝ 第 160 格，鏡像 y ↔ 320 − y；抄來的工具把中線寫死成 160）、Z 高度（z 0 ＝ 龍骨底面）；P ＝ y < 160。
- 0.1 m／格（船殼、組裝件書卡都記了）。西班牙尺寸用 codo de ribera ＝ 0.57468 m ⇒ 1 codo ＝ 5.7468 格（研究筆記 §1）。
- 「在不在船裡」：|y − 160| ≤ 半寬（格心判斷）⇒ 兩舷逐格對稱。

## 作品
- 船殼 `pinnacle-patache-01m`「聖羅曼號 船殼」：任務作品（委託 TASK-0970、10 token 已發），`tags=sub`。
- 組裝件 `pinnacle-patache-01m-assembly`「聖羅曼號」：主作品（沒標 sub），parent 船殼；關聯 `船殼` at 0,0,0。
- 子作品照康塞普西翁號的拆法（甲板每層一件、梯子、桅、帆桁、裝飾、彈藥庫、舵、錨架…），parent 船殼、`tags=sub`，建立時就記 0.1 m。

## 產生程式
- `design/` 從康塞普西翁號 `apex-two-galeon-01m/design/` 抄來（它又出自藍鯊號 → 收穫號）；每個檔第一行寫直接出處。`plan.json` 照 patache 重寫。

## 沿用的現有元件（`work sub=components`，2026-10-28 查）
- 迴旋砲：皇家號 pierrier `apex-one-reale-01m-gun-pierrier`（gun:pierrier；西班牙的 verso／pedrero 同一類）。
- 舷側輕砲：⛔ 不縮放別的口徑（Tim 2026-10-28）⇒ 步驟 9 新做一件通用部件。
- 舵輪＋座 `basecamp-frigate-constitution-01m-wheel`／`-wheel-stand`、羅經櫃 `summit-night-falcon-01m-binnacle`、絞盤 `basecamp-ember-01m-capstan`、小艇 `basecamp-ember-01m-boat`（或憲法號 whaleboat）、錨 `basecamp-frigate-constitution-01m-anchor`、火藥桶 `basecamp-frigate-constitution-01m-powder-barrel`、門 `gura-pinas-01m-door`、廚房 `gura-pinas-01m-galley`、方帆桁 `basecamp-frigate-constitution-01m-yard-*`、船尾燈 `gura-tridente-01m-lantern`。
- 自己做：船首像、船尾鏡板裝飾、船名、三角帆桁、輕砲。

## 步驟 3 找資料與新圖紙（2026-10-28）
查證：研究代理 ⇒ `references/research_patache_2026-10-28.md`（每個數字標〔查／估〕）。最硬的出處是 FG 2009（1607／1613／1618 Ordenanza 的尺寸表與 1618 條文英譯，逐條轉錄原文）；1613 年的噸位公式拿表格回算過，大船各級都對到小數位。
- 單上的「沒核」那幾條核過了：
  - 「MUCAIN 37–200 t」查不到這個來源；有依據的範圍是 55–96 t（1588 年、1613 年、Serrano Mangas 60–100 t），上限到約 210 t（1669 San Luis）。
  - 「San Luis 210 t、38 門；Soledad 50 t、24 門」出自英文維基的 Maracaibo 條目（引 Bradley 1999 p.172），不是 Patache 條目；Soledad 另有 10 門（Earle）、14 門（Marley）的說法（經部落格轉述、原書沒看到）⇒ 24 門不採用。
  - 查不到：1650–70 年的實船尺寸、同時代 patache 的圖、量過船殼的沉船、1618 年 art.72–91 的桅桁尺寸、Torres Ramírez／Serrano Mangas／Phillips 書裡的船表。
- ⇒ 採用 **1618 年 Ordenanza 的 10 codos navío**（106⅛ toneladas）：1613 年同寬那一級明文叫 patache（94½ t），1618 年的表沿用到 1660 年代。英國噸位約 90–107 tons（研究〔估〕）。
設計 `design/plan.json`（每個數字的 src：參考資料／研究的推／設計決定）。程式：`lines.py`（照抄，沒改）、`layout.py`（照抄）、`draft_lines.py`（對照那一格的鍵 concepcion ⇒ ordenanza）、`draft_layout.py`（一層甲板＋tolda／castillo 的「上一層」表、畫的範圍與比例、喙與帆的高度）；新寫 `tools/tune_lines.py`（掃 s_aft × s_fwd × aft_pow 對 art.21）。

| 項目 | 本船（格 ＝ 0.1 m） | 1618 年 10 codos（1 codo ＝ 5.7468 格） |
|---|---|---|
| 甲板長（主甲板 z 32，艏柱到艉柱） | 206.9 | eslora 36 ＝ 206.9 |
| 龍骨 | 172.4 | quilla 30 ＝ 172.4 |
| 最大寬（含外板） | 57 | manga 10 ＝ 57.5（寬只能是奇數格） |
| puntal（龍骨頂到最寬處） | 26.0 | 4½ ＝ 25.9 |
| plan（平底寬） | 28.8（參數；格子量到 z 5 → 25、z 6 → 35 夾住） | 5 ＝ 28.7 |
| 艏／艉 rake（到主甲板） | 23.0／11.5 | 4／2 codos ＝ 23.0／11.5 |
| mura／cuadra 的寬（art.21） | 51／47 | 51.3／45.5 |
| 設計水線 | z 24（吃水 2.4 m） | 查不到；研究〔估〕0.9 × puntal |
| 排水量（水線下實心 × 1.025） | 119 t | 106⅛ toneladas 是 arqueo（容積噸），只當量級 |
| 船殼牆 | 81,893 格（3 格厚）；1 元件、空腔 0、鏡像差 0 | — |

- 🩸 線形照抄康塞普西翁號的 s_aft 0.45／s_fwd 0.59／aft_pow 2.0 ⇒ cuadra 55（要 45.5）：本船短，「艉柱往前 L/4 ＋ 2 codos」的 2 codos 佔的比例大 ⇒ `tools/tune_lines.py` 掃 27 組 ⇒ 0.50／0.51／1.2（mura 51、cuadra 47；排水量 133 → 119 t）。art.22（hold beams 的寬 ＝ 上一層甲板）是多層甲板船的規矩，本船一層甲板 ⇒ 只照實列（艙深一半 z 16 寬 53、主甲板 57）。
- 甲板（甲板面 z）：艙底板 orlop 12（x 92–230）、主甲板 main 32（舷弧 aft 6、fwd 3）、tolda 50（到 x 122）、castillo 50（從 x 222）。⚠ 條文的 tolda 是「low」（約 2 codos ＝ 11.5 格）⇒ 遊戲站人要頭頂 14 格 ⇒ 抬到主甲板上 18（設計決定）；castillo 條文沒寫（查不到）⇒ 短的一座、同高。
- 舷頂 `top_curve`（Ship_Ends §2）：tolda 62、船腰 50、castillo 60；船樓前後緣 10 格的 smoothstep、船尾翹 4、船頭翹 3；`stern_tumble` z 34 以上船尾往裡收。
- Ship_Ends 只取適用的那幾項：⛔ 不做 counter 與 stern walk（1618 art.69：船寬 15 codos 以下不准加船尾走廊）、⛔ 不做 beakhead 艙壁（前桅照 art.67 立在艏柱 rake 中點 x 254，主甲板那一層離艏柱只有 11 格 ⇒ 沒有地方往後退一道艙壁）；船頭做 espolón 平台＋寬帶＋cheek（步驟 6）。
- 砲 **8 門**：主甲板船腰每舷 4 門 4 磅（研究〔估〕：1522 年 100 t 4 門、1552 年 100–170 t 8 門、1588 年 patache 6–14 門）；砲門 art.42（下緣甲板上 1 codo ＝ 6 格、1¼ codos 見方 ＝ 7 格）；間距（邊到邊）17–18 格；砲門頂到舷頂 5 格。迴旋砲 6–8 門在步驟 9 擺在舷牆上（不開砲門）。沒有船尾追擊砲。
- 桅（三根）：前 x 254（艏柱 rake 中點，art.67）、主 x 156（龍骨中點，art.66）、後 x 100（立在主甲板、穿過 tolda）、艏斜桅腳 (258, z 36) 仰 30°（art.68：腳在主甲板）。長度研究〔估〕：主 13.8 m（2.4 × manga）＋上桅 6.9、前 11.7＋5.9、後 8.3、艏斜桅 9.4；帆桁 主 course 12.1／topsail 6.6、前 9.7／5.3、後三角帆 9.7、cebadera 6.5。主桅頂離水線 17.9 m。
- 讀數：產生程式重跑 5 個輸出檔逐位元組相同。**反向對照**：`draft_lines.py --probe=half_beam=+3` ⇒ 寬 57 → 63、mura 51 → 55、cuadra 47 → 53；`--probe=forefoot_x=+3` ⇒ 只有甲板長、龍骨 +3（寬、rake 不變）；`draft_layout.py --probe=port=main:2:+3` ⇒ 只有第 2 門兩邊的間距變（17／18 → 20／15）。
- 圖紙：`design/sheet01_lines_v1.png`（側面、半寬、橫剖面、主尺寸）、`sheet02_layout_v1.png`（甲板、砲門、桅帆、俯視、砲位表）。

## 步驟 4 船殼落格、砲門、塗裝、船尾窗（2026-10-28）
- 標記 `船殼:begin`（upto=start）→ `tools/stamp_lists.py pinnacle-patache-01m 0 masks/hull/hull_01.vox.txt`（81,893，placed ＝ 清單）→ `船殼:end` → `砲門:begin` → carvevox `masks/ports/carve.vox.txt`（帶刻之前的顏色守門，1,471）→ stampvox overwrite=1 `masks/ports/paint.vox.txt`（5,901）→ `砲門:end`。
- `draft_ports.py` 沒改程式；plan 新寫 `paint`（三條 wale art.52、wale 舷弧多翹 艉 3／艏 3、tolda 與 castillo 舷牆赭黃底紅菱格、舷頂金；康塞普西翁號的 wreath、counter 扇形、beakhead 那一面都不用）與 `stern`（tolda 底下船長室 3 扇窗 z 42–46：最外一格刻開、第二格玻璃 `masks/glass/stern_glass.vox.txt` 75 格（步驟 6 做成子作品）、後面刻穿到艙裡）。
- 讀數（作品一律從 CLI 匯出讀）：
  - `tools/check_hull.py`：結果帳 作品 81,893 ＝ 設計，缺 0、多 0、色差 0；線形對照 99 點差 0；**反向對照** probe_x=160（那一站 +3）⇒ 只報那一站 10 點、最大差 3（🩸 第一次給 probe_x=150 報 0 點：站是每 40 格一站，150 不是站 —— 是尺沒量到，不是船對）。
  - `tools/check_stage3.py`：結果帳（船殼 − 刻 ＋ 換色）80,422，缺 0、多 0、色差 0；8 個舷側砲門開口裡實心 0；**正向對照**（同一把尺量 `船殼:end`）⇒ 8 個全報。
  - 引擎 `stats structure=1 mirror=y:160`：1 元件、封閉空腔 0、鏡像差 0。
- 過程圖：`overlays/step4_hull.png`、`design/sheet03_ports_paint_v1.png`。

## 步驟 5 甲板、梯子、艙房（2026-10-28）
設計 plan.json `decks_build`；產生 `design/draft_decks.py`（照抄，沒改程式）⇒ `masks/decks/<層>.vox.txt`、`masks/ladders/<上面那層>.vox.txt`、`ladder_points.json`、`verify_decks.json`、`sheet04_decks_v1.png`；落格 `design/tools/build_decks.py`。
- 甲板 4 層（子作品 `-deck-{orlop,main,tolda,castillo}`、組裝件關聯 `甲板-<層>`）；主艙口 x 190–200（主桅與船首樓梯子之間）；break 兩道（tolda 前緣 x 122、castillo 後緣 x 222：艙壁兩扇門 dy ±12＋7 格胸牆，梯子頭留口）；桅孔照傾斜軸線（後桅立在主甲板 ⇒ 只開 tolda 的孔）。
- 梯子 3 座（子作品 `-ladders-<上面那層>`，關聯 `梯子` meta `kind=ladders`，固定點 `<梯名>.foot／lo／hi／head`）：艙底板→主甲板（中線 x 166 往船頭爬、主甲板開井）、主甲板→tolda（中線、梯頂 x 123 貼著 break 122）、主甲板→castillo（中線、梯頂 x 221 貼著 break 222）。砲架往裡伸到 |dy| 約 10 ⇒ 梯子都放中線、break 的門讓到 dy ±12。
- 甲板 meta：每層子作品 `export format=vxk links=none` ⇒ Blockside `src/decks.py` ⇒ `design/decks_meta.tsv`（name 換成 plan 的名字）⇒ `work sub=meta`（4 條）：level 0 艙底板（floor 113:13–230:13、thick 3）、1 主甲板（舷弧 59:39 → 124:33 → 196:33 → 260:36、thick 4）、2 tolda（51、thick 3）、3 castillo（51、thick 3）。
- 艙房：沒隔（同康塞普西翁號）。
- 讀數：設計那一側：重疊 0、砲門往艙裡被擋 0、梯子點問題 0、鏡像差 0、每層都接得到（艙底板 2 格的封閉空腔照實填進那一層）；`tools/check_decks.py`（每件從匯出讀）：7 件 21,192 格，缺 0、多 0、色差 0、跟船殼／彼此重疊 0；梯子點（組裝件 parts）12／12、跟設計差 0、空氣／腳下／頭頂 14 格問題 0；組裝件 101,614 格、1 元件、空腔 0。產生程式重跑逐位元組相同。**反向對照**：`draft_decks.py --probe=drop_ladder=castillo` ⇒ 2 座、castillo 走不到（reach 空）。
- 預覽 preset：`藏船殼`。過程圖 `overlays/step5_decks.png`。

## 步驟 6 裝飾、窗的玻璃（2026-10-28）
`draft_deco.py` 框架照康塞普西翁號（plan.json `espolon`、`figurehead`、`stern_deco`）；改：FONT 補 S／R／M、船頭的 x 門檻 400 → 200、圖的範圍與比例；`tools/build_deco.py`、`tools/check_stage5.py` 拿掉 stern-deco（沒有 stern walk）。
- `-espolon`「船首喙」1,672：Ship_Ends §4.3 的整片平台＋knee 縮成本船 —— 甲板頂 z 36、伸出艏柱 34（1618 art.45：manga 的 3/5 ＝ 6 codos）、半寬 9 收到 2、側板包到 z 32、欄杆 7 格每 4 格一根柱；knee 從艏柱 z 6 掃到 x 286、水線下白、兩條 trailboard 金線。
  - 🩸 v0 甲板頂 37 ⇒ 艏斜桅那條線（半徑 3）被擋 6 格（出船頭 x 264 底 36.5）⇒ 36。
- `-figurehead`「船首像」531：鍍金的戴冠獅子縮成 1.6 m（x 282–298），頭在喙尖。🩸 v0 x 281 ⇒ 尾巴尖 (281, z 46) 在艏斜桅半徑 3 裡（1 格）⇒ 往前 1 格。
- `-hackebort`「船尾拱形板」1,008：船尾頂上 z 66–84、半寬 14 收成拱；奶油底金框、**Santo Cristo**（十字架上的基督：深色十字、膚色、白腰布、金光環）、紅帶金字 **S ROMAN**（從船尾看從左讀 ⇒ 鏡像差 40 照實報）；板頂一盞船尾燈（三叉戟號 `lantern` scale 0.5、kind=light；不是旗艦 ⇒ 一盞〔估〕），腳下實心、頭上空。坐在船殼頂上那 42 格照實跳過（不蓋船）。🩸 v0 名帶 z 65–71 ⇒ 字的最下一列壓在板底的金框上 ⇒ 66–73。
- ⛔ 沒有 stern walk、兩舷側廊（1618 art.69：船寬 15 codos 以下不准）、沒有 beakhead 艙壁、沒有 head 寬帶（喙接在船頭中段、castillo 前面沒有艙壁可以起帶）。
- **窗的玻璃**（Ship_Materials）：子作品 `-stern-glass`（船長室 3 扇窗 75 格），組裝件關聯 `船尾窗玻璃` meta `material=glass`；玻璃格在步驟 4 的刻裡已經從船殼拿掉。
- 讀數：`tools/check_stage5.py` 三件結果帳缺 0／多 0／色差 0；跟船重疊 0、部件之間重疊 0；艏斜桅那條線被擋 0；`tools/glass_seal.py` 3 片漏 0、判不出 0（**反向對照** `--drop=1` ⇒ 漏 1 片）；組裝件 104,900 格、1 元件、空腔 0、link_overlap 0。**反向對照**：`draft_deco.py --probe=shift=figurehead:3` ⇒ 獅子鏡像差 0 → 531、其他件不變。產生程式重跑逐位元組相同（落格之後重跑：自己的件與玻璃都扣掉）。
- 過程圖：`overlays/step6_deco.png`、`design/sheet05_deco_v1.png`。

## 步驟 7 桅與帆桁（2026-10-28）
設計 plan.json `rig_build`（長度與位置在 `masts`）；產生 `design/draft_masts.py`（照抄康塞普西翁號；改：斜桅頂桅照 plan 有沒有 `sprit_top`（本船沒有）、`heel_ext` 桅腳往下接、量 lateen 伸出船尾的高度照線形最高處、圖的範圍）；落格 `design/tools/build_masts.py`（三根桅＋艏斜桅）；讀數 `tools/check_stage6.py`（拿掉 bonaventure）。
- 桅（每根一件子作品）：前桅 2,045（下桅＋桅樓 r 10＋中桅）、主桅 2,691（下桅＋桅樓 r 11＋中桅）、後桅 318（只有下桅、沒有桅樓）、艏斜桅 794（沒有斜桅頂桅）。桅樓半徑：遊戲的桅頂水手站在半徑 9／12 那一圈 ⇒ 不能再小。
- 帆桁 6 根（外部模型，掛在各自的桅子作品）：方帆桁 5 根沿用憲法號的帆桁元件、只沿長度縮放 —— 前 course 9.7 m（mizzen-topgallant ×0.98）、前 topsail 5.3（mizzen-royal ×0.82）、主 course 12.1（main-topgallant ×0.85）、主 topsail 6.6（mizzen-royal ×1.0）、cebadera 6.5（mizzen-royal）；三角帆桁 1 根新做 `-yard-mizzen-lateen`（9.7 m、40°；吊點前端往後 40%、meta yard=gaff、rig=lateen）。
- 艏斜桅孔：船頭牆刻 69 格（標記 `艏斜桅孔`），孔由艏斜桅填滿。
- 🩸 組裝件 2 個元件：主桅整根（2,673 格）浮空 —— 桅腳 z 8 照抄康塞普西翁號的「龍骨頂 ＋ 4」（它的牆 4 格），本船牆 3 格、中線的船殼只到 z 4；甲板的桅孔半徑 3 比桅 2 大 ⇒ 哪裡都沒碰到 ⇒ plan `rig_build.heel_ext.main` 3：桅腳往下接 3 格坐到船殼上（軸與平台不動 ⇒ 甲板的孔不變）；`tools/delta_apply.py` 刻 6、貼 24 ⇒ 1 元件。
- 讀數：`tools/check_stage6.py` 桅 4 件＋三角帆桁 1 件結果帳缺 0／多 0／色差 0；船殼（砲門:end − 艏斜桅孔 69）80,353 ＝ 作品；帆桁模型 6 根 meta 與來源固定點問題 0；帆桁穿船 6 根全 0；組裝件 110,679 格、1 元件、空腔 0、link_overlap 0。跳過的格：前桅腳插進船頭 deadwood 28、主桅腳 6、艏斜桅腳壓到甲板 4（同康塞普西翁號）。主桅頂離水線 17.9 m；三角帆桁後端在船尾裡 0.6 m。**反向對照**：`--probe=pivot=yard-main-course:-80`（放到船殼的高度）⇒ 只有那一根報 38 格。產生程式重跑逐位元組相同。
- 過程圖：`overlays/step7_masts.png`、`design/sheet06_masts_v1.png`。

## 步驟 8 索具、帆、旗（2026-10-28）
設計 plan.json `rigging`；產生 `design/draft_rigging.py`（照抄康塞普西翁號；改（`scratchpad` 的 patch 照字串一條一條換、每條斷言只出現一次）：前、主桅有桅樓＋中桅（MASTS），後桅只有下桅 ＝ 康塞普西翁號 bonaventure 那一套（ALL）；拿掉上桅帆、後中桅帆、斜桅頂桅與斜桅頂帆、bonaventure 的支索與 sheet（照 plan／帆桁有沒有）；主桅繩梯落腳在主甲板、主支索綁前桅 castillo 上、後桅支索綁主桅主甲板上；船尾旗掛在後桅三角帆桁後端；bobstay 的高度照 plan）⇒ `masks/rigging/channels.vox.txt`、`rigging_plan.json`、`textures/{ensign,cross_course}.png`、`verify_rigging.json`；套用 `design/tools/rigging_apply.py`（沒改）。
- **channels**（`-channels`，關聯 `支索板`，兩舷一件）978 格：每舷 shrouds 前 4、主 5、後 2（＋中桅 backstay 前、主各 1）；主桅那一排在船腰舷頂下 2 格（砲門頂之上）、從桅前 8 格起往後排。
- 固定點 96、繩 68（shrouds 22、中桅 shrouds 8、futtock 8、backstays 4、stays 5 —— 前支索拉到艏斜桅、前中桅支索到艏斜桅頂、主支索到前桅 castillo 上、主中桅支索到前桅桅樓後緣、後桅支索到主桅；艏斜桅 4、帆自己的繩 17）。
- **ratlines 用橫繩組**：8 組（前、主 × lower／topmast × 兩舷），下桅 4 組 `climb=1` 繩梯（foot：前 castillo、主 主甲板的舷牆內側往裡 3 格；head：桅樓靠這一舷的邊），站不站得住先量過 —— 問題 0。後桅沒有桅樓 ⇒ 不做 ratlines。
- 帆 8：前／主 course（勃艮第十字）、topsail、後桅三角帆（clew (62, z 72)、sheet 綁船尾舷頂 x 56、tack 綁 tolda 前緣 x 118）、cebadera、船尾旗（勃艮第十字，後桅三角帆桁後端）、主桅頂紅長旗。
- **帆裝三段**（Ship_Rigging §9.1）：
  | 帆裝 | 張哪幾面 |
  |---|---|
  | 收帆（1） | fore-topsail、main-topsail（2 面） |
  | 戰鬥帆（2） | 收帆的 2 面 ＋ mizzen-lateen（3 面） |
  | 滿帆（3） | 戰鬥帆的 3 面 ＋ fore-course、main-course、spritsail（set 3）（6 面） |
- 讀數：channels 結果帳 0 差；CLI 繩 122（含展開的橫繩）、ropes_broken 0、帆 8、sails_broken 0；meta 帆 8／8、帆自己的繩 17／17、sail 標錯 0；帆桁 meta 的 sail 都是某一面帆的名字；組裝件 111,657 格、1 元件、空腔 0、link_overlap 0。固定點落在實心上 26 個 ＝ 兩座桅樓邊與桅樓後緣（固定點本來就釘在那幾格上；康塞普西翁號同類 47）。**反向對照**：`draft_rigging.py --probe=nometa=main-topsail.sheet-S` ⇒ 只報那一條。產生程式重跑逐位元組相同。
- 過程圖：`overlays/step8_rigging.png`。

## 步驟 9 砲（2026-10-28）
Tim 2026-10-28：「3 或 4 磅 請另外做炮(炮只有同型號共用模型)」⇒ 4 磅砲新做一件通用部件，⛔ 不拿 6 磅縮（Ship_Guns §2.2 原本寫「只差口徑照現有的縮放」—— 照 Tim 的新規則）。
- **新通用部件 `pinnacle-patache-01m-gun-4l`**「4 磅長砲（gun 4l，鐵砲管＋兩軸四輪砲架；通用部件，0.05 m）」：產生程式 `design/draft_gun4l.py`（結構出處風暴角號 draft_guns 的 Part／tube／砲架；plan.json `gun4l`）⇒ `masks/gun4l/gun-4l.vox.txt`、`verify_gun4l.json`。13×46×20、1,659 格、1 元件、空腔 0、左右鏡像差 0；砲管（cascabel 到砲口）2.2 m、耳軸高 0.73 m；固定點 muzzle（內膛空格）／breech／cascabel／trunnion／train／eye-aft／eye-fwd；作品預設 meta `kind=gun, gun=4l`（遊戲砲種表本來就有 4l）。座標照 Ship_Guns §4.1（x 中線、砲口 +y、z 0 ＝ 甲板面），pivot ＝ 砲架前緣中間 (6.5, 28, 0)。
  - 🩸 v0 耳軸 0.53 m（AZ 10）⇒ 砲軸在主甲板上 5.25 格、砲門下緣在甲板上 6 格（art.42）⇒ 8 門砲口都卡在砲門下緣、退到砲口在船殼裡 3–22 格 ⇒ AZ 14、cheek 加高、輪子加大（`delta_apply` 刻 732、貼 1,059＋61；作品框 16 → 20、固定點重登）。
- 設計 plan.json `guns_build`；產生 `design/draft_guns.py`（照抄康塞普西翁號；加迴旋砲那一段 —— 出處拉貝爾號 draft_guns：插在舷牆頂、命名「迴旋砲-<舷><序>」排最後）⇒ `guns_placement.json`、`verify_guns.json`；落格 `design/tools/build_guns.py`（砲名表換成兩種）；讀數 `tools/check_stage8.py`（④ 迴旋砲量砲口正下方那一層的舷頂）。
- **16 門**（全部外部模型、掛在所在甲板的子作品上；P 舷 mirror=y；meta kind=gun、gun、deck、side、port）：
  - 主甲板船腰 4 磅 ×8（每舷 4，砲門 x 132／156／181／205），退 3 格、砲口伸出 4.0–5.0 格、砲軸 z 40–41。
  - 迴旋砲 ×8：皇家號 pierrier `apex-one-reale-01m-gun-pierrier` scale 0.39（同一種砲 ⇒ 跟拉貝爾號同一份網格）、meta `mount=turret, arc=-80,80, rate=45`；tolda x 66、82，船腰 x 176，castillo x 228（讓開三組 channels）。
- 讀數（`tools/check_stage8.py`，從作品讀）：模型 16 ＝ 設計、CLI ok 16；參數 ≠ 設計 0；外框最大差 0.05；碰撞 0 門；砲口不在船殼外 0 門；meta 不合 0（4l 8、pierrier 8）；兩舷不對稱 0、砲撞砲 0。**反向對照**：`--push=砲M-S02:4`（往外推）⇒ 碰撞只報那一門 2,214 樣本；`--push=砲M-S02:-6`（往裡拉）⇒ 只報那一門伸出 −1.0；`--push=迴旋砲-S03:-8` ⇒ 只報那一門 −3.5。產生程式重跑逐位元組相同。
  - 🩸 ④ 第一次報 8 門迴旋砲「量不到」：砲口在舷頂上面，砲口那一層的線碰不到船殼 ⇒ 迴旋砲改量樞軸底下那一層（舷頂）。
- ⚠ 沒做砲具與砲索（環、breeching、tackle）—— 記在 todo。
- 過程圖：`overlays/step9_gun4l.png`（新部件）。

## 步驟 10 彈藥庫與甲板物件（2026-10-28）
設計 plan.json `gear_build`；產生 `design/draft_gear.py`（照抄，沒改程式）；落格 `design/tools/build_gear.py`。
- **彈藥庫**（`-magazine`，關聯 `彈藥庫`，meta `kind=magazine、pos=aft、powder_lb=1000`）2,621 格：艙底板 x 122–146（再往後艙底板窄到半寬 1–6 格）、水線（z 24）以下、門開在船頭那道艙壁，往前繞過主桅到艙底板梯子（x 165）。固定點 `blast` (135,160,21)、`door` (146,160,14)。火藥桶 **10 桶**（憲法號 `-powder-barrel` scale 0.2）：HAR p.314 的 1552 年條例 100–170 t 級配火藥 9 cwt 1 qr ≈ 1,036 磅〔查，OCR 重排〕⇒ 10 × 100 磅。
- **小艇架**（`-boat-skids`，關聯 `小艇架`）632 格：主甲板船腰三座橫架 x 170、183、196（橫跨主艙口與艙底板梯子的井）、橫樑底 z 47（甲板上 1.4 m，人從底下走得過）、柱 dy ±11。
  - 🩸 v0 小艇的 z 給 null 讓程式量 ⇒ 艇比兩根柱的間距窄、從橫樑底下滑進去，停在主艙口圍欄上 z 36 ⇒ 明寫 z 49（橫樑頂 ＋ 1）；🩸 只有兩座架 ⇒ 艇的外框中心往下 12 格內沒有實心（遊戲判斷模型掉不掉）⇒ 中間加一座 x 183。
- 模型（沿用現有元件）：主絞盤（餘燼號，縮成 1.0 m）主甲板中線 x 146、羅經櫃（夜隼號）tolda 中線 x 110、小艇（餘燼號 cutter 縮成 4.5 m 的 batel；小艇不是砲 ⇒ 可以縮）擱在小艇架上 x 183。
- **艙壁門**（Ship_Fittings §9.7）：門板引用藍鯊號 `gura-pinas-01m-door`；`draft_doors.py` 甲板名換成本船、門洞高度範圍 z 40 → 20 起（本船的門在 z 34–48）。4 扇：tolda 前緣 x 123.5（rotate 0）、castillo 後緣 x 221.5（rotate 180），dy ±12，meta kind=door open=side；撞實心 0、背後都是艙壁、腳下都有地板。
- **廚房爐灶**（Ship_Fittings §9.13）：引用藍鯊號 `gura-pinas-01m-galley`、scale 0.4（castillo 底下只有 15 格：主甲板 34 → 甲板樑底 47 ⇒ 0.5 的鍋頂到 z 50.5 撞甲板）；castillo 底下、主甲板中線 x 238.5（爐 x 232–244 踩在甲板面 z 34 那一段；煙囪 x 241–244 從 castillo 甲板穿出 ⇒ 甲板-castillo 刻 15 格、前桅 x 252 之前）；撞實心 0、懸空 0。⚠ 程式自己的「船尾面站得住」只認腳下正好一格（x 230 那裡甲板低一格 ⇒ 報 false）；遊戲照 0.6 m 內找走路格 ⇒ 步驟 14 的匯入檢查看。
- 艙蓋不做：主艙口在主甲板（水線上 0.9 m）—— 遊戲沒有門的開口不當成進水口（記在 todo）。
- 讀數（`tools/check_stage9.py`，從作品讀）：彈藥庫、小艇架結果帳缺 0／多 0／色差 0；模型 13 ＝ 設計、CLI ok 13；powder_lb 1,000 ＝ 10 × 100；blast 空氣、door 空氣且腳下實心；參數 ≠ 設計 0、撞實心 0、腳下 12 格內沒有實心 0；新格落在實心上 0、封閉空腔 0、浮空 0、鏡像差 0（缺的種類 wheel 在步驟 11）。甲板帳（扣掉煙囪洞）7 件 0 差；組裝件 114,895 格、1 元件、空腔 0、link_overlap 0。**反向對照**：`draft_gear.py --probe=nokind=小艇` ⇒ 只報小艇。產生程式重跑逐位元組相同（verify_gear 讀到的組裝件格數照實少了煙囪洞 15 格）。

## 步驟 11 舵、舵輪、錨（2026-10-28）
設計 plan.json `rudder_anchor_build`；產生 `design/draft_rudder_anchor.py`（照抄，沒改程式）；落格 `design/tools/build_rudder_anchor.py`。
- **舵**（`-rudder` 533 格，組裝件的外部模型 `舵`）：沿艉柱後緣（斜 19.75°）從龍骨底到 z 28（yugo z 29 底下）；3 格厚、舵葉 0.9 m 往上收到 0.4 m；水線下白、上橡木褐、每 6 格一道鐵箍。meta `kind=rudder`、鉸鏈 (70, 160.5, 0)、軸 (−0.338, 0, 0.941)、max_deg 35、turn_axis=hinge、**spin**（rudder、±35、lag 0.3）。固定點 `stock-top` (57,160,28) 離船殼 3 格。
- **舵輪＋座**：沿用憲法號雙舵輪 `-wheel`（spin rudder 540）＋木頭雙柱座 `-wheel-stand`，縮 0.13（小船），tolda 中線 x 89（後桅後面）。⚠ 1660 年代西班牙船用舵桿（pinzote），遊戲要舵輪（同收穫號、康塞普西翁號）。
  - 🩸 v0 x 104（後桅前面）⇒ 輪與座把後桅包在中間、撞 12,298／41,600 樣本 ⇒ 挪到後桅後面 x 89；tolda 的兩門迴旋砲跟著往後挪（x 66／82 → 62／74，讓開輪的外框 x 83–95）⇒ 步驟 9 重算重掛（16 門照樣 ok）。
- 🩸 重算砲時兩門放不下（砲M-P03／S03）：步驟 10 中間那座小艇架（x 183）的柱在 dy ±11，正好擋在第 3 門砲（砲門 x 181–187）的砲架上 —— 步驟 9 量砲的時候小艇架還沒落格 ⇒ 柱改 dy ±7（站在艙口與梯子井的圍欄外緣，橫樑 z 47 在砲上面不擋）；`delta_apply` 小艇架刻 332、貼 398；砲重算 16 門 ok、重掛。
- **錨**：共用錨元件 ×2（scale 0.5、kind=anchor、anchor=bower）吊在船頭舷外 x 259.4、ring z 52、錨臂順著船殼切線（rz ±63.5）、離船殼 11 格（試了 x 254–260 × z 52–58）；錨架 `-anchor-gear`（billboard 托板，關聯 `錨架`）926 格；錨鏈孔固定點 hawse-S／P (262, ±6, 41)（FG art.5：船首樓底下、盡量高；只登記、沒有開孔）。
- 讀數（`tools/check_stage95.py`，從作品讀）：舵、錨架結果帳 0 差；舵模型 CLI ok、stock-top 8 格內有船殼、舵跟組裝件重疊 0、轉 ±35° 掃進實心 0；錨 2 隻 CLI ok、撞實心 0、腳是錨架、來源有 ring；hawse 在船殼上、在那一舷；問題 0。舵輪與座撞實心 0。遊戲讀的那一份（組裝件 `export format=parts`）：舵、舵輪都有 spin。**反向對照**：`--drop=錨-P` ⇒ 只報 P 舷沒有錨。步驟 9／10 的檢查重跑：砲 16 門碰撞 0、砲口在外 16；彈藥庫與小艇架帳 0 差；組裝件 115,887 格、1 元件、空腔 0、link_overlap 0。

## 步驟 14 給遊戲的 meta 與匯入（2026-10-28）
- 組裝件的關聯 `船殼` meta kind=ship、waterline_z 24；ropecheck 122 條、244 端 ok（沒有 bind／snap）。
- Blockside 自己的 worktree（分支 pinnacle/0970-patache，從 refs/heads/dev 36da004；共用 `_cache` 先整份抄過去）：`admin.py import --work pinnacle-patache-01m-assembly --id sanroman --name 聖羅曼號` ⇒ reimport ⇒ `ids` ⇒ reimport。
- 給遊戲那側填的 geo（z 從龍骨底，格 ＝ 0.1 m）：水線 24；甲板地板 艙底板 13、主甲板 34（船尾 39、船頭 36）、tolda 51、castillo 51；砲軸 z 40–41；迴旋砲軸 z 54–56（船腰舷牆頂）；桅樓 前 116／主 134、桅頂 前 175／主 203、後桅頂 117；外框 x 39–339 ⇒ `spar [34,53]`、`marines [21,89]`、`center 50`、`aim 34`、`aimZ [5,205]`、`deckAim [34,51]`、`rigAim [60,200]`；crew 照澤漢號、陸戰隊 8（約 25 名步兵〔估〕）；cfg.pump 2。
  🩸 import／ids 把整份 game.json 照 json.dump 重排 ⇒ 照 HEAD 原樣、只插回新船那一段（斷言其他船與其他鍵逐字相同）。
- 🩸 **匯入檢查第一輪 ✗ 2 → ✗ 3 → ✗ 2 → ✗ 0**（每一輪都回雕刻那側改，改完重匯）：
  1. castillo 底下（廚房那一塊）9.2 m² 接不到主幹、廚房四面都走不到：第 4 門砲（砲門 x 205–212）跟 castillo 梯子並排，船頭收窄 ⇒ 砲往裡伸到 |dy| 7.5、梯子側板 |dy| 4 ⇒ 中間 3 格，遊戲的走路格（42_hands.js：每 2 格一點、砲的外框外擴 1 格不能站）過不去 ⇒ 砲門收到 x 132–204（plan `ports.tiers` x_to 212 → 204；`draft_ports.py` 重產 ⇒ `tools/hull_expected.py` 組設計帳 ⇒ 標記 `砲門挪:begin／end` 之間 `delta_apply` 船殼刻 630、貼 630、換色 636；差只在 x 153–212、z 37–46，第 1 門沒動 ＝ 控制組）。
  2. 收完換成第 4 門跟主艙口圍欄（|dy| 7）與小艇架的柱並排 ⇒ castillo 整層接不到（✗ 甲板走不到）⇒ **拿掉主艙口**（plan `decks_build.hatches` 清空；下貨艙走艙底板梯子的井）；甲板-main `delta_apply` 刻 104、貼 221；小艇架的柱跟著落到甲板面。
     🩸 `draft_gear.py` 扣掉「自己現在的格」量柱要落到哪 ⇒ 柱插進甲板的 4 格也被當成空的、柱一路往下（link_overlap 4）⇒ 先 carvevox 那 4 格、再重產 ⇒ 624 格、link_overlap 0。
  3. tolda、castillo 的迴旋砲讓兩座船樓變成砲甲板、要有取用點（23_powder.js：從彈藥庫往船頭船尾找 9×9 平地，y 只試 |dy| 6–15、16–25 那幾條）—— 兩座船樓太窄 ⇒ ✗ 取用點 ×2；改用彈藥庫 `hoist`（三座梯子）⇒ castillo 那份桶擺在梯腳前面，正好堵住船腰唯一往船頭的走道（✗ 甲板走不到）、tolda 梯腳旁擺不下（✗ 取用點）⇒ **迴旋砲全部放船腰舷牆頂**（x 133、168、189、211；`work sub=unmodel` 拿掉船樓上那 6 門）、拿掉 hoist ⇒ 只有主甲板是砲甲板，取用點 1 個（彈藥庫上方）。
- 讀數：checksum 1043098078、格 115,930、模型 46、繩 122、帆 8；船卡 121 t、水線 21.4 m、16 門、齊射 22、船員 57；**匯入檢查 ✗ 0、⚠ 9**（直立的門 4 扇「打掉也不進水」—— 門洞在水線上；站不滿：送藥手 6／8、軍官 1／2、陸戰隊 7／8、桅頂水手 2／3；tolda 梯頂前 nav 擺的木工台）；火藥 16／16 門走得到取用點；廚房 1 座、廚師 1、站得住的面 4；操舵 100%；樓梯自檢 3 座 ✗ 0；甲板連通 4 層都接得到；超載極限 再多載 246 噸 ⇒ 舷牆頂（露天甲板）。srccheck 對得上、verify 1448 份網格逐個相同。
- **泊位反向對照**（Blocksail `BSW.fineBerthCls`，scratchpad 的 probe_patache.cjs，照 town.js BERTH_CLS 的 loa）：聖羅曼號全長 30.0 m（.vxk 外框 x 39–339）⇒ 小船那一級（loa ≤ 36、水深 5 m）；**停不進小艇那一級**（loa ≤ 12、水深 2.5 m —— 長度與吃水 2.4 ＋ 0.5 都卡）。對照組：拉貝爾號 22.4 m ⇒ 小船、澤漢號 42.3 m ⇒ 大船。

## 步驟 15 交船（2026-10-28）
照 Ship_Game §10 換一艘船時的檢查表逐條看過（遊戲那一份：`admin.py shipcheck --id sanroman` ✗ 0 ⚠ 9）：
- ✓ ropecheck 122 條 244 端 ok、沒有 bind／snap；組裝件名 ＝ 聖羅曼號、船殼帶 sub；mpv 0.1 每件都記（門板、爐灶、砲、火藥桶、帆桁等元件照它們自己的 0.05／0.02 m，模型明寫 scale）；開工前查過現有元件（新做的：4 磅砲通用部件 —— Tim「砲只有同型號共用模型」；船首喙、鍍金獅子、船尾拱形板、三角帆桁 —— 個性裝飾與本船尺寸的部件）。
- ✓ 砲 16（4l 8、pierrier 8）、帆桁 6、舵輪＋座、火藥桶 10、絞盤、羅經櫃、小艇、門 4、爐灶都是外部模型帶 kind；舵 kind=rudder＋stock-top；遊戲裡開局 `__game.lostModels(0)` ＝ []；spin：舵 ±35°、舵輪 540°；操舵鏈「舵令 ⇒ 甲板-tolda/舵輪 ⇒ 舵 100%」。
- ✓ 關聯 `船殼` kind=ship waterline_z 24（高度在步驟 14 那一段）；甲板 4 層 kind=deck、梯子 3 座 kind=ladders 四個固定點；樓梯自檢 3 座 ✗ 0、甲板連通都接得到；ratlines 橫繩組、下桅 4 組繩梯；三角帆桁 rig=lateen＋fore；彈藥庫 10 桶、16／16 門送藥走得到；窗的玻璃獨立關聯 material=glass（75 格）；廚房 kind=galley（不標 deco）、站得住的面 4、廚師 1。
- ✓ 繩與帆的端點綁 model:、ropes_broken／sails_broken／models_broken 0；帆 meta 8／8、帆自己的繩 17／17、帆桁 sail ＝ 帆名；帆裝三段表在步驟 8；組裝件 1 元件、空腔 0、link_overlap 0；vxk checksum 1043098078。
- 不適用：槳、撞角、蒸汽、鐵甲與金屬部件、砲塔、砲身與砲座拆兩件、砲門蓋板（露天甲板的砲，§9.12）、空艙房（沒隔艙）。
- ✓ **遊戲裡看過**（Blockside worktree 的成品 `index.html?ship=sanroman,falcon&debug=1`，本機靜態伺服器）：載得進來（115,930 格、checksum 跟封裝檔 header 相同、繩 122、帆 8＋陣營旗 3、桅 3）；按 S 一段一段 ⇒ 滿帆 6 面、戰鬥帆 3 面（兩面 topsail＋後桅三角帆）、收帆 2 面 topsail、全收 0 面；按 W 一段一段回到滿帆 —— 跟步驟 8 那張表一樣。截圖 `overlays/step15_ingame.jpg`。
  - 對打一場（`?demo=60&dump=1&seed=3&headless=1&ship=sanroman,falcon`，只跑一個種子、當讀數）：聖羅曼號開 70 發、被打中 49、桅 0 斷、航速 5.7 → 4.2 節；廚房 廚師 1／1、吃過飯 45 人、效率 ×1.098；夜隼號開 32 發。
- ⚠ 沒特別看的：窗玻璃的透明與反光（遠景截圖看不出來）—— 等 Tim 看那一格一起看。
- ⚠ 照實留著的匯入檢查 ⚠ 9：見步驟 14。

### todo（沒做的，照實留著）
- 砲具與砲索（環、breeching、tackle；Ship_Guns §4.4）。
- 主艙口（為了走道拿掉了）；露天的出入口沒有艙蓋（低乾舷：主甲板在水線上 0.9 m）。
- 錨鏈孔只登記固定點、沒開孔；後桅沒有桅樓（桅頂水手 2／3）。
- 遊戲那側：站不滿的那幾樣（送藥手 6／8、軍官 1／2、陸戰隊 7／8）照 crew 配置調；tolda 梯頂前 nav 擺的木工台。
