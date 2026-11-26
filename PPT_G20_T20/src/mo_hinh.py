"""Đề tài 20 - Mô hình tính toán: tích phân hình thang, chia đôi, khảo sát làm thưa lưới và dung sai.

Chạy từ thư mục gốc:
  python src\\mo_hinh.py          -> menu: 1 chạy hết, 2 tính riêng, 3 kiểm chứng
  python src\\mo_hinh.py --het    -> chạy hết, không hỏi
  python src\\mo_hinh.py --demo   -> mở thẳng menu tính riêng
"""
# ==== Phần 1: chuẩn bị =============================================
import argparse
import csv
import json
import math
import sys
from pathlib import Path

import numpy as np

try:
    sys.stdout.reconfigure(encoding="utf-8")         # in tiếng Việt có dấu ra terminal không bị lỗi
except Exception:
    pass

try:
    HERE = Path(__file__).resolve().parent           # chạy cả file: thư mục chứa file
except NameError:
    HERE = Path.cwd()                                # chạy từng ô: thư mục đang làm việc
ROOT = HERE if (HERE / "config.json").exists() else HERE.parent   # tự tìm config.json
DTYPE = np.float64                                   # kiểu số thực 64 bit


def load_config():
    with open(ROOT / "config.json", encoding="utf-8") as f:
        return json.load(f)


def data_dir():
    return ROOT / "data"


def results_dir():
    d = ROOT / "results"
    d.mkdir(exist_ok=True)                           # chưa có thư mục results thì tự tạo
    return d


# ==== Phần 2: tích phân hình thang =================================
# 2.1: Đọc dữ liệu từ lưới (grid) và kiểm tra tính hợp lệ

def grid_path(seg, kind, f):
    # Đường dẫn file lưới, ví dụ ("A", "timestamps", 1) -> data\grid_A_timestamps_f1.csv
    return data_dir() / ("grid_%s_%s_f%d.csv" % (seg, kind, f))


def read_grid(path):
    # Đọc file lưới, trả về 2 mảng: t (phút) và y (số xe)
    t, y = [], []
    with open(path, encoding="utf-8-sig", newline="") as fh:   # utf-8-sig: bỏ ký tự ẩn BOM của Excel
        for r in csv.DictReader(fh):
            t.append(float(r["t_min"]))
            y.append(float(r["y"]))
    return np.asarray(t, dtype=DTYPE), np.asarray(y, dtype=DTYPE)


def check_grid(t, y):
    # Kiểm tra dữ liệu trước khi tính; sai thì dừng và báo lỗi
    if len(t) != len(y) or len(t) < 2:               # t, y cùng độ dài và có ít nhất 2 mốc
        raise ValueError("Cần ít nhất 2 mốc và số phần tử t, y phải bằng nhau")
    for i in range(len(t)):
        if not (t[i] == t[i]) or abs(t[i]) == float("inf") or not (y[i] == y[i]):
            raise ValueError("Giá trị không hữu hạn tại mốc %d" % i)
        if i > 0 and not t[i] > t[i - 1]:            # thời gian phải tăng dần, không trùng
            raise ValueError("Thời gian phải tăng nghiêm ngặt (mốc %d)" % i)


# 2.2: Tích phân hình thang

def cumulative(t, y):
    # Tải tích lũy tại từng mốc: I[0] = 0, I[k+1] = I[k] + diện tích hình thang khoảng k
    n = len(t)
    I = np.zeros(n, dtype=DTYPE)                     # n ô toàn số 0; ô đầu I[0] = 0
    for k in range(n - 1):                           # đi qua n-1 khoảng
        h = t[k + 1] - t[k]                          # bề rộng khoảng k (phút)
        I[k + 1] = I[k] + h * (y[k] + y[k + 1]) / 2.0
    return I                                         # I[-1] là tổng tải I_tot (xe·phút)


# Thử 2.2: nhập khoảng k -> xem hình thang A_k và I_k, I_k+1

def chon_luoi():
    # Hỏi đoạn và mức làm thưa, đọc lưới, kiểm tra, tính tích lũy
    seg = input("Đoạn (A/B, Enter = A): ").strip().upper() or "A"
    f = int(input("Mức làm thưa f (1/2/4, Enter = 1): ").strip() or 1)
    t, y = read_grid(grid_path(seg, "timestamps", f))
    check_grid(t, y)
    I = cumulative(t, y)
    n = len(t)
    print("Đoạn %s, f%d: %d mốc (0..%d), %d khoảng (k = 0..%d)" % (seg, f, n, n - 1, n - 1, n - 2))
    print("T từ %.4f đến %.4f phút | I_tot = %.4f xe·phút" % (t[0], t[-1], I[-1]))
    return t, y, I


