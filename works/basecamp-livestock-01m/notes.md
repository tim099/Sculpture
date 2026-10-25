畜牧建築（TASK-0926；Blocksail BUILDING_SPEC §6.22）：養雞場 henhouse 8 × 8、豬圈 pigsty 8 × 10、牧場 ranch 16 × 12，風格 common。
產生程式在 design/：python -I -X utf8 -B build.py . ⇒ apply.py . create|stamp|anchors|links|models|check（工具從 trailhead-harbour-01m、apex-one-industry-01m、meadow-farm-01m import）。
拆法：每一種一件成品（牆身 body ＋屋頂 roof ＋木板門窗的部件關聯 ＋燈籠）；配方一款配兩條（穀飼與否），不分變體。
穀飼看得出飼料：槽、料箱、豬食都是玉米 252 與大麥 177 混著，旁邊擺穀袋。
牲畜（TASK-0933，2026-10-25）：第一版雕在牆身的雞、豬、牛拿掉了；遊戲照固定點 pen-<物種>-<組><號>（兩點 ＝ 長方形對角、點 ＝ 動物中心走得到的地方）放 2D 點陣圖的動物。
  養雞場 pen-chicken-a～e、豬圈 pen-pig-a／b、牧場 pen-cow-a～c；量法：每組外擴半個身長、離地 1～h 格沒有實心格（豬圈第一版碰到石牆，收窄一格）。apply.py check 9 件缺 0 多 0 色差 0。
史料沒有上網查：雞舍的棲木與產卵箱、半露天的豬圈、牛欄的乾草架與料槽是照歐洲鄉間通法的設計。
牧場的牧草地（annex pasture）之後才做 ⇒ 牛欄後緣留一道門。
讀數（2026-10-25）：產生程式 框外 0、撞格 0、浮空 0、封閉空腔 0、door_ok；apply.py check 9 件缺 0 多 0 色差 0、link_overlap 0。
改過的：豬腳接在身體修圓的那一角 ⇒ 四頭豬浮空，腳挪到內側一格；尾巴放回屁股頂那一格。
