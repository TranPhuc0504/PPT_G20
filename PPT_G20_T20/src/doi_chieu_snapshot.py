"""Sai số dữ liệu (Đề 20, việc dòng 24 bảng tiến độ): đối chiếu snapshot BAN ĐẦU với snapshot SAU NGHIỆM THU.

Chạy từ thư mục gốc:
  python src\\doi_chieu_snapshot.py               -> dùng 2 đường dẫn trong config.json (xem dưới)
  python src\\doi_chieu_snapshot.py --tu-kiem     -> so snapshot ban đầu với CHÍNH NÓ (phải lệch 0), không ghi file
main.py gọi file này ở mọi lần chạy: CHƯA có snapshot nghiệm thu thì chỉ báo "bỏ qua", không ghi gì.

Đường dẫn (config.json, khóa "doi_chieu_snapshot"; thiếu khóa thì dùng mặc định):
  "ban_dau":    snapshot nhãn ban đầu (prelabel)    mặc định = "snapshot_path" trong config
  "nghiem_thu": snapshot sau nghiệm thu (human)      mặc định = data/analysis_snapshot_nghiem_thu.csv

Cách làm:
  1. Ghép hai snapshot theo image_id. Ảnh có ở cả hai bản: so số xe (tổng và từng lớp).
     Ảnh chỉ có ở một bản: không so, chỉ liệt kê.
  2. Sai số đếm theo ảnh: Δ = số xe (nghiệm thu) − số xe (ban đầu); MAE, RMSE, E∞ theo đoạn A, B.
  3. Ảnh hưởng lên T: GIỮ NGUYÊN mốc thời gian của đoạn A/B ban đầu, chỉ thay số xe của ảnh ghép được
     bằng số nghiệm thu, rồi chạy lại đúng code tự viết (cumulative, bisect). Nhờ giữ lưới, ΔT chỉ do nhãn.
  4. Đặt cạnh 2 nguồn sai số còn lại: dung sai thuật toán (cận tol/2) và lấy mẫu (làm thưa f2, f4).

Ghi (chỉ khi có snapshot nghiệm thu): results/data_error_images.csv, data_error_summary.csv,
data_error_T.csv, data_error_sources.csv
"""
import argparse
import csv
import sys

import numpy as np

from chuan_bi_du_lieu import doc_doan
from mo_hinh import (DTYPE, ROOT, bisect, check_grid, cumulative, khao_sat_lam_thua, load_config, metrics,
                     q_levels, write_csv)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

LOP = [("total_count", "Tổng số xe"), ("count_2wheel", "Xe 2 bánh"), ("count_car", "Ô tô con"),
       ("count_bus", "Xe buýt"), ("count_truck", "Xe tải")]
MAC_DINH_NGHIEM_THU = "data/analysis_snapshot_nghiem_thu.csv"


# ==== Phần 1: đọc và ghép hai snapshot ====

def duong_dan(cfg):
    d = cfg.get("doi_chieu_snapshot", {})
    return ROOT / d.get("ban_dau", cfg["snapshot_path"]), ROOT / d.get("nghiem_thu", MAC_DINH_NGHIEM_THU)