def thu_tich_phan():
    t, y, I = chon_luoi()
    n = len(t)
    while True:
        s = input("\nNhập khoảng k (0..%d), Enter để thoát: " % (n - 2)).strip()
        if s == "":                                  # Enter trống -> thoát
            break
        try:
            k = int(s)
        except ValueError:
            print("  Hãy nhập số nguyên.")
            continue
        if not (0 <= k <= n - 2):                    # n mốc thì có n-1 khoảng: 0..n-2
            print("  k phải từ 0 đến %d." % (n - 2))
            continue
        h = t[k + 1] - t[k]
        A = h * (y[k] + y[k + 1]) / 2.0              # diện tích hình thang
        print("  Mốc k   : t = %.4f phút, y = %g xe" % (t[k], y[k]))
        print("  Mốc k+1 : t = %.4f phút, y = %g xe" % (t[k + 1], y[k + 1]))
        print("  h = %.4f phút | hình thang A_k = h(y_k + y_k+1)/2 = %.4f xe·phút" % (h, A))
        print("  I_k = %.4f  ->  I_k+1 = I_k + A_k = %.4f xe·phút" % (I[k], I[k + 1]))


# 2.3: Tải tích lũy tại thời điểm T bất kỳ

def locate(t, T):
    # Tìm khoảng k chứa T, tức t[k] <= T <= t[k+1] (tìm nhị phân, chỉ so T với các mốc t)
    n = len(t)
    if T <= t[0]:
        return 0
    if T >= t[n - 1]:
        return n - 2
    lo, hi = 0, n - 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if t[mid] <= T:
            lo = mid                                 # T nằm bên phải mid
        else:
            hi = mid                                 # T nằm bên trái mid
    return lo


def y_interp(t, y, T):
    # Số xe ỹ(T): nối thẳng giữa 2 mốc (nội suy tuyến tính từng đoạn)
    k = locate(t, T)
    h = t[k + 1] - t[k]
    return y[k] + (y[k + 1] - y[k]) * (T - t[k]) / h


def I_of_T(t, y, I, T):
    # Tải tích lũy từ đầu đến T: I(T) = I_k + y_k*s + m*s^2/2
    k = locate(t, T)
    s = T - t[k]                                     # quãng đã đi trong khoảng k (phút)
    m = (y[k + 1] - y[k]) / (t[k + 1] - t[k])        # độ dốc của ỹ trong khoảng k
    return I[k] + y[k] * s + m * s * s / 2.0


# Thử 2.3: nhập T -> khoảng chứa T, số xe tại T, tải tích lũy đến T

def thu_nhap():
    t, y, I = chon_luoi()
    while True:
        s = input("\nNhập T (phút), Enter để thoát: ").strip()
        if s == "":
            break
        try:
            T = float(s)
        except ValueError:
            print("  Hãy nhập một số.")
            continue
        if not (t[0] <= T <= t[-1]):
            print("  T phải nằm trong [%.4f, %.4f]" % (t[0], t[-1]))
            continue
        k = locate(t, T)
        iT = I_of_T(t, y, I, T)
        print("  Khoảng k = %d (giữa t = %.4f và t = %.4f)" % (k, t[k], t[k + 1]))
        print("  Số xe ỹ(T) = %.4f xe" % y_interp(t, y, T))
        print("  Tải I(T)   = %.4f xe·phút (%.2f%% tổng)" % (iT, 100 * iT / I[-1]))


# ==== Phần 3: tìm T bằng chia đôi ==================================
# 3.1: Lập phương trình F(T) = I(T) - Q = 0

def q_levels(total, fractions):
    # Các mức Q = q * I_tot, ví dụ q = 0.25, 0.5, 0.75
    return [f * total for f in fractions]


def F_of_T(t, y, I, Q, T):
    # F(T) = I(T) - Q; F < 0: tải chưa đủ Q, F >= 0: tải đã đủ Q
    return I_of_T(t, y, I, T) - Q


