# 潮墓號接入候選（未改正式遊戲）

舊nav_candidate/42_hands.patch已過時；現行遊戲已有deck meta與navRegions。採用前逐檔核對source.json/crew_source.json的source SHA，這裡沒有覆寫ame的source或正式成品。

- 42_hands.patch：梯端按deckFloor(x)、近地高度與實際snap選層，保留區域圖；cache加deck.path；補砲按meta身份；舵手替補按實際站位選層。CLIMB_LIFT2→3對應本船已精刻的七梯淨空，其他船必須先回歸。
- 40_crew.patch：舵手出生以wheel本身XY/Z找支撐，不再站在舵輪下方甲板；保留standNear的14格頭空、模型與佔位檢查。

最終VXK a5994eee...，完整SHA見../delivery/manifest.json。`python -I -X utf8 ../test_game_fixture.py 10 deck`：兩艘各348船員/2舵手、54砲最低足額、7梯14端region可達、10秒GL0。強制兩舵手傷亡後，再用真正stepHand、60Hz及每幀HAND_PATHS額度，35.133秒兩人到quarter z139、轉ROLE.HELM。這段probe凍結世界戰鬥，沒有宣稱額外35秒整世界對戰。

限制：1.8m×0.7m指定爬升截面不等於2.1m人物sprite/pose全包絡；navSnap接近與離開段沒全幾何掃；游泳登船、無梯home、多處不同層舵手等通用路徑仍待。模型感知索具另有舊穿透與ratline誤綁，見../CONTINUED_20261014.md。這不是全船正式簽收。
