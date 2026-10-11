# 重播作品 events/ 得到 voxel 表。
# replay(work_dir, upto=None)         —— 走 CLI（引擎重播：`senate cmd sculpture op=export format=list mark=<事件> links=none`）。
#                                        workedit（草稿 apply、undo、move…）與之後新加的 op 都由引擎認，這裡不必跟著補（TASK-0493，Tim 2026-10-11）。
# replay_witness(work_dir, upto=None) —— 純 Python，不經過引擎；跟引擎不同源的證人，對拍用（`python replay.py <作品資料夾>` 兩支逐格比）。
# upto：事件名（YYYY-MM-DD/HHMMSS_mmm_xxxxxx.json）—— 重播到它「之前」（不含它），兩支相同。
# 回傳 dict[(x,y,z)] = (color, 事件名)；CLI 版不知道每格是哪一刀放的 ⇒ 事件名是 None（呼叫端都只用顏色）。
import glob, json, os, subprocess, tempfile


def _events(work_dir):
    files = sorted(glob.glob(os.path.join(work_dir, 'events', '*', '*.json')))
    return [(os.path.basename(os.path.dirname(f)) + '/' + os.path.basename(f), f) for f in files]


def replay(work_dir, upto=None, senate='senate', draft=False, mark=None):
    """draft=True ⇒ 作品＋開著的草稿（`draft=1`，§9.4.3）；mark ⇒ 時間標記那一刻（例 '砲門:end'，§9.4.1）。三者只能給一個。"""
    if sum(1 for v in (upto, draft, mark) if v) > 1:
        raise SystemExit('replay：upto／draft／mark 只能給一個（引擎擋 draft＋mark）')
    if upto:
        keep = [n for n, _ in _events(work_dir) if n < upto]
        mark = keep[-1] if keep else 'start'          # mark=<事件> 含那一刀 ⇒ 給 upto 的前一個
    work = os.path.basename(os.path.normpath(work_dir))
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, 'world.txt').replace('\\', '/')
        args = [senate, 'cmd', 'sculpture', '--arg', 'op=export', '--arg', 'format=list', '--arg', 'work=' + work,
                '--arg', 'links=none', '--arg', 'out=' + out]
        if mark:
            args += ['--arg', 'mark=' + mark]
        if draft:
            args += ['--arg', 'draft=1']
        r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace')
        if r.returncode != 0 or not os.path.exists(out):
            msg = r.stdout + r.stderr
            if '不認得的參數' in msg or 'format' in msg and 'list' in msg and '只能是' in msg:
                raise SystemExit('CLI 重播失敗：PATH 上的 senate 太舊（讀不懂 export format=list／links／mark=事件檔，TASK-0492～0494）—— '
                                 '先在 Senate 跑 ./build.sh 出廠；要對拍可以先用 replay_witness()')
            raise SystemExit('CLI 重播失敗（exit %d）：%s' % (r.returncode, msg[-800:]))
        vox = {}
        for line in open(out, encoding='utf-8'):
            if line.startswith('#') or not line.strip():
                continue
            x, y, z, c = map(int, line.split(','))
            vox[(x, y, z)] = (c, None)
    return vox


def replay_witness(work_dir, upto=None):
    vox = {}
    for name, f in _events(work_dir):
        if upto and name >= upto:
            break
        e = json.load(open(f, encoding='utf-8'))
        op = e.get('op')
        if op == 'box':
            c = e.get('color')
            for v in e['placed_voxels']:
                vox[tuple(v[:3])] = (v[3] if len(v) > 3 else c, name)
        elif op == 'carve':
            for v in e['carved_voxels']:
                vox.pop(tuple(v[:3]), None)
        elif op in ('stampimg', 'stamp2d', 'stampvox', 'importwork'):
            for v in e['placed_colored']:
                vox[tuple(v[:3])] = (v[3], name)
        elif op == 'workedit':                          # 草稿 apply／undo／redo／move／assemble：照順序套 edit.after（color 0 ＝ 刪）
            for ch in e['edit']['after']:
                k = (ch['x'], ch['y'], ch['z'])
                if ch['color'] == 0:
                    vox.pop(k, None)
                else:
                    vox[k] = (ch['color'], name)
        else:
            raise SystemExit('未知 op %s @ %s' % (op, name))
    return vox


if __name__ == '__main__':
    import sys
    a = {k: v[0] for k, v in replay(sys.argv[1]).items()}
    b = {k: v[0] for k, v in replay_witness(sys.argv[1]).items()}
    diff = sum(1 for k in set(a) | set(b) if a.get(k) != b.get(k))
    print('cli', len(a), 'witness', len(b), 'diff', diff)
    sys.exit(0 if diff == 0 else 1)