# 3.2: Thuật toán chia đôi
#   Luôn giữ F(a) < 0 <= F(b). Dừng khi b - a <= tol/2 (tức chạy thêm 1 vòng so với b - a <= tol).
#   Lấy T = b (cận trên): bảo đảm I(T) >= Q, và |T - T*| <= b - a <= tol/2.
#   Trả thêm T_giua = (a + b)/2 để so sánh (cận sai số (b - a)/2 nhưng có thể F(T_giua) < 0).

def bisect(t, y, I, Q, tol, max_iter, F=None, in_vong=False):
    if F is None:                                    # mặc định: F(T) = I(T) - Q trên lưới t, y
        def F(T):
            return F_of_T(t, y, I, Q, T)
    a, b = float(t[0]), float(t[-1])                 # khoảng ban đầu: cả đoạn
    fa, fb = F(a), F(b)
    if fb < 0.0:                                     # tới cuối đoạn vẫn chưa đủ Q -> vô nghiệm
        raise ValueError("Q = %.6g lớn hơn tổng tích phân %.6g: không đạt được" % (Q, fb + Q))
    if fa >= 0.0:                                    # Q <= 0: đạt ngay tại mốc đầu
        return {"T": a, "T_giua": a, "iters": 0, "width": 0.0, "residual": fa, "F_giua": fa,
                "a": a, "b": a}
    it = 0
    while (b - a) > tol / 2.0 and it < max_iter:     # thêm 1 vòng: dừng khi b - a <= tol/2
        m = (a + b) / 2.0
        Fm = F(m)
        if in_vong:
            print("  vòng %2d: a = %.6f  b = %.6f  m = %.6f  F(m) = %+.6f" % (it + 1, a, b, m, Fm))
        if Fm >= 0.0:
            b = m                                    # tại m đã đủ Q -> nghiệm ở nửa trái
        else:
            a = m                                    # tại m chưa đủ Q -> nghiệm ở nửa phải
        it += 1
    c = (a + b) / 2.0
    return {"T": b, "T_giua": c, "iters": it, "width": b - a,
            "residual": F(b),                        # F(b) >= 0: tải tại T đã chạm hoặc vượt Q
            "F_giua": F(c), "a": a, "b": b}


def bisect_diem_giua(t, y, I, Q, tol, max_iter):
    # CÁCH CŨ (chỉ để so sánh): dừng khi b - a <= tol, lấy T = điểm giữa (a + b)/2.
    # Gọi bisect với 2*tol -> dừng đúng lúc b - a <= tol (ít hơn cách mới 1 vòng).
    r = bisect(t, y, I, Q, 2.0 * tol, max_iter)
    return {"T": r["T_giua"], "iters": r["iters"], "width": r["width"], "residual": r["F_giua"]}


def sci(x, nd=3):
    # Hiển thị kiểu 10^: 3.876e-13 -> "3.876 x 10^-13"
    if x == 0:
        return "0"
    m, e = ("%.*e" % (nd, x)).split("e")
    return "%s x 10^%d" % (m, int(e))


# Thử 3: nhập q -> tìm T bằng chia đôi

