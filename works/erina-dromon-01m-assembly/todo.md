# 持火號 TODO

## 等 Tim
- [ ] 看預覽（overlays/final_*.png、design/sheet00_general.png）—— 造型、配色、武器擺法要不要改。

## 等遊戲那側（Blockside）
- [ ] 槳動力系統定規格 ⇒ 加槳：下層每舷 25（槳口記號在 x 78 + 10k、z 15–16，要開洞＋皮套）、上層每舷 25（甲板上划，槳栓在舷牆頂、錯半個位 x 83 + 10k）。
- [ ] 新彈種希臘火（`ammo=greekfire`）、武器種類（`weapon=`）⇒ 換掉 `gun=` 的頂替代碼；siphon 的噴嘴迴旋（strepton）做成只轉噴嘴。
- [ ] 正式匯入（admin.py import）、填 geo 與船員配置（三角帆船沒有桅頂水手的位置；陸戰隊站在舷牆內側與木塔、艏樓）、`cfg` 航速。
- [ ] 帆 meta 用 `sail=gaff` ＋ `rig=lateen`、帆桁 `yard=gaff`（遊戲當縱帆往下風擺）；要不要給 lateen 自己一種帆裝，由遊戲那側定。

## 可以再細修（不影響功能）
- [ ] 帆的紅色上角（Prokopios：從上角起約三分之一漆紅）—— 用帆的 texture。
- [ ] 艉部船長的帳篷（skēnē）、艏柱上方的鏈子（spur 的 katakorax）、舷牆掛盾（裝飾模型 deco=1）。
- [ ] 組裝件的預覽 preset（藏船殼看艙底、只看甲板）。
- [ ] 艙房標註（§9.2）：目前沒有隔出來的艙房。
