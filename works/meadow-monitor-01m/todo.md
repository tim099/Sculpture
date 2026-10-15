# 莫尼特號 TODO
- [ ] 遊戲那側：砲種表加 11d（XI 吋 Dahlgren；建議 burst 2 讓兩根砲管都出彈）、DMG 鍵；ships[].cfg.base（6 kn）、geo。
- [ ] 遊戲那側若支援「圓筒跟著砲轉、砲各一個模型」：砲改掛 `-turret-gun` ×2（第二門 mirror=x），圓筒掛 `-turret-shell`。
- [ ] 有空再讀 NH 60660（砲塔橫剖面）量兩門砲的軸距與砲門高度，換掉 plan.json 的設計值。
- [ ] 艙房可以照 §9.2 標 kind=rooms（軍官艙 6 間、砲彈艙）。
- [ ] 旗（船尾 ensign）海戰時有沒有沒查到，先不做。
- 重做任何部件：改 plan.json → gen_monitor.py／gen_turret.py → apply_build.py <out> [部件] 只同步差的格 → apply_links／apply_models（同名覆寫）→ 重匯 vxk。