def thu_chia_doi():
    cfg = load_config()
    seg = input("Đoạn (A/B, Enter = A): ").strip().upper() or "A"
    f = int(input("Mức làm thưa f (1/2/4, Enter = 1): ").strip() or 1)
    t, y = read_grid(grid_path(seg, "timestamps", f))
    check_grid(t, y)
    I = cumulative(t, y)
    t1, y1 = read_grid(grid_path(seg, "timestamps", 1))
    tot_goc = float(cumulative(t1, y1)[-1])          # Q luôn chốt từ lưới gốc f1
    print("Đoạn %s, f%d: T từ %.4f đến %.4f phút | I_tot lưới này = %.4f | I_tot gốc f1 = %.4f"
          % (seg, f, t[0], t[-1], I[-1], tot_goc))
    while True:
        s = input("\nNhập q (0 < q <= 1, ví dụ 0.5), Enter để thoát: ").strip()
        if s == "":
            break
        try:
            q = float(s)
        except ValueError:
            print("  Hãy nhập một số.")
            continue
        if not (0 < q <= 1):
            print("  q phải nằm trong (0, 1].")
            continue
        Q = q * tot_goc
        if Q > I[-1]:
            print("  Q = %.4f lớn hơn tổng trên lưới f%d (%.4f): không có nghiệm." % (Q, f, I[-1]))
            continue
        s = input("  Dung sai tol = 10^? (Enter = -6): ").strip()
        tol = 10.0 ** float(s or -6)
        xem = input("  In từng vòng? (c/k, Enter = k): ").strip().lower() == "c"
        r = bisect(t, y, I, Q, tol, cfg["bisection"]["max_iter"], in_vong=xem)
        g = bisect_diem_giua(t, y, I, Q, tol, cfg["bisection"]["max_iter"])
        print("  Q = %.6f xe·phút\n" % Q)
        print("  %-24s %-24s %-24s" % ("", "CÁCH MỚI: T = b", "CÁCH CŨ: T = điểm giữa"))
        print("  %-24s %-24s %-24s" % ("Điều kiện dừng", "b − a <= tol/2", "b − a <= tol"))
        print("  %-24s %-24s %-24s" % ("T (phút)", "%.9f" % r["T"], "%.9f" % g["T"]))
        print("  %-24s %-24s %-24s" % ("Số vòng", r["iters"], g["iters"]))
        print("  %-24s %-24s %-24s" % ("Độ rộng b − a (phút)", sci(r["width"]), sci(g["width"])))
        print("  %-24s %-24s %-24s" % ("Cận sai số (phút)", "<= " + sci(r["width"]), "<= " + sci(g["width"] / 2)))
        print("  %-24s %-24s %-24s" % ("F(T) = I(T) − Q", sci(r["residual"]), sci(g["residual"])))
        kr, kg = locate(t, r["T"]), locate(t, g["T"])
        print("  %-24s %-24s %-24s" % ("Khoảng k chứa T", kr, kg))
        print("  %-24s %-24s %-24s" % ("t_k → t_k+1 (phút)", "%.4f → %.4f" % (t[kr], t[kr + 1]),
                                       "%.4f → %.4f" % (t[kg], t[kg + 1])))
        print("  %-24s %-24s %-24s" % ("Tải đã đạt Q?", "có" if r["residual"] >= 0 else "CHƯA",
                                       "có" if g["residual"] >= 0 else "CHƯA"))


# ==== Phần 4: khảo sát làm thưa lưới và dung sai ===================
# 4.1: Ba chỉ số sai số

def metrics(errs):
    # MAE: trung bình |e|; RMSE: căn trung bình e^2; E_inf: |e| lớn nhất
    n = len(errs)
    mae = sum(abs(e) for e in errs) / n
    rmse = math.sqrt(sum(e * e for e in errs) / n)
    einf = max(abs(e) for e in errs)
    return mae, rmse, einf


# 4.2: Ảnh hưởng của làm thưa lưới (f2, f4 so với lưới gốc f1)

def khao_sat_lam_thua(cfg, seg, kind="timestamps"):
    tol, mx = cfg["bisection"]["tol_minutes"], cfg["bisection"]["max_iter"]
    data = {}
    for f in cfg["thin_factors"]:                    # đọc cả 3 lưới f1, f2, f4
        t, y = read_grid(grid_path(seg, kind, f))
        check_grid(t, y)
        data[f] = (t, y, cumulative(t, y))
    t1, y1, I1 = data[1]
    Qs = q_levels(float(I1[-1]), cfg["q_fractions"])    # Q chốt từ lưới gốc f1
    Tref = [bisect(t1, y1, I1, Q, tol, mx)["T"] for Q in Qs]   # T gốc: f1, dung sai chính thức
    T_thua, sai_so = {}, {}
    for f in cfg["thin_factors"]:
        if f == 1:
            continue                                 # f1 là mốc so sánh
        t, y, I = data[f]
        Ts = []
        for Q in Qs:
            if Q > I[-1]:                            # lưới thưa không đạt được Q
                Ts.append(None)
            else:
                Ts.append(bisect(t, y, I, Q, tol, mx)["T"])
        T_thua[f] = Ts
        if None not in Ts:
            errs = [T - Tr for T, Tr in zip(Ts, Tref)]   # độ lệch so với lưới gốc (phút)
            sai_so[f] = metrics(errs)
    p = float("nan")                                 # chỉ báo bậc p = log2(E_f4 / E_f2)
    if 2 in sai_so and 4 in sai_so and sai_so[2][2] > 0 and sai_so[4][2] > 0:
        p = math.log2(sai_so[4][2] / sai_so[2][2])
    return {"Qs": Qs, "Tref": Tref, "T_thua": T_thua, "sai_so": sai_so, "p": p}


# 4.3: Ảnh hưởng của dung sai chia đôi (trên lưới gốc f1)

