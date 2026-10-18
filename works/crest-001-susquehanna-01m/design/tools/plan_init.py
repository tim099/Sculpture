# 蘇士奎哈納號（crest-001，TASK-0697）：plan.json 第一版 —— 從光榮號的 plan.json（抄過來的那份）換掉線形、主尺寸、甲板、塗裝這幾段（階段一要用的）。
#   其他段（桅、砲、帆…）先留著光榮號的值，到那一階段再換；換過的段 src 開頭寫「蘇士奎哈納號：」。
#   用法：python -I -X utf8 tools/plan_init.py <design>（只在第一次用；之後改 plan.json 用文字插入，⛔ 不整份重寫）
import os, sys, json
sys.path.insert(0, os.path.abspath(sys.argv[1]))
import plan_io

design = os.path.abspath(sys.argv[1])
P = plan_io.load(design)
P['title'] = '蘇士奎哈納號（USS Susquehanna，1850）新圖紙 01：線形、側面、甲板高度、明輪、帆裝、砲位'
P['task'] = 'TASK-0697'
P['author'] = 'crest-001'
P['date'] = '2026-10-18'
P['space'] = {'x': 1300, 'y': 400, 'z': 800, 'yc': 200, 'note': '中線 ＝ 第 200 格（鏡像 y ↔ 400 − y）'}
P['refs'] = {
    'RES': 'references/susquehanna_research_2026-10-18.md（crest-001 派的研究 agent，2026-10-18；每個數字附網址與 opened／snippet／LOW）',
    'STUART': 'C. B. Stuart, The Naval and Mail Steamers of the United States（1853）pp. 83–85、附錄 Note G（Powhatan／Susquehanna 建造規範）—— archive.org navalmailsteamer00stuauoft（opened）',
    'BARTOL': 'B. H. Bartol, A Treatise on the Marine Boilers of the United States（1851）p. 2 —— archive.org 0160TREA（opened）',
    'PLATE05': 'Stuart 1853 書中的 Powhatan（姊妹艦，同一份規範）側面石版畫 —— references/05_*.jpg；主要拿來量位置（桅、明輪、煙囪）',
    'JP1853': '1853-07-08 日本畫師的右舷圖（LoC 2006677644）—— references/01_*.jpg',
    'PHOTO': 'Gutekunst 1860 年代照片（唯一的照片，左舷）—— references/02_*.jpg',
    'SIMONE': 'de Simone 1857 那不勒斯油畫（NHHC NH 1310-KN）—— references/03_*.jpg',
    'GLOIRE': '光榮號（kaguya-gloire-01m，TASK-0622）—— 管線整套抄過來（同樣約 78 m 的蒸汽巡防艦）',
    'NAP': '拿破崙號（kotoko-napoleon-01m）—— 機艙（主機、鍋爐、軸）的做法'
}
L = P['lines']
L['half_beam'] = {'v': 68.5, 'src': 'STUART／BARTOL：寬 45 ft（13.7 m）⇒ 半寬 68.5 ⇒ 137 格（格數只能奇數）'}
L['keel_top'] = {'v': 5, 'src': 'STUART：龍骨深 1 ft 6 in（0.46 m）⇒ 5 格'}
L['keel_half'] = {'v': 2, 'src': '設計決定：龍骨寬 5 格'}
L['max_breadth_z'] = {'v': 62, 'src': '設計決定：最寬處在水線上一點（木殼巡防艦）'}
L['tumblehome'] = {'v': 4, 'src': '設計決定：PLATE05／PHOTO 舷側幾乎直、舷牆微微內收 ⇒ 每舷 0.4 m'}
L['tumblehome_ref_z'] = {'v': 110, 'src': '設計決定：舷牆頂'}
L['tumblehome_pow'] = {'v': 1.6, 'src': '設計決定（同光榮號）'}
L['bilge_pow'] = {'v': 2.4, 'src': '設計決定：調飽滿度讓水線 z 56 以下排水量對上約 3,550 t（STUART：17½ ft 3,277 t、19½ ft 3,824 t ⇒ 18½ ft 內插 3,550 t）'}
L['s_aft'] = {'v': 0.3, 'src': '設計決定（調排水量）'}
L['s_fwd'] = {'v': 0.62, 'src': '設計決定（調排水量）'}
L['sternpost_x0'] = {'v': 150, 'src': '倒推：水線 z 56 的長度 ＝ 762 格（STUART：吃水 18½ ft 時長 250 ft ＝ 76.2 m）'}
L['sternpost_rake_deg'] = {'v': 4, 'src': '設計決定：明輪船沒有螺旋槳框 ⇒ 艉柱照帆船微微往後倒'}
L['wing_transom_z'] = {'v': 66, 'src': '設計決定：counter 從住艙甲板那一層開始往後挑'}
L['counter_aft'] = {'v': 12, 'src': '設計決定：PHOTO 船尾是圓／橢圓的 counter，往後挑約 1.2 m'}
L['counter_top_z'] = {'v': 88, 'src': '設計決定：counter 頂 ＝ 砲甲板'}
L['stern_rake_deg'] = {'v': 14, 'src': '設計決定：PLATE05 船尾面往後倒'}
L['transom_ratio'] = {'v': 0.2, 'src': '設計決定：PHOTO 圓船尾 ⇒ 不留寬的 transom'}
L['forefoot_x'] = {'v': 880.0, 'src': '倒推：水線 z 56 的長度 762 格；艏柱頂落在甲板長 256.5 ft（BARTOL：on deck 256 ft 6 in）附近'}
L['forefoot_r'] = {'v': 34, 'src': '設計決定：圓 forefoot'}
L['stem_rake_deg'] = {'v': 12, 'src': '設計決定：PLATE05／PHOTO 艏柱往前傾（接 cutwater 與船首像）'}
L['deadwood_aft_z'] = {'v': 40, 'src': '設計決定：帆船式的船尾 deadwood（沒有螺旋槳框）'}
L['deadwood_fwd_z'] = {'v': 18, 'src': '設計決定'}
L['bow_pow_low'] = {'v': 1.6, 'src': '設計決定：入水線收細'}
L['bow_pow_high'] = {'v': 2.3, 'src': '設計決定：上半船頭飽滿一點（接 head 與吊錨架）'}
L['aft_pow'] = {'v': 2.0, 'src': '設計決定'}
L['round_stern'] = {'r': 55, 'z0': 60, 'z1': 84, 'src': 'PHOTO：圓／橢圓船尾 ⇒ 水線以上俯視收成半徑 5.5 m 的圓弧（設計決定）'}
L['top'] = [[128, 116], [300, 111], [500, 109], [700, 111], [930, 121]]
P['top_src'] = '設計決定：舷牆頂 ＝ 砲甲板（露天甲板）＋ 20 格（2.0 m；STUART Note G 的 plank sheer 2 ft 再加上放得下砲門的舷牆與 hammock rail），照甲板舷弧兩頭抬'
P['waterline'] = {'z': 56, 'src': 'BARTOL：平均吃水 18 ft 6 in（STUART service draft 18½ ft；DANFS 20 ft 6 in 應是滿載）⇒ 5.64 m ⇒ z 56（遊戲只吃一條水線 ⇒ 平龍骨）'}
P['targets'] = {
    'displacement_t': {'v': 3550, 'src': 'STUART p. 83：15½ ft 2,745 t、17½ ft 3,277 t、19½ ft 3,824 t ⇒ 18½ ft 內插約 3,550 t（2,450 t 是 burthen 噸位、不是排水量）'},
    'length_wl_m': {'v': 76.2, 'src': 'STUART：吃水 18½ ft 時長 250 ft'},
    'length_deck_m': {'v': 78.2, 'src': 'BARTOL：on deck 256 ft 6 in（STUART custom house 257 ft）'}
}
P['readings_at'] = {'lower_deck_z': 56, 'deck_len_target': 762, 'note': '長度在水線量（STUART 給的是吃水 18½ ft 的長）'}
P['hull_build'] = {'wall': 4, 'frame_color': 141, 'inner_color': 177, 'side_color': 36, 'bottom_color': 168, 'bottom_top_z': 54,
                   'src': '設計決定：木殼牆 4 格（外板 1、肋骨 2、內板 1，同三叉戟號）；水線下包銅 168 到 z 54、以上黑 36（黑船：SIMONE 整片深色、JP1853 黑殼）'}
