import os, sys, time, zipfile
root = os.path.expanduser("~/mnt/usrp-projects")
zpath = os.path.join(root, "backups", "usrp_data_backup_2026-10-02.zip")
budget, rate = float(sys.argv[1]) if len(sys.argv) > 1 else 140, 25e6   # bytes/s guess, refined below
t0 = time.time()
files = sorted(os.path.join(dp, f) for dp, _, fs in os.walk(os.path.join(root, "data")) for f in fs)
with zipfile.ZipFile(zpath, "a", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    have = set(z.namelist()); added = 0
    for p in files:
        arc = os.path.relpath(p, root)
        if arc in have: continue
        size = os.path.getsize(p)
        if time.time() - t0 + size / rate > budget: break
        s = time.time(); z.write(p, arc); dt = time.time() - s
        if size > 5e6 and dt > 0: rate = 0.7 * rate + 0.3 * (size / dt)
        added += 1
    left = sum(1 for p in files if os.path.relpath(p, root) not in set(z.namelist()))
print(f"added {added}, left {left}, rate {rate/1e6:.1f} MB/s, zip {os.path.getsize(zpath)/1e6:.0f} MB, {time.time()-t0:.0f} s")
