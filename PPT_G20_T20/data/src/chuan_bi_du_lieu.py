"""Chuẩn bị dữ liệu (Đề 20): từ analysis_snapshot.csv tạo lưới f1, f2, f4 cho đoạn A, B."""
import csv
import statistics
from datetime import datetime

from mo_hinh import ROOT, data_dir, load_config, write_csv


# 1. Đọc một đoạn từ snapshot
def doc_doan(path, seg):
    # Lấy các ảnh có analysis_segment = seg, sắp theo thời gian; trả về danh sách dòng, t (phút), y (số xe)
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if r["analysis_segment"] == seg]
    for r in rows:
        r["ts"] = datetime.fromisoformat(r["timestamp"])       # chuỗi ISO 8601 -> thời điểm (có múi giờ)
    rows.sort(key=lambda r: r["ts"])                           # sắp theo thời gian tăng dần
    t0 = rows[0]["ts"]
    t = [(r["ts"] - t0).total_seconds() / 60.0 for r in rows]  # phút tính từ ảnh đầu
    y = [float(r["total_count"]) for r in rows]                # tổng số xe trong ảnh
    return rows, t, y


# 2. Kiểm tra dữ liệu theo quy định
def kiem_tra(rows, t, y, cfg):
    # Trả về danh sách (tên kiểm tra, giá trị, mức); mức ERROR là vi phạm, phải dừng
    kq = []
    n = len(t)
    dt = [(t[i + 1] - t[i]) * 60.0 for i in range(n - 1)]      # bước thời gian giữa 2 ảnh (giây)
    duong = [d for d in dt if d > 0]
    med = statistics.median(duong)                              # bước trung vị
    kq.append(("so_quan_sat", n, "OK" if cfg["min_obs"] <= n <= cfg["max_obs"] else "ERROR"))
    trung = sum(1 for d in dt if d <= 0)                        # hai ảnh cùng thời điểm
    kq.append(("trung_timestamp", trung, "OK" if trung == 0 else "ERROR"))
    kq.append(("buoc_min_s", round(min(dt), 3), "INFO"))
    kq.append(("buoc_trung_vi_s", round(med, 3), "INFO"))
    kq.append(("buoc_max_s", round(max(dt), 3), "INFO"))
    gap = sum(1 for d in dt if d > cfg["gap_factor"] * med)    # khoảng trống > 3 lần trung vị
    kq.append(("gap_lon_hon_%gx_trung_vi" % cfg["gap_factor"], gap, "OK" if gap == 0 else "ERROR"))
    rec = len(set(r["recording_id"] for r in rows))             # số lần ghi hình khác nhau
    kq.append(("so_recording", rec, "OK" if rec == 1 else "ERROR"))
    xau = sum(1 for v in y if not (v == v) or v < 0)            # y là NaN hoặc âm
    kq.append(("y_am_hoac_khong_huu_han", xau, "OK" if xau == 0 else "ERROR"))
    kq.append(("do_dai_doan_phut", round(t[-1], 4), "INFO"))
    nhan = ";".join(sorted(set(r["label_status"] for r in rows)))
    kq.append(("label_status", nhan, "OK" if nhan == "human_verified" else "WARN"))   # prelabel -> sơ bộ
    return kq


# 3. Làm thưa lưới: giữ mốc 0, f, 2f, ... và luôn giữ mốc cuối
def lam_thua(t, y, f):
    idx = list(range(0, len(t), f))
    if idx[-1] != len(t) - 1:
        idx.append(len(t) - 1)                                  # cùng hai đầu với lưới gốc
    return [t[i] for i in idx], [y[i] for i in idx]


def main():
    cfg = load_config()
    snap = ROOT / cfg["snapshot_path"]                          # data/analysis_snapshot.csv
    if not snap.exists():
        raise SystemExit("Khong thay %s. Chep shared/analysis_snapshot.csv vao thu muc data/." % snap)
    bao_cao, co_loi = [], False
    for seg in cfg["segments"]:
        rows, t, y = doc_doan(snap, seg)
        for ten, gt, muc in kiem_tra(rows, t, y, cfg):
            bao_cao.append((seg, ten, gt, muc))
            co_loi = co_loi or muc == "ERROR"
        with open(data_dir() / ("segment_%s.csv" % seg), "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)                                  # bảng đoạn: để tra lại ảnh nào, lúc nào
            w.writerow(["image_id", "timestamp", "t_min", "y_total_count", "label_status", "recording_id"])
            for r, ti, yi in zip(rows, t, y):
                w.writerow([r["image_id"], r["timestamp"], ti, yi, r["label_status"], r["recording_id"]])
        for f in cfg["thin_factors"]:                           # lưới f1 (gốc), f2, f4
            g, yg = lam_thua(t, y, f)
            with open(data_dir() / ("grid_%s_timestamps_f%d.csv" % (seg, f)), "w", newline="",
                      encoding="utf-8") as fh:
                w = csv.writer(fh)
                w.writerow(["t_min", "y"])
                w.writerows(zip(g, yg))
            bao_cao.append((seg, "luoi_f%d_so_moc" % f, len(g), "OK" if len(g) >= 2 else "ERROR"))
            bao_cao.append((seg, "luoi_f%d_dau_cuoi_phut" % f, "%.4f..%.4f" % (g[0], g[-1]), "INFO"))
    write_csv("data_validation.csv", ["segment", "check", "value", "level"], bao_cao)
    print("%-4s %-28s %-22s %s" % ("Doan", "Kiem tra", "Gia tri", "Muc"))
    for r in bao_cao:
        print("%-4s %-28s %-22s %s" % r)
    if co_loi:
        raise SystemExit("\nCO LOI (ERROR): xem results/data_validation.csv. Khong chay buoc sau.")
    print("\nDu lieu hop le. Da ghi data/segment_*.csv va data/grid_*_timestamps_f*.csv")
    print("LUU Y: nhan la prelabel -> moi ket qua la SO BO.")


if __name__ == "__main__":
    main()