P.pop('aperture', None)
P['body_stations'] = [160, 200, 260, 350, 450, 550, 650, 750, 820, 860, 890]
P['decks'] = {
    'src': 'STUART Note G：orlop、berth deck、gun deck（gun deck 就是露天甲板，舷牆直接蓋在上面）；berth deck 板頂到 gun deck 樑底 6 ft 9 in、berth deck 樑頂到 orlop 板 5 ft 2 in ⇒ 砲甲板 z 89（離水線 3.3 m：艙深 26 ft 6 in ＋ 龍骨 − 吃水）、住艙甲板 z 65、底艙 z 45',
    'sheer': {'x_mid': 520, 'x_aft': 150, 'x_fwd': 900, 'aft': 6, 'fwd': 12, 'src': '設計決定：PLATE05／SIMONE 舷弧平緩 ⇒ 船尾抬 0.6 m、船頭 1.2 m'},
    'rows': [
        {'key': 'orlop', 'name': '底艙（orlop）', 'z': 45, 'x_from': 175, 'x_to': 860, 'skip': [[400, 640]],
         'skip_src': '設計決定：機艙（四座鍋爐、兩具斜置主機、明輪軸底下）不鋪 orlop'},
        {'key': 'berth', 'name': '住艙甲板（berth deck）', 'z': 65, 'skip': [[430, 520]],
         'skip_src': '設計決定：斜置主機的汽缸與連桿往上接到明輪軸（z 87）⇒ 主機那一段不鋪'},
        {'key': 'gun', 'name': '砲甲板（gun deck，露天）', 'z': 89}
    ]
}
P['paint'] = {'base': 36, 'band': 255, 'bottom': 168, 'gold': 36, 'glass': 87, 'banded': [], 'band_overrun': 0,
              'src': 'SIMONE（1857，本船）整片深色、沒有帶；JP1853 黑殼；PLATE05（姊妹艦 Powhatan）有一條淺色細帶 ⇒ 設計決定：照本船的圖，不畫帶；舷牆頂的白是 hammock 帆布（之後的部件）'}
plan_io.save(design, P)
print('ok', sorted(P.keys()))