def doc_snapshot(path):
    # Trả về {image_id: dòng}; kiểm cột bắt buộc và số xe hợp lệ (số, không âm)
    with open(path, encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        sys.exit("%s: file rỗng." % path.name)
    for cot in ("image_id", "total_count"):
        if cot not in rows[0]:
            sys.exit("%s: thiếu cột %s." % (path.name, cot))
    kq = {}
    for i, r in enumerate(rows, 2):
        if r["image_id"] in kq:
            sys.exit("%s dòng %d: image_id bị trùng (%s)." % (path.name, i, r["image_id"]))
        for cot, _ in LOP:
            if cot in r and r[cot] != "":
                try:
                    v = float(r[cot])
                except ValueError:
                    sys.exit("%s dòng %d: %s = '%s' không phải số." % (path.name, i, cot, r[cot]))
                if not v >= 0:
                    sys.exit("%s dòng %d: %s = %s âm hoặc trống." % (path.name, i, cot, r[cot]))
        kq[r["image_id"]] = r
    return kq


def so_xe(r, cot):
    # Số xe của một lớp; lớp không có cột hoặc ô trống -> None (không so lớp đó)
    v = r.get(cot, "")
    return None if v == "" else float(v)


# ==== Phần 2: sai số đếm theo từng ảnh ====

def sai_so_anh(cfg, truoc, sau, p_truoc):
    anh, theo_doan = [], {}
    trong_doan = set()
    for seg in cfg["segments"]:
        rows, t, _ = doc_doan(p_truoc, seg)                  # cùng cách sắp/đổi phút như chuan_bi_du_lieu
        theo_doan[seg] = []
        for r, ti in zip(rows, t):
            iid = r["image_id"]
            trong_doan.add(iid)
            if iid not in sau:
                anh.append([seg, iid, r["timestamp"], "%.4f" % ti, "chỉ có ở bản ban đầu", "",
                            "%g" % so_xe(truoc[iid], "total_count"), "", ""] + [""] * (len(LOP) - 1))
                continue
            d = {}
            for cot, _ in LOP:
                a, b = so_xe(truoc[iid], cot), so_xe(sau[iid], cot)
                d[cot] = None if a is None or b is None else b - a
            theo_doan[seg].append((iid, d))
            anh.append([seg, iid, r["timestamp"], "%.4f" % ti, "cả hai", sau[iid].get("label_status", ""),
                        "%g" % so_xe(truoc[iid], "total_count"), "%g" % so_xe(sau[iid], "total_count")]
                       + ["" if d[c] is None else "%+g" % d[c] for c, _ in LOP])
    for iid, r in truoc.items():                             # ảnh ngoài đoạn A/B (nếu có)
        if iid not in trong_doan:
            anh.append(["ngoài A/B", iid, r.get("timestamp", ""), "", "cả hai" if iid in sau else
                        "chỉ có ở bản ban đầu", sau.get(iid, {}).get("label_status", ""),
                        "%g" % so_xe(r, "total_count"),
                        "%g" % so_xe(sau[iid], "total_count") if iid in sau else "", "", ] + [""] * (len(LOP) - 1))
    for iid, r in sau.items():
        if iid not in truoc:
            anh.append(["", iid, r.get("timestamp", ""), "", "chỉ có ở bản nghiệm thu", r.get("label_status", ""),
                        "", "%g" % so_xe(r, "total_count"), ""] + [""] * (len(LOP) - 1))
    return anh, theo_doan


def tong_hop_dem(cfg, theo_doan, anh):
    bang = []
    nhom = [(seg, theo_doan[seg]) for seg in cfg["segments"]]
    nhom.append(("A+B", [x for seg in cfg["segments"] for x in theo_doan[seg]]))
    for ten, ds in nhom:
        for cot, ten_lop in LOP:
            cap = [(iid, d[cot]) for iid, d in ds if d[cot] is not None]
            if not cap:
                bang.append([ten, ten_lop, 0, "", "", "", "", "", ""])
                continue
            e = [x for _, x in cap]
            mae, rmse, einf = metrics(e)
            iid_max = max(cap, key=lambda c: abs(c[1]))[0]
            bang.append([ten, ten_lop, len(e), sum(1 for x in e if x != 0), "%+.4f" % (sum(e) / len(e)),
                         "%.4f" % mae, "%.4f" % rmse, "%g" % einf, iid_max if einf > 0 else ""])
    chi_dau = sum(1 for r in anh if r[4] == "chỉ có ở bản ban đầu")
    chi_sau = sum(1 for r in anh if r[4] == "chỉ có ở bản nghiệm thu")
    bang.append(["ghi chú", "ảnh không ghép được", "", "", "", "", "", "",
                 "chỉ ở bản ban đầu: %d; chỉ ở bản nghiệm thu: %d" % (chi_dau, chi_sau)])
    return bang


# ==== Phần 3: ảnh hưởng của sai số đếm lên I_tot và T (code tự viết) ====

def anh_huong_T(cfg, truoc, sau, p_truoc):
    tol, mx = cfg["bisection"]["tol_minutes"], cfg["bisection"]["max_iter"]
    bang, dT = [], {}
    for seg in cfg["segments"]:
        rows, t, y0 = doc_doan(p_truoc, seg)
        y1 = [float(sau[r["image_id"]]["total_count"]) if r["image_id"] in sau else v for r, v in zip(rows, y0)]
        t = np.asarray(t, dtype=DTYPE)
        y0, y1 = np.asarray(y0, dtype=DTYPE), np.asarray(y1, dtype=DTYPE)
        check_grid(t, y0)
        check_grid(t, y1)
        I0, I1 = cumulative(t, y0), cumulative(t, y1)       # cùng mốc t, chỉ khác số xe
        Q0, Q1 = q_levels(float(I0[-1]), cfg["q_fractions"]), q_levels(float(I1[-1]), cfg["q_fractions"])
        dT[seg] = []
        for q, a, b in zip(cfg["q_fractions"], Q0, Q1):
            T0 = bisect(t, y0, I0, a, tol, mx)["T"]
            T1 = bisect(t, y1, I1, b, tol, mx)["T"]
            dT[seg].append(T1 - T0)
            bang.append([seg, "%d%%" % round(100 * q), "%.6f" % I0[-1], "%.6f" % I1[-1],
                         "%+.4f" % (100.0 * (I1[-1] - I0[-1]) / I0[-1]), "%.6f" % a, "%.6f" % b,
                         "%.6f" % T0, "%.6f" % T1, "%+.6f" % (T1 - T0)])
    return bang, dT


def so_nguon(cfg, dT):
    # Đặt 3 nguồn sai số của T cạnh nhau (phút): thuật toán, lấy mẫu, dữ liệu
    tol = cfg["bisection"]["tol_minutes"]
    bang = []
    for seg in cfg["segments"]:
        bang.append([seg, "Thuật toán (dung sai chia đôi)", "cận lý thuyết |T − T*| ≤ tol/2", "", "",
                     "%.3e" % (tol / 2.0)])
        ls = khao_sat_lam_thua(cfg, seg)                     # lưới f2, f4 của snapshot đang chạy (data/)
        for f, (mae, rmse, einf) in sorted(ls["sai_so"].items()):
            bang.append([seg, "Lấy mẫu (làm thưa f%d)" % f, "T(f%d) − T(f1), cùng Q" % f,
                         "%.4f" % mae, "%.4f" % rmse, "%.4f" % einf])
        mae, rmse, einf = metrics(dT[seg])
        bang.append([seg, "Dữ liệu (nhãn ban đầu → nghiệm thu)", "T(nghiệm thu) − T(ban đầu), cùng lưới",
                     "%.4f" % mae, "%.4f" % rmse, "%.4f" % einf])
    return bang


# ==== Phần 4: chạy ====

def main():
    ap = argparse.ArgumentParser(description="Đề 20: sai số dữ liệu - đối chiếu hai snapshot")
    ap.add_argument("--tu-kiem", action="store_true", help="so snapshot ban đầu với chính nó, không ghi file")
    a = ap.parse_args()
    cfg = load_config()
    p_truoc, p_sau = duong_dan(cfg)
    if a.tu_kiem:
        p_sau = p_truoc
    elif not p_sau.exists():
        print("Chưa có snapshot nghiệm thu (%s): bỏ qua bước sai số dữ liệu, không ghi file."
              % p_sau.relative_to(ROOT).as_posix())
        print("Khi thầy gửi: chép file vào đường dẫn trên (hoặc khai báo trong config.json) rồi chạy lại main.py.")
        return
    if p_sau.resolve() == p_truoc.resolve() and not a.tu_kiem:
        sys.exit("Snapshot nghiệm thu trùng file với snapshot ban đầu. Kiểm tra config.json.")

    truoc, sau = doc_snapshot(p_truoc), doc_snapshot(p_sau)
    anh, theo_doan = sai_so_anh(cfg, truoc, sau, p_truoc)
    dem = tong_hop_dem(cfg, theo_doan, anh)
    bang_T, dT = anh_huong_T(cfg, truoc, sau, p_truoc)
    nguon = so_nguon(cfg, dT)
    trang_thai = sorted(set(r.get("label_status", "") for r in sau.values()))

    print("Ban đầu  : %s (%d ảnh)" % (p_truoc.relative_to(ROOT).as_posix(), len(truoc)))
    print("Nghiệm thu: %s (%d ảnh), label_status: %s" % (p_sau.relative_to(ROOT).as_posix(), len(sau),
                                                        ", ".join(trang_thai)))
    if trang_thai != ["human_verified"] and not a.tu_kiem:
        print("CẢNH BÁO: bản nghiệm thu còn ảnh chưa human_verified -> kết quả vẫn là sơ bộ.")
    print("\n(1) Sai số đếm theo ảnh (xe) - tổng số xe")
    print("%-5s %8s %8s %10s %8s %8s %6s" % ("Đoạn", "Số ảnh", "Ảnh lệch", "Lệch TB", "MAE", "RMSE", "E∞"))
    for r in dem:
        if r[1] == "Tổng số xe":
            print("%-5s %8s %8s %10s %8s %8s %6s" % tuple(r[0:1] + r[2:8]))
    print("  " + dem[-1][-1])
    print("\n(2) Ảnh hưởng lên T (cùng lưới thời gian, chỉ đổi số xe)")
    print("%-5s %5s %14s %14s %14s %14s %12s" % ("Đoạn", "q", "I_tot đầu", "I_tot sau", "T đầu (phút)",
                                                  "T sau (phút)", "ΔT (phút)"))
    for r in bang_T:
        print("%-5s %5s %14s %14s %14s %14s %12s" % (r[0], r[1], r[2], r[3], r[7], r[8], r[9]))
    print("\n(3) So ba nguồn sai số của T (phút)")
    print("%-5s %-38s %10s %10s %10s" % ("Đoạn", "Nguồn", "MAE", "RMSE", "E∞"))
    for r in nguon:
        print("%-5s %-38s %10s %10s %10s" % (r[0], r[1], r[3], r[4], r[5]))

    if a.tu_kiem:
        lech = max([abs(float(r[9])) for r in bang_T] + [float(r[7]) for r in dem if r[7] not in ("", None)])
        print("\nTỰ KIỂM: %s (lệch lớn nhất %g). Không ghi file." % ("ĐẠT" if lech == 0 else "KHÔNG ĐẠT", lech))
        return
    write_csv("data_error_images.csv",
              ["Đoạn", "image_id", "timestamp", "t (phút)", "Ghép", "label_status (nghiệm thu)",
               "Tổng số xe ban đầu", "Tổng số xe nghiệm thu"] + ["Δ %s (xe)" % ten for _, ten in LOP], anh)
    write_csv("data_error_summary.csv",
              ["Đoạn", "Lớp", "Số ảnh so", "Số ảnh lệch", "Lệch trung bình có dấu (xe)", "MAE (xe)", "RMSE (xe)",
               "E∞ (xe)", "Ảnh lệch nhiều nhất (image_id)"], dem)
    write_csv("data_error_T.csv",
              ["Đoạn", "Mức q", "I_tot ban đầu (xe·phút)", "I_tot nghiệm thu (xe·phút)", "ΔI_tot (%)",
               "Q ban đầu (xe·phút)", "Q nghiệm thu (xe·phút)", "T ban đầu (phút)", "T nghiệm thu (phút)",
               "ΔT (phút)"], bang_T)
    write_csv("data_error_sources.csv",
              ["Đoạn", "Nguồn sai số", "Cách đo", "MAE (phút)", "RMSE (phút)", "E∞ (phút)"], nguon)
    print("\nĐã ghi results/data_error_images.csv, data_error_summary.csv, data_error_T.csv, data_error_sources.csv")


if __name__ == "__main__":
    main()