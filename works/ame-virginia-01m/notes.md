
## 換砲：Dahlgren、Brooke 換成自己的模型（ridge-two，TASK-1155，2026-11-01）

- Tim 2026-11-01：「排查一下目前船有哪些炮是用其他炮暫代的 然後替換成對應的炮」（Ship_Guns §2.2 砲只跟同一種砲共用模型）⇒ 9d ×6 → IX 吋 Dahlgren `ridge-two-centurion-01m-gun-dahlgren9`、64b ×2 → 6.4 吋 Brooke `-gun-brooke64`、7b ×2 → 7 吋 Brooke `-gun-brooke7`（以前都拿餘燼號 32 磅 ×0.55／×0.6）。`design/apply_models.py` 跟著改成新的 work、at、pivot。
- 擺法（ridge-two-centurion-01m/design/place1155.py）：沿舊砲的砲軸、新砲口對到舊砲口 ⇒ 10 門都不用退、零碰撞（9 吋砲口低 1.12 格、6.4 吋高 0.38）；船頭船尾迴旋砲轉軸中心照舊（砲廓圓頭的圓心）⇒ meta pivot −9.5／−10.5 ⇒ −9.2／−10.2，runin 6 照舊；三個砲門角度＋換砲門那段都量 0。
- 7 吋的滑軌拆成砲座：雙生「砲-船頭座／砲-船尾座」kind=gunmount、`mount_of` gun-9／10、id gunmount-1／2。