def khao_sat_dung_sai(cfg, seg, kind="timestamps"):
    mx = cfg["bisection"]["max_iter"]
    t, y = read_grid(grid_path(seg, kind, 1))
    check_grid(t, y)
    I = cumulative(t, y)
    Qs = q_levels(float(I[-1]), cfg["q_fractions"])
    ket_qua = []
    for frac, Q in zip(cfg["q_fractions"], Qs):
        Tref = bisect(t, y, I, Q, cfg["bisection"]["tol_minutes"], mx)["T"]   # T ở dung sai chính thức
        for tl in cfg["tol_study_minutes"]:          # thử các mức trong tol_study_minutes
            r = bisect(t, y, I, Q, tl, mx)
            ket_qua.append({"q": frac, "tol": tl, "iters": r["iters"], "T": r["T"],
                            "lech": abs(r["T"] - Tref), "residual": r["residual"]})
    return ket_qua


# Thử 4: chọn đoạn -> xem kết quả hai khảo sát

def thu_khao_sat():
    cfg = load_config()
    seg = input("Đoạn (A/B, Enter = A): ").strip().upper() or "A"
    ls = khao_sat_lam_thua(cfg, seg)
    print("\n(1) Làm thưa lưới, đoạn %s (phút)" % seg)
    for i, frac in enumerate(cfg["q_fractions"]):
        dong = "  q = %.2f: T_f1 = %.4f" % (frac, ls["Tref"][i])
        for f, Ts in ls["T_thua"].items():
            dong += " | T_f%d = %s" % (f, "không đạt" if Ts[i] is None else "%.4f" % Ts[i])
        print(dong)
    for f, (mae, rmse, einf) in ls["sai_so"].items():
        print("  f%d: MAE = %.4f  RMSE = %.4f  E∞ = %.4f" % (f, mae, rmse, einf))
    print("  Chỉ báo p = log2(E_f4 / E_f2) = %.3f (dữ liệu thực có nhiễu, chỉ tham khảo)" % ls["p"])
    print("\n(2) Dung sai chia đôi, đoạn %s, lưới f1" % seg)
    for r in khao_sat_dung_sai(cfg, seg):
        print("  q = %.2f  tol = %-7g vòng = %2d  |T - T(tol chính thức)| = %s phút" % (
            r["q"], r["tol"], r["iters"], sci(r["lech"])))


# ==== Phần 5: tổng hợp kết quả, ghi file, chạy chương trình ========
# 5.1: Lập các bảng kết quả cho cả A, B và ghi ra file CSV

