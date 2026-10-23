# 松島號 TODO

## 交船前（遊戲那側）
- [x] **合進 Blockside dev、推上測試站**（Tim 2026-10-21「先合併到dev吧」）：dev df97a68（砲種表 f838c8a、上船 d5c3923）；共用 `_cache` 補了 matsushima.vxk；worktree 與分支已刪；Blocksail 1323923 記到 df97a68（Blocksail 還沒推）。
- [x] 砲種表加四種 —— 分支 `ridge-001/matsushima-guns`，**已提交 `f838c8a`**（Refs TASK-0780）：`canet320`（`320c`：V 290、裝填 4.0、big、hole 2.2、砲班 8／5、66 t、450 kg、hpK 1）、`armstrong120`（`120a`：V 275、裝填 0.5、hole 1.0、6／3、2.1 t、20.4 kg）、`hotch57`（`h57`：V 235、0.35、0.55、3／2、0.37 t、2.72 kg）、`hotch47`（`h47`：V 230、0.3、0.45、2／1、0.24 t、1.5 kg）；每發傷害 dmg320c 920（上限 1200）、dmg120a 160、dmgh57 40、dmgh47 30（照「傷害 ∝ 彈重^0.57」）。初速照 trailhead 的換算（約 0.42 × m/s）、裝填與砲班是設計決定。對拍三組逐位元組相同。
- [x] 正式匯入遊戲（2026-10-21 晚上，在分支上）：`admin.py import`、`ids`、`parts`；cfg base 15、geo、防護甲板改 iron_hull ⇒ 浮在設計水線；匯入檢查 ✗ 0 ⚠ 3（notes.md「上船」）。
- [x] 匯入檢查「火藥」那一行：23／27 門走得到取用點；沒走到的 4 門是兩層桅樓的 47 mm（走路格量不到、照直線送）。
- [ ] ⚠ 剩 2 條：送藥手 12／13 站得下；露砲台的梯子上端落在轉盤（尋路不收 ⇒ 預備水手、傷員不走，第一人稱照樣爬）。（「找不到桅」已解：信號桁改帆桁模型）
- [x] 混合材質（dev b8178db）：船殼 `iron*0.15`（金屬外觀）、防護甲板 `iron*0.28`（取代被拿掉的 iron_hull）；`mass.py` 認混合寫法。
- [x] 桅與其他鋼構（Tim「是否能標記桅杆…如果是金屬的話也改一下材質吧」）：信號桁兩根改帆桁模型（引用定遠號 yard-main 縮放、上白色；meta yard=signal、mast=main）⇒ 遊戲認得桅；桅、上層建築 `iron*0.1`，通風筒 `iron*0.05`，露砲台撐柱 `iron*0.2`（平滑金屬）；艙壁、欄杆、梯子 `iron*0.1`～`0.2`＋render=voxel（1 格細）。
- [ ] 主機、鍋爐是 ame 換成的自帶格子模型（TASK-0793，Blockside c0f6e70）—— apply_links.py 還是寫成關聯，重跑之前先照 ame 的寫法改（不然會把它們換回關聯）。
- [ ] 雕刻預覽（Senate SCP_SculptSmooth）不認混合寫法 ⇒ 雕刻那邊看不到金屬（要修得動 Senate）。

- [x] 樓梯自檢（TASK-0838；Tim 2026-10-23「甲板下的樓梯都有偏移現象(有個洞) 且還有樓梯口被堵死」）：艙口改照 §9.3 開（gen_matsushima.py `ladder()`）⇒ ✗ 11 → 1；四層甲板重同步。在 Blockside 分支 `ridge-001/matsushima-ladders`（還沒提交、沒合 dev）。
- [x] 樓梯自檢剩 `barbette` ✗ 1 —— 照留（Tim 2026-10-23「保留吧」）：轉盤正中間的彈藥井，人本來就上不去；史料見 notes「樓梯自檢與梯口」。
- [x] 砲罩後門的繩梯（Tim「其實可以用繩梯(可以跟著轉)」）：綁在主砲塔上、轉 ±140° 不撞；尋路不走（轉盤那圈是牆），第一人稱爬得上。
- [x] 揚弾筒（TASK-0841）：子作品 -hoist＋關聯 meta kind=hoist、bottom／top；露砲台圈開門；彈藥庫-後 hoist 只剩 mu-aft。測試 worktree 匯入檢查 ✗ 0 ⚠ 10。
- [x] 揚弾機那邊修好「整船框 ⇒ 揚弾筒血量讀成整艘船」之後重匯、`admin.py ids`（Blockside dev 3816f29；揚弾筒 id hoist-1）。
- [ ] 樓梯自檢的 ⚠ 4：取用點的火藥桶擋在 lm-fwd／mu-fwd／uf-fwd／bridge-S 梯腳正前方 —— 遊戲那側擺桶（23_powder.js），雕刻不用改。
- [x] 裝飾（Tim 2026-10-23「然後加上裝飾吧(參考 拿破崙號)」）：菊花紋章、錨鏈繫纜柱（引用拿破崙號）、雙柱繫纜樁 ×6、12 cm 備便彈架 ×8，全部 deco=1（draft_furnish.py／apply_furnish.py）。

## 之後可以細修
- [x] 12 cm 砲列的砲門蓋板（§9.12）：自己一件窄高的 `-portlid` 9 × 14 × 2，中甲板 10 片（design/tools/portlids.py；匯入檢查 ✗ 0）。
- [x] 突出砲台 57 mm 的 4 個射口：不做蓋板（Tim「由妳判斷」；理由見 notes「12 cm 砲門蓋板」），照實留成進水口。
- [ ] 請 calli 再量一次砲列的房間／進水（有蓋板的砲口照 TASK-0822 隔水，打壞才進水）。
- [ ] 露天的艙口加門（§9.7）：船首樓後壁兩扇、後甲板 mu-aft 的艙口
- [ ] 魚雷網桿（照片沿水線一排長桿）、雨篷架（後甲板）
- [x] 艏的菊花紋章（照片 P1896 船首看得到）—— 2026-10-23 裝飾那一批
- [x] 艙房（§9.2，`kind=rooms`；Tim「接著參考憲法號 根據圖紙加上內部艙室吧」）：gen_rooms.py ＋ apply_rooms.py；每舷 防護甲板上 12、中甲板 8、船首樓底下 4 ⇒ 48 間，rooms.py check 全過。
- [x] 繩梯（Tim「參考憲法號 加上上桅杆的繩梯」）：兩舷 shroud-a ↔ shroud-b 每 4 格一道、climb（船首樓甲板 ⇒ 下桅樓），各 35 道。
- [ ] 火藥送不到桅樓那 4 門 47 mm 照舊（送藥手的路不走繩梯）。
- [x] ~~對拍：加了艙房之後 dingyuan,constitution 變了~~ —— 不是艙房：合 dev c56c52d、照共用 _cache 補齊重匯之後四組都跟 dev 逐位元組相同（2d1ad37293）；那時 worktree 抄來的 _cache 裡定遠號比 dev 的成品新。
- [ ] 廚房（§9.13）
- [ ] 桅頂的將旗（伊東祐亨中將旗）
