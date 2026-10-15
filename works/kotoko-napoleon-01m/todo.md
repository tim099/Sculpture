# 拿破崙號 TODO

## 下一步：階段八 砲（TASK-0613）
- 每舷：下砲甲板 18（30 磅 No.1 ⇒ 沿用 `basecamp-ember-01m-gun-long32`，32l）、上砲甲板 15（30 磅 No.2 ⇒ `basecamp-frigate-constitution-01m-gun-24`，24l）、上甲板 12（16 cm 砲 ⇒ `summit-stormkaap-01m-gun-12l`／carronade ⇒ `basecamp-frigate-constitution-01m-gun-carronade32`）。
- 結構參考三叉戟號 `draft_guns.py`、`tools/apply_guns.py`：每個砲門從舷牆外往裡退到零碰撞、砲口在船殼外；P 舷 mirror=y 或 rotate 180。
- ⚠ 上甲板的砲不能撞 channels（channels 在上甲板 ＋ 17，砲門在 ＋ 7..＋ 15）、不能撞煙囪、梯子、艙口圍欄。

## 之後
- 階段九～十：彈藥庫、舵、甲板物件、匯進遊戲。
- ⚠ faux-pont 的 floor meta 中間是機艙（沒有地板）—— 跟 ame 對。
- ⚠ 煙囪、螺旋槳在遊戲裡怎麼處理 —— 跟 ame 對（TASK-0615）。
- 船尾四分之一的白帶零碎，可以之後細修。