def write_csv(name, head, rows):
    # Ghi bảng vào results/<name>. utf-8-sig để Excel hiện đúng tiếng Việt có dấu.
    try:
        with open(results_dir() / name, "w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh)
            w.writerow(head)
            w.writerows(rows)
    except PermissionError:
        raise SystemExit("Không ghi được results/%s: file đang mở (Excel?). Đóng file rồi chạy lại." % name)


def lap_bang(cfg):
    # Gọi lại các hàm Phần 2-4 cho mọi đoạn, lưới, mức q; trả về 4 bảng (tên cột, các dòng)
    tol, mx = cfg["bisection"]["tol_minutes"], cfg["bisection"]["max_iter"]
    qs = cfg["q_fractions"]
    tp, cd, ls, ds = [], [], [], []
    for seg in cfg["segments"]:
        for kind in cfg["base_grids"]:
            Qs = None
            for f in cfg["thin_factors"]:            # (a) tích phân và (b) chia đôi
                t, y = read_grid(grid_path(seg, kind, f))
                check_grid(t, y)
                I = cumulative(t, y)
                total, cover = float(I[-1]), float(t[-1] - t[0])
                if f == 1:
                    Qs = q_levels(total, qs)         # Q chốt từ lưới gốc f1
                tp.append([seg, "f%d" % f, len(t), "%.9f" % cover, "%.9f" % total,
                           "%.9f" % (total / cover)] + ["%.9f" % Q for Q in Qs])
                for frac, Q in zip(qs, Qs):
                    r = bisect(t, y, I, Q, tol, mx)              # cách mới: T = b
                    g = bisect_diem_giua(t, y, I, Q, tol, mx)    # cách cũ: T = điểm giữa (so sánh)
                    k = locate(t, r["T"])                         # khoảng k chứa nghiệm T = b
                    cd.append([seg, "f%d" % f, "%d%%" % round(100 * frac), "%.9f" % Q, k,
                               "%.4f → %.4f" % (t[k], t[k + 1]),
                               "%.9f" % r["T"], r["iters"], "%.3e" % r["width"], "%.3e" % r["residual"],
                               "%.9f" % g["T"], g["iters"], "%.3e" % g["width"], "%.3e" % g["residual"],
                               "%.3e" % (r["T"] - g["T"])])
            k = khao_sat_lam_thua(cfg, seg, kind)    # (c) làm thưa lưới
            for f, (mae, rmse, einf) in k["sai_so"].items():
                ls.append([seg, "f%d" % f, "%.4f" % mae, "%.4f" % rmse, "%.4f" % einf, ""])
            ls.append([seg, "chỉ báo p", "", "", "", "%.3f" % k["p"]])
            for r in khao_sat_dung_sai(cfg, seg, kind):   # (d) dung sai
                ds.append([seg, "%d%%" % round(100 * r["q"]), "%g" % r["tol"], r["iters"],
                           "%.9f" % r["T"], "%.3e" % r["lech"], "%.3e" % r["residual"]])
    return {
        "integral_summary.csv": (["Đoạn", "Lưới", "Số mốc", "Thời gian phủ (phút)", "Tổng tải I_tot (xe·phút)",
                                  "Số xe trung bình theo thời gian (xe)"]
                                 + ["Q %d%% (xe·phút)" % round(100 * q) for q in qs], tp),
        "bisection_results.csv": (["Đoạn", "Lưới", "Mức q", "Q (xe·phút)", "Khoảng k chứa T",
                                   "t_k → t_k+1 (phút)",
                                   "[Mới] T = b (phút)", "[Mới] Số vòng", "[Mới] Độ rộng b − a (phút)",
                                   "[Mới] Residual F(b) (xe·phút)",
                                   "[Cũ] T = điểm giữa (phút)", "[Cũ] Số vòng", "[Cũ] Độ rộng b − a (phút)",
                                   "[Cũ] Residual F(T giữa) (xe·phút)", "T mới − T cũ (phút)"], cd),
        "sampling_summary.csv": (["Đoạn", "Lưới", "MAE (phút)", "RMSE (phút)", "E∞ (phút)", "Chỉ báo p"], ls),
        "tolerance_study.csv": (["Đoạn", "Mức q", "tol (phút)", "Số vòng", "T (phút)",
                                 "|T(tol) − T(tol chính thức)| (phút)", "Residual F(T) (xe·phút)"], ds),
    }


def ghi_ket_qua(bang):
    # Ghi từng bảng ra file CSV trong thư mục results
    for ten, (head, rows) in bang.items():
        write_csv(ten, head, rows)
        print("Đã ghi results/%s (%d dòng)" % (ten, len(rows)))


# 5.2: In ra terminal các bảng kết quả và dòng so sánh hai nguồn biến động

def in_bang(bang, cfg):
    tol = cfg["bisection"]["tol_minutes"]
    _, tp = bang["integral_summary.csv"]
    print("\n== (1) TÍCH PHÂN: tổng tải mỗi lưới ==")
    print("%-4s %-4s %5s %12s %14s %10s" % ("Đoạn", "Lưới", "Mốc", "Phủ (phút)", "I_tot (xe·ph)", "TB (xe)"))
    for r in tp:
        print("%-4s %-4s %5s %12.4f %14.4f %10.4f" % (r[0], r[1], r[2], float(r[3]), float(r[4]), float(r[5])))

    _, cd = bang["bisection_results.csv"]
    print("\n== (2) CHIA ĐÔI (tol = %g phút) ==" % tol)
    print("     Mới: T = b, dừng khi b − a <= tol/2   |   Cũ: T = điểm giữa, dừng khi b − a <= tol")
    print("%-4s %-4s %-4s %4s | %13s %5s %10s %10s | %13s %5s %10s %10s" % (
        "Đoạn", "Lưới", "q", "k", "T mới", "Vòng", "Độ rộng", "F(T)", "T cũ", "Vòng", "Độ rộng", "F(T)"))
    for r in cd:
        print("%-4s %-4s %-4s %4s | %13.6f %5s %10s %10s | %13.6f %5s %10s %10s" % (
            r[0], r[1], r[2], r[4], float(r[6]), r[7], r[8], r[9], float(r[10]), r[11], r[12], r[13]))

    _, ls = bang["sampling_summary.csv"]
    print("\n== (3) LÀM THƯA LƯỚI: độ lệch T so với lưới gốc f1 (phút) ==")
    print("%-4s %-10s %9s %9s %9s %8s" % ("Đoạn", "Lưới", "MAE", "RMSE", "E∞", "p"))
    for r in ls:
        print("%-4s %-10s %9s %9s %9s %8s" % tuple(r))

    _, ds = bang["tolerance_study.csv"]
    print("\n== (4) DUNG SAI: |T(tol) − T(%g)| trên lưới f1 (phút) ==" % tol)
    print("%-4s %-4s %8s %6s %12s" % ("Đoạn", "q", "tol", "Vòng", "Độ lệch"))
    for r in ds:
        print("%-4s %-4s %8s %6s %12s" % (r[0], r[1], r[2], r[3], r[5]))

    # So sánh: biến động lớn nhất do lấy mẫu với biến động do dung sai chính thức
    lay_mau = max(float(r[4]) for r in ls if r[1] != "chỉ báo p")
    min_hon = [float(r[5]) for r in ds if float(r[2]) < tol]       # các mức mịn hơn tol chính thức
    dung_sai = max(min_hon) if min_hon else tol / 2                 # không có thì dùng cận tol/2
    print("\n== SO SÁNH (Bước 5) ==")
    print("Biến động do LẤY MẪU (E∞ lớn nhất)         = %.4f phút" % lay_mau)
    print("Biến động do DUNG SAI chính thức (tol = %g) = %s phút" % (tol, sci(dung_sai)))
    if lay_mau > 10 * dung_sai:
        print("=> Biến động do lấy mẫu lớn hơn rất nhiều: độ tin cậy của T bị giới hạn bởi mật độ ảnh,")
        print("   không phải bởi thuật toán chia đôi.")
    else:
        print("=> Hai nguồn biến động cùng bậc, cần xem thêm.")
    print("Lưu ý: nhãn là prelabel -> kết quả SƠ BỘ; chỉ báo p trên dữ liệu có nhiễu chỉ để tham khảo.")


# 5.3: Menu tính riêng (gom các hàm thử của Phần 2-4)

def menu():
    lua_chon = {
        "1": ("Xem hình thang của khoảng k", thu_tich_phan),
        "2": ("Tính tải tích lũy I(T) tại T bất kỳ", thu_nhap),
        "3": ("Tìm T theo q bằng chia đôi", thu_chia_doi),
        "4": ("Xem khảo sát làm thưa và dung sai của một đoạn", thu_khao_sat),
    }
    while True:
        print("\n=== TÍNH RIÊNG (Đề 20) ===")
        for so, (ten, _) in lua_chon.items():
            print("%s) %s" % (so, ten))
        print("0) Thoát")
        c = input("Chọn: ").strip()
        if c == "0":
            break
        if c not in lua_chon:
            print("Hãy chọn 0-%d." % len(lua_chon))
            continue
        try:
            lua_chon[c][1]()
        except (ValueError, OSError) as e:           # nhập sai hoặc không có file lưới
            print("Lỗi:", e)


# 5.4: Chương trình chính

def main():
    ap = argparse.ArgumentParser(description="Đề 20: thời điểm đạt chỉ số tải tích lũy")
    ap.add_argument("--het", action="store_true", help="chạy hết mô hình, không hỏi")
    ap.add_argument("--demo", action="store_true", help="mở menu tính riêng, không hỏi")
    args = ap.parse_args()
    cfg = load_config()
    if args.het:
        c = "1"
    elif args.demo:
        c = "2"
    else:                                            # bấm ▷ hoặc chạy không kèm gì -> hỏi
        print("=== ĐỀ 20 ===\n1) Chạy hết mô hình (ghi file + in kết quả)\n2) Tính riêng (menu thử)"
              "\n3) Kiểm chứng y = 1 + t\n0) Thoát")
        c = input("Chọn: ").strip()
    if c == "1":
        bang = lap_bang(cfg)
        ghi_ket_qua(bang)
        in_bang(bang, cfg)
    elif c == "2":
        menu()
    elif c == "3":
        sys.path.insert(0, str(ROOT / "src"))        # cho Python tìm thấy kiem_chung.py trong src
        from kiem_chung import kiem_chung, kiem_chung_lam_thua   # chỉ nạp khi chọn mục này
        kiem_chung(cfg)
        kiem_chung_lam_thua(cfg)


if __name__ == "__main__":
    main()