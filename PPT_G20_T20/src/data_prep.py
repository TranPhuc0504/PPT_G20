"""Chuan bi du lieu cho De tai 20 (Mang 1 - Du lieu).

Lam gi:
  1. Doc data/analysis_snapshot.csv (copy tu shared/analysis_snapshot.csv, KHONG tu dem tu anh).
  2. Voi moi doan A/B: sap xep theo thoi gian, kiem tra trung, gap > 3 lan trung vi,
     so quan sat 80-300, cung recording, y >= 0.
  3. Doi thoi gian ra PHUT tu moc dau (giu nguyen giay that cua ISO 8601).
  4. Tao LUOI GOC (f1) theo 2 bien the: regular30s (luoi deu 30 s, noi suy tuyen tinh) va
     timestamps (cac moc that). Roi LAM THUA moi 2/4 moc (f2, f4) bang cach GIU tap con cua luoi
     goc, cung hai dau, y khong tinh lai (Buoc 5 cua de tai 20).
Dau ra: data/segment_X.csv, data/grid_X_<regular30s|timestamps>_f{1,2,4}.csv,
        results/data_validation.csv
"""
import csv

import numpy as np
import pandas as pd

from common import DTYPE, data_dir, load_config, results_dir


def load_segment(df, name):
    s = df[df["analysis_segment"] == name].copy()
    s["ts"] = pd.to_datetime(s["timestamp"], utc=True)
    s = s.sort_values("ts").reset_index(drop=True)
    t = ((s["ts"] - s["ts"].iloc[0]).dt.total_seconds().to_numpy(dtype=DTYPE)) / 60.0
    y = s["total_count"].to_numpy(dtype=DTYPE)
    return s, t, y


def validate(s, t, y, cfg, name):
    """Tra ve danh sach (kiem_tra, ket_qua, muc_do). muc_do ERROR neu vi pham quy dinh."""
    rows = []
    n = len(s)
    dt = np.diff(t) * 60.0  # giay
    med = float(np.median(dt[dt > 0])) if (dt > 0).any() else float("nan")
    rows.append(("so_quan_sat", n, "OK" if cfg["min_obs"] <= n <= cfg["max_obs"] else "ERROR"))
    rows.append(("trung_timestamp", int((dt <= 0).sum()), "OK" if (dt > 0).all() else "ERROR"))
    rows.append(("buoc_min_s", round(float(dt.min()), 3), "INFO"))
    rows.append(("buoc_trung_vi_s", round(med, 3), "INFO"))
    rows.append(("buoc_max_s", round(float(dt.max()), 3), "INFO"))
    big = int((dt > cfg["gap_factor"] * med).sum())
    rows.append(("gap_lon_hon_%gx_trung_vi" % cfg["gap_factor"], big, "OK" if big == 0 else "ERROR"))
    rows.append(("so_recording", s["recording_id"].nunique(), "OK" if s["recording_id"].nunique() == 1 else "ERROR"))
    rows.append(("y_am_hoac_khong_huu_han", int((~np.isfinite(y) | (y < 0)).sum()),
                 "OK" if np.isfinite(y).all() and (y >= 0).all() else "ERROR"))
    rows.append(("do_dai_doan_phut", round(float(t[-1]), 4), "INFO"))
    rows.append(("label_status", ";".join(sorted(s["label_status"].unique())),
                 "WARN" if (s["label_status"] != "human_verified").any() else "OK"))
    return rows


def base_grid(t, y, kind, h0_min):
    """Luoi GOC (f1).
    - regular30s: luoi deu buoc h0 tu t[0], ket thuc o moc h0 cuoi con trong mien
      (Quy dinh 2.3 muc 4), y noi suy tuyen tinh tung doan; KHONG them diem cuoi, KHONG ngoai suy.
    - timestamps: chinh cac timestamp that cua doan (de tai 20 cho phep thoi gian khong deu).
    """
    if kind == "timestamps":
        return t.copy(), y.copy()
    k = int(np.floor((t[-1] - t[0]) / h0_min + 1e-12))
    g = t[0] + h0_min * np.arange(k + 1, dtype=DTYPE)
    return g, np.interp(g, t, y)


def thin_grid(g, yg, factor):
    """Lam thua 'moi factor moc' cua luoi goc: giu moc 0, factor, 2*factor, ...
    Gia tri y GIU NGUYEN (khong tinh lai). Luon giu moc cuoi cua luoi goc de CUNG HAI DAU."""
    idx = np.arange(0, len(g), factor)
    if idx[-1] != len(g) - 1:
        idx = np.append(idx, len(g) - 1)
    return g[idx], yg[idx]


def main():
    cfg = load_config()
    snap = data_dir().parent / cfg["snapshot_path"]
    if not snap.exists():
        raise SystemExit("Khong thay %s. Chep shared/analysis_snapshot.csv vao thu muc data/." % snap)
    df = pd.read_csv(snap, encoding="utf-8-sig")
    h0 = cfg["h0_seconds"] / 60.0
    report = []
    any_error = False

    for name in cfg["segments"]:
        s, t, y = load_segment(df, name)
        for chk, val, lvl in validate(s, t, y, cfg, name):
            report.append((name, chk, val, lvl))
            any_error |= lvl == "ERROR"
        out = pd.DataFrame({"image_id": s["image_id"], "timestamp": s["timestamp"],
                            "t_min": t, "y_total_count": y,
                            "label_status": s["label_status"], "recording_id": s["recording_id"]})
        out.to_csv(data_dir() / ("segment_%s.csv" % name), index=False)
        for kind in cfg["base_grids"]:
            g0, y0 = base_grid(t, y, kind, h0)
            for f in cfg["thin_factors"]:
                g, yg = thin_grid(g0, y0, f)
                pd.DataFrame({"t_min": g, "y": yg}).to_csv(
                    data_dir() / ("grid_%s_%s_f%d.csv" % (name, kind, f)), index=False)
                tag = "%s_f%d" % (kind, f)
                report.append((name, "luoi_%s_so_moc" % tag, len(g), "OK" if len(g) >= 2 else "ERROR"))
                report.append((name, "luoi_%s_dau_cuoi_phut" % tag,
                               "%.4f..%.4f" % (g[0], g[-1]), "INFO"))
            if kind == "regular30s":
                n0 = len(g0)
                report.append((name, "luoi_regular30s_du_80_moc", n0, "OK" if n0 >= 80 else "WARN"))

    with open(results_dir() / "data_validation.csv", "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(["segment", "check", "value", "level"])
        w.writerows(report)

    print("%-3s %-34s %-22s %s" % ("Doan", "Kiem tra", "Gia tri", "Muc"))
    for r in report:
        print("%-3s %-34s %-22s %s" % r)
    if any_error:
        raise SystemExit("\nCO LOI (ERROR): xem results/data_validation.csv. Khong chay buoc sau.")
    print("\nDu lieu hop le. Da ghi data/segment_*.csv, data/grid_*_<luoi>_f*.csv")
    print("LUU Y: nhan hien tai la prelabel chua nghiem thu -> moi ket qua phai ghi la SO BO.")


if __name__ == "__main__":
    main()
