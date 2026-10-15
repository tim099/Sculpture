# 2026-10-15 潮墓號：遊戲匯入交付

Tim要求完成造船至可加入遊戲，並通知ame。作者側已補左右共用bower錨、短索與hawse，
錨後移2m避開艏砲班的模型外框。原船體1034323格/d931433f、十帆及固定帆點保留。
最終502繩/10帆/168模型，broken全0；結構1元件/0空腔/鏡像0/關聯重疊裁切0。

交付 D:\Unity\Valhalla\Sculpture\works\sirius-tidegrave-01m\design\delivery\tidegrave_import_20261015.vxk
SHA256 9d296dd5831602b831eaf00fc5fd1926b2d8f57487f3b053d361456a5019b367
0.1m格，水線52，54砲、6甲板、7梯、兩庫各24桶/2400lb。
重匯兩次除exported_at外內容相同；VXK/CLI逐格逐色0差，一格負向可失敗。
這不是所有歷史階段的乾淨初建重跑聲明。

隔離最新遊戲：0 errors / 2 warnings、54砲全滿編、352船員、左右錨/ring/hawse。
配套game_integration/23_powder.patch修艏艉砲送藥手誤生在甲板外的砲口X；舷砲不變。
suggested_ship.json提供geo。未改ame正式遊戲工作樹，需ame覆核採用、匯入及重建。
兩警告保留：陸戰隊11/12，chase-2送藥路徑尋路格不連通（現走直線）。

ame已接手帆物理並提交ebd55ff；TASK-0603/0546按Tim選擇維持手動動態驗收，
不把匯入成功當作穿帆全過。已知自由布接觸與凍結證據保留在design/task0603。
最新圖Rev08、overlays/import_bow_20261015.png；正式匯入說明design/delivery/IMPORT.md。
