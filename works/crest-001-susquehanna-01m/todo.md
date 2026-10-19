# 蘇士奎哈納號 TODO（crest-001，TASK-0697）

- [ ] Tim 預覽（觀測頁 `crest-001-susquehanna-01m-assembly`）—— 看完說要改哪裡
- [ ] 匯進 Blockside 正式版（遊戲那側）：geo.spar [90, 104]、drive=steam、cfg.base 10；砲種 9d／11d 是借的（8 吋、10 吋 Paixhans 要不要新增由遊戲那側定）
- [ ] 小艇改掛船尾 quarter davits（照片、油畫）—— 要先確認遊戲吊艇的擺動不會撞船殼
- [ ] 明輪 meta：遊戲現在照 kind=propeller 轉；要不要另外一個 kind=paddle（畫面：槳板入水濺水花）由遊戲那側定
- [ ] 船頭兩門迴旋砲輪子著地 75% ⇒ 要不要補墊木
- [x] 砲門蓋板 4 片（TASK-0752，2026-10-20；`design/tools/portlids.py`）：S01／S02／P01／P02。
- [ ] 3 號砲門（兩舷）沒蓋板：後桅 channels（z 105–106、往外 12 格）貼在砲門上緣 ⇒ 要蓋就得把 channels 往上挪（連 chain plate、deadeye、繩一起動），Tim 要再做
- [x] 甲板陳設 6 件（TASK-0752；`design/draft_furnish.py`，引用拿破崙號 kotoko 的 fiferail／bitts／shotrack，deco=1）：三根桅腳圍欄、船頭繫纜柱、後艙口兩舷砲彈架。爐灶沒放（§9.13 是功能件）
- ⚠ 改任何部件 ⇒ 重匯 vxk（格數、checksum 會變），跟遊戲那側說
- ⚠ 船殼的帳：設計清單 ＝ mio.hull_now（masks/build − masks/masts/hull_carve − masks/guns/pivot_carve）；砲甲板、住艙甲板 ＝ masks/decks − masks/machinery/deck_*（機艙開的縫與梯子口）
