"""Mô hình tính toán"""
# ==== Phần 1: chuẩn bị ===============================
import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np

try:
    HERE = Path(__file__).resolve().parent   # chạy cả file: thư mục chứa file
except NameError:
    HERE = Path.cwd()                        # chạy từng ô: thư mục đang làm việc
ROOT = HERE if (HERE / "config.json").exists() else HERE.parent   # tự tìm config.json
DTYPE = np.float64                           # Kiểu số thực 64 bit


def load_config():
    with open(ROOT / "config.json", encoding="utf-8") as f:
        return json.load(f)


def data_dir():
    return ROOT / "data"


def results_dir():
    d = ROOT / "results"
    d.mkdir(exist_ok=True)          # chua co thu muc results thi tu tao
    return d

# ==== Phần 2: tích phân hình thang =============================
# 2.1: Đọc dữ liệu từ lưới (grid) và kiểm tra tính hợp lệ

def grid_path(seg, kind, f):
    # Tạo đường dẫn file lưới, ví dụ ("A", "timestamps", 1) -> data\grid_A_timestamps_f1.csv
    return data_dir() / ("grid_%s_%s_f%d.csv" % (seg, kind, f))


def read_grid(path):
    # Đọc file lưới, trả về 2 mảng: t (phút) và y (số xe)
    t, y = [], []
    with open(path, encoding="utf-8-sig", newline="") as fh: # utf-8-sig: bỏ ký tự ẩn BOM của Excel
        for r in csv.DictReader(fh):
            t.append(float(r["t_min"]))
            y.append(float(r["y"]))
    return np.asarray(t, dtype=DTYPE), np.asarray(y, dtype=DTYPE) # đổi sang mảng float64


def check_grid(t, y):
    # Kiểm tra dữ liệu trước khi tính; sai thì dừng và báo lỗi
    if len(t) != len(y) or len(t) < 2: # t, y phải cùng độ dài (số mốc) và có ít nhất 2 mốc
        raise ValueError("can it nhat 2 moc va len(t) == len(y)")
    for i in range(len(t)):
        if not (t[i] == t[i]) or abs(t[i]) == float("inf") or not (y[i] == y[i]):
            raise ValueError("gia tri khong huu han tai moc %d" % i)
        if i > 0 and not t[i] > t[i - 1]: # thời gian phải tăng dần, không trùng
            raise ValueError("thoi gian phai tang nghiem ngat (moc %d)" % i)

# 2.2: Tích phân hình thang
def cumulative(t, y):
    # Tải tích lũy tại từng mốc: I[0] = 0, I[k+1] = I[k] + diện tích hình thang khoảng k
    n = len(t) 
    I = np.zeros(n, dtype=DTYPE) # tạo n ô toàn số 0; ô đầu I[0] = 0
    for k in range(n - 1): # đi qua n-1 khoảng
        h = t[k + 1] - t[k] # bề rộng khoảng k (phút)
        I[k + 1] = I[k] + h * (y[k] + y[k + 1]) / 2.0 # cộng diện tích hình thang
    return I # I[-1] là tổng tải I_tot (xe.phút)

# Thử 2.2: nhập khoảng k -> xem hình thang A_k và I_k, I_k+1
def chon_luoi():
    # Hỏi đoạn và mức làm thưa, đọc lưới, kiểm tra, tính tích lũy
    seg = input("Doan (A/B, Enter = A): ").strip().upper() or "A"
    f = int(input("Muc lam thua f (1/2/4, Enter = 1): ").strip() or 1)
    t, y = read_grid(grid_path(seg, "timestamps", f))
    check_grid(t, y)
    I = cumulative(t, y)
    n = len(t)
    print("Doan %s, f%d: %d moc (0..%d), %d khoang (k = 0..%d)" % (seg, f, n, n - 1, n - 1, n - 2))
    print("T tu %.4f den %.4f phut | I_tot = %.4f xe.phut" % (t[0], t[-1], I[-1]))
    return t, y, I


def thu_tich_phan():
    t, y, I = chon_luoi()
    n = len(t)
    while True:
        s = input("\nNhap khoang k (0..%d), Enter de thoat: " % (n - 2)).strip()
        if s == "":                                   # Enter trống -> thoát
            break
        try:
            k = int(s)                                # k là số nguyên
        except ValueError:
            print("  Hay nhap so nguyen.")
            continue
        if not (0 <= k <= n - 2):                     # n mốc thì có n-1 khoảng: 0..n-2
            print("  k phai tu 0 den %d." % (n - 2))
            continue
        h = t[k + 1] - t[k]                           # bề rộng khoảng
        A = h * (y[k] + y[k + 1]) / 2.0               # diện tích hình thang
        print("  Moc k   : t = %.4f phut, y = %g xe" % (t[k], y[k]))
        print("  Moc k+1 : t = %.4f phut, y = %g xe" % (t[k + 1], y[k + 1]))
        print("  h = %.4f phut | hinh thang A_k = h*(y_k + y_k+1)/2 = %.4f xe.phut" % (h, A))
        print("  I_k = %.4f  ->  I_k+1 = I_k + A_k = %.4f xe.phut" % (I[k], I[k + 1]))

# 2.3: Tải tích lũy tại thời điểm T bất kỳ

def locate(t, T):
    # Tìm khoảng k chứa T, tức là t[k] <= T <= t[k+1] (tìm nhị phân, chỉ so T với các mốc t)
    n = len(t)
    if T <= t[0]:                   # T ở trước hoặc đúng mốc đầu -> khoảng đầu
        return 0
    if T >= t[n - 1]:               # T ở sau hoặc đúng mốc cuối -> khoảng cuối
        return n - 2 
    lo, hi = 0, n - 1               # vùng đang tìm: từ mốc đầu đến mốc cuối
    while hi - lo > 1:              # còn hơn 1 khoảng thì tiếp tục thu hẹp
        mid = (lo + hi) // 2        # mốc ở giữa (// là chia lấy phần nguyên)
        if t[mid] <= T:
            lo = mid                # T nằm bên phải mid
        else:
            hi = mid                # T nằm bên trái mid
    return lo                       # t[lo] <= T < t[lo+1] -> khoảng k = lo


def y_interp(t, y, T):
    # Số xe ỹ(T) tại T: nối thẳng giữa 2 mốc (nội suy tuyến tính từng đoạn)
    k = locate(t, T)
    h = t[k + 1] - t[k]
    return y[k] + (y[k + 1] - y[k]) * (T - t[k]) / h   # y_k + độ dốc * quãng đã đi


def I_of_T(t, y, I, T):
    # Tải tích lũy từ đầu đến T: I(T) = I_k + y_k*s + m*s^2/2
    k = locate(t, T)                                # T nằm trong khoảng k
    s = T - t[k]                                    # quãng đã đi trong khoảng k (phút)
    m = (y[k + 1] - y[k]) / (t[k + 1] - t[k])       # độ dốc đoạn thẳng ỹ trong khoảng k
    return I[k] + y[k] * s + m * s * s / 2.0        # tích lũy đến mốc k + phần hình thang từ t_k đến T


# Thử Phần 2.3: nhập số từ bàn phím
def thu_nhap():
    seg = input("Doan (A/B, Enter = A): ").strip().upper() or "A"          # chọn đoạn
    f = int(input("Muc lam thua f (1/2/4, Enter = 1): ").strip() or 1)     # chọn lưới
    t, y = read_grid(grid_path(seg, "timestamps", f))   # đọc lưới
    check_grid(t, y)                                     # kiểm tra dữ liệu
    I = cumulative(t, y)                                 # tải tích lũy tại các mốc
    print("So moc: %d | T tu %.4f den %.4f phut | I_tot = %.4f xe.phut" % (len(t), t[0], t[-1], I[-1]))
    while True:                                          # lặp: nhập T nhiều lần
        s = input("\nNhap T (phut), Enter de thoat: ").strip()
        if s == "":                                      # bấm Enter không gõ gì -> thoát
            break
        try:
            T = float(s)                                 # đổi chữ -> số
        except ValueError:                               # gõ chữ không phải số
            print("  Hay nhap mot so.")
            continue
        if not (t[0] <= T <= t[-1]):                     # T phải nằm trong đoạn
            print("  T phai nam trong [%.4f, %.4f]" % (t[0], t[-1]))
            continue
        k = locate(t, T)                                 # khoảng chứa T
        iT = I_of_T(t, y, I, T)                          # tải tích lũy đến T
        print("  Khoang k = %d (giua t = %.4f va t = %.4f)" % (k, t[k], t[k + 1]))
        print("  So xe y(T) = %.4f xe" % y_interp(t, y, T))
        print("  Tai I(T)   = %.4f xe.phut (%.2f%% tong)" % (iT, 100 * iT / I[-1]))

 # ==== Phần 3: tìm T bằng chia đôi ================================================
# 3.1: Lập phương trình F(T) = I(T) - Q = 0

def q_levels(total, fractions):
    # Các mức Q = q * I_tot, ví dụ q = 0.25, 0.5, 0.75
    return [f * total for f in fractions]


def F_of_T(t, y, I, Q, T):
    # F(T) = I(T) - Q; F < 0: tải chưa đủ Q, F >= 0: tải đã đủ Q
    return I_of_T(t, y, I, T) - Q


# 3.2: Thuật toán chia đôi

def bisect(t, y, I, Q, tol, max_iter, F=None, in_vong=False):
    # Tìm T trong [t0, tN] sao cho F(T) = 0; trả về T, số vòng, độ rộng khoảng, residual
    if F is None:                                   # mặc định: F(T) = I(T) - Q trên lưới t, y
        def F(T):
            return F_of_T(t, y, I, Q, T)
    a, b = float(t[0]), float(t[-1])                # khoảng ban đầu: cả đoạn
    fa, fb = F(a), F(b)
    if fb < 0.0:                                    # tới cuối đoạn vẫn chưa đủ Q -> vô nghiệm
        raise ValueError("Q = %.6g lon hon tong tich phan %.6g: khong dat duoc" % (Q, fb + Q))
    if fa >= 0.0:                                   # Q <= 0: đạt ngay tại mốc đầu
        return {"T": a, "iters": 0, "width": 0.0, "residual": abs(fa), "a": a, "b": a}
    it = 0                                          # đếm số vòng
    while (b - a) > tol and it < max_iter:          # dừng khi khoảng đủ hẹp hoặc hết số vòng
        m = (a + b) / 2.0                           # điểm giữa
        Fm = F(m)
        if in_vong:                                 # in từng vòng để xem (chỉ dùng khi thử)
            print("  vong %2d: a = %.6f  b = %.6f  m = %.6f  F(m) = %+.6f" % (it + 1, a, b, m, Fm))
        if Fm >= 0.0:
            b = m                                   # tại m đã đủ Q -> nghiệm ở nửa trái
        else:
            a = m                                   # tại m chưa đủ Q -> nghiệm ở nửa phải
        it += 1
    T = (a + b) / 2.0                               # lấy khoang giữa làm T cuối cùng
    return {"T": T, "iters": it, "width": b - a, "residual": abs(F(T)), "a": a, "b": b}


def sci(x, nd=3):
    # Hiển thị kiểu 10^: 3.876e-13 -> "3.876 x 10^-13"
    if x == 0:
        return "0"
    m, e = ("%.*e" % (nd, x)).split("e")
    return "%s x 10^%d" % (m, int(e))


# Thử 3: nhập q -> tìm T bằng chia đôi
def thu_chia_doi():
    cfg = load_config()
    seg = input("Doan (A/B, Enter = A): ").strip().upper() or "A"
    f = int(input("Muc lam thua f (1/2/4, Enter = 1): ").strip() or 1)
    t, y = read_grid(grid_path(seg, "timestamps", f))           # lưới đang xét
    check_grid(t, y)
    I = cumulative(t, y)
    t1, y1 = read_grid(grid_path(seg, "timestamps", 1))         # lưới gốc f1
    tot_goc = float(cumulative(t1, y1)[-1])                     # Q luôn chốt từ lưới gốc
    print("Doan %s, f%d: T tu %.4f den %.4f phut | I_tot luoi nay = %.4f | I_tot goc f1 = %.4f"
          % (seg, f, t[0], t[-1], I[-1], tot_goc))
    while True:
        s = input("\nNhap q (0 < q <= 1, vd 0.5), Enter de thoat: ").strip()
        if s == "":
            break
        try:
            q = float(s)
        except ValueError:
            print("  Hay nhap mot so.")
            continue
        if not (0 < q <= 1):
            print("  q phai nam trong (0, 1].")
            continue
        Q = q * tot_goc
        if Q > I[-1]:
            print("  Q = %.4f lon hon tong tren luoi f%d (%.4f): khong co nghiem." % (Q, f, I[-1]))
            continue
        s = input("  Dung sai tol = 10^? (Enter = -6): ").strip()
        tol = 10.0 ** float(s or -6)
        xem = input("  In tung vong? (c/k, Enter = k): ").strip().lower() == "c"
        r = bisect(t, y, I, Q, tol, cfg["bisection"]["max_iter"], in_vong=xem)
        print("  Q               = %.6f xe.phut" % Q)
        print("  T (chia doi)    = %.9f phut  (khoang k = %d)" % (r["T"], locate(t, r["T"])))
        print("  So vong         = %d" % r["iters"])
        print("  Do rong khoang  = %s phut  (<= tol = %s)" % (sci(r["width"]), sci(tol, 0)))
        print("  Residual |F(T)| = %s xe.phut" % sci(r["residual"]))
        print("  I(T)            = %.6f xe.phut" % I_of_T(t, y, I, r["T"]))

# ==== Phần 4: khảo sát làm thưa lưới và dung sai ====================
# 4.1: Ba chỉ số sai số

def metrics(errs):
    # MAE: trung bình |e|; RMSE: √(trung bình của e²); E_inf: |e| lớn nhất
    n = len(errs)
    mae = sum(abs(e) for e in errs) / n
    rmse = math.sqrt(sum(e * e for e in errs) / n)
    einf = max(abs(e) for e in errs)
    return mae, rmse, einf


# 4.2: Ảnh hưởng của làm thưa lưới (f2, f4 so với lưới gốc f1)

def khao_sat_lam_thua(cfg, seg, kind="timestamps"):
    tol, mx = cfg["bisection"]["tol_minutes"], cfg["bisection"]["max_iter"]
    data = {}
    for f in cfg["thin_factors"]:                           # đọc cả 3 lưới f1, f2, f4
        t, y = read_grid(grid_path(seg, kind, f))
        check_grid(t, y)
        data[f] = (t, y, cumulative(t, y))
    t1, y1, I1 = data[1]
    Qs = q_levels(float(I1[-1]), cfg["q_fractions"])        # Q chốt từ lưới gốc f1
    Tref = [bisect(t1, y1, I1, Q, tol, mx)["T"] for Q in Qs]   # T gốc: f1 với dung sai chính thức 1e-6
    T_thua, sai_so = {}, {}
    for f in cfg["thin_factors"]:
        if f == 1:
            continue                                        # f1 là mốc so sánh, bỏ qua
        t, y, I = data[f]
        Ts = []
        for Q in Qs:
            if Q > I[-1]:                                   # lưới thưa không đạt được Q
                Ts.append(None)
            else:
                Ts.append(bisect(t, y, I, Q, tol, mx)["T"])  # T trên lưới thưa, dung sai chính thức
        T_thua[f] = Ts
        if None not in Ts:
            errs = [T - Tr for T, Tr in zip(Ts, Tref)]      # độ lệch so với T chuẩn (phút)
            sai_so[f] = metrics(errs)                       # (MAE, RMSE, E_inf)
    p = float("nan")                                        # chỉ báo bậc p = log2(E_f4 / E_f2)
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
        Tref = bisect(t, y, I, Q, cfg["bisection"]["tol_minutes"], mx)["T"]   # T gốc: dung sai 1e-6
        for tl in cfg["tol_study_minutes"]:                 # thử 1e-2, 1e-4, 1e-6, 1e-8
            r = bisect(t, y, I, Q, tl, mx)
            ket_qua.append({"q": frac, "tol": tl, "iters": r["iters"], "T": r["T"],
                            "lech": abs(r["T"] - Tref), "residual": r["residual"]})
    return ket_qua


# Thử 4: chọn đoạn -> xem kết quả hai khảo sát
def thu_khao_sat():
    cfg = load_config()
    seg = input("Doan (A/B, Enter = A): ").strip().upper() or "A"
    ls = khao_sat_lam_thua(cfg, seg)
    print("\n(1) Lam thua luoi, doan %s (phut)" % seg)
    for i, frac in enumerate(cfg["q_fractions"]):
        dong = "  q = %.2f: T_f1 = %.4f" % (frac, ls["Tref"][i])
        for f, Ts in ls["T_thua"].items():
            dong += " | T_f%d = %s" % (f, "khong dat" if Ts[i] is None else "%.4f" % Ts[i])
        print(dong)
    for f, (mae, rmse, einf) in ls["sai_so"].items():
        print("  f%d: MAE = %.4f  RMSE = %.4f  E_inf = %.4f" % (f, mae, rmse, einf))
    print("  chi bao p = log2(E_f4 / E_f2) = %.3f (du lieu thuc co nhieu, chi tham khao)" % ls["p"])
    print("\n(2) Dung sai chia doi, doan %s, luoi f1" % seg)
    for r in khao_sat_dung_sai(cfg, seg):
        print("  q = %.2f  tol = %-7g vong = %2d  |T - T_chuan| = %s phut" % (
            r["q"], r["tol"], r["iters"], sci(r["lech"])))

# ==== Phần 5: tổng hợp kết quả, ghi file, chạy chương trình ====
# 5.1: Lập các bảng kết quả cho cả A, B và ghi ra file CSV

def write_csv(name, head, rows):
    # Ghi bảng vào results/<name>: dòng đầu là tên cột, các dòng sau là số liệu
    with open(results_dir() / name, "w", newline="", encoding="utf-8-sig") as fh:
        w = csv.writer(fh)
        w.writerow(head)
        w.writerows(rows)


def lap_bang(cfg):
    # Gọi lại các hàm Phần 2-4 cho mọi đoạn, lưới, mức q; trả về 4 bảng (tên cột, các dòng)
    tol, mx = cfg["bisection"]["tol_minutes"], cfg["bisection"]["max_iter"]
    qs = cfg["q_fractions"]
    tp, cd, ls, ds = [], [], [], []
    for seg in cfg["segments"]:
        for kind in cfg["base_grids"]:
            Qs = None
            for f in cfg["thin_factors"]:                       # (a) tích phân và (b) chia đôi
                t, y = read_grid(grid_path(seg, kind, f))
                check_grid(t, y)
                I = cumulative(t, y)
                total, cover = float(I[-1]), float(t[-1] - t[0])
                if f == 1:
                    Qs = q_levels(total, qs)                    # Q chốt từ lưới gốc f1
                tp.append([seg, kind, "f%d" % f, len(t), "%.9f" % cover, "%.9f" % total,
                           "%.9f" % (total / cover)] + ["%.9f" % Q for Q in Qs])
                for frac, Q in zip(qs, Qs):
                    r = bisect(t, y, I, Q, tol, mx)
                    cd.append([seg, kind, "f%d" % f, "%d%%" % round(100 * frac), "%.9f" % Q,
                               "%.9f" % r["T"], r["iters"], "%.3e" % r["width"],
                               "%.3e" % r["residual"], "%.9f" % I_of_T(t, y, I, r["T"])])
            k = khao_sat_lam_thua(cfg, seg, kind)               # (c) làm thưa lưới
            for f, (mae, rmse, einf) in k["sai_so"].items():
                ls.append([seg, kind, "f%d" % f, "%.4f" % mae, "%.4f" % rmse, "%.4f" % einf, ""])
            ls.append([seg, kind, "chi_bao_p", "", "", "", "%.3f" % k["p"]])
            for r in khao_sat_dung_sai(cfg, seg, kind):         # (d) dung sai
                q_pt = "%d%%" % round(100 * r["q"])
                ds.append([seg, kind, q_pt, "%g" % r["tol"], r["iters"], "%.9f" % r["T"],
                           "%.3e" % r["lech"], "%.3e" % r["residual"]])
    return {
        "integral_summary.csv": (["segment", "grid", "thin", "n_moc", "thoi_gian_phu_phut", "tong_I_xe_phut",
                                  "trung_binh_xe"] + ["Q%d%%_xe_phut" % round(100 * q) for q in qs], tp),
        "bisection_results.csv": (["segment", "grid", "thin", "Q_phan_tram", "Q_xe_phut", "T_phut_tu_dau_doan",
                                   "so_vong", "do_rong_khoang_phut", "residual_xe_phut", "I(T)_xe_phut"], cd),
        "sampling_summary.csv": (["segment", "grid", "thin", "MAE_phut", "RMSE_phut", "Einf_phut",
                                  "chi_bao_p"], ls),
        "tolerance_study.csv": (["segment", "grid", "Q_phan_tram", "tol_phut", "so_vong", "T_phut",
                                 "|T - T(tol chinh thuc)|_phut", "residual_xe_phut"], ds),
    }


def ghi_ket_qua(bang):
    # Ghi từng bảng ra file CSV trong thư mục results
    for ten, (head, rows) in bang.items():
        write_csv(ten, head, rows)
        print("Da ghi results/%s (%d dong)" % (ten, len(rows)))

# 5.2: In ra terminal các bảng kết quả (tích phân, chia đôi, làm thưa, dung sai)
#    cfg = load_config()                                                                                                                                        
#    bang = lap_bang(cfg)                                                                                                                                       
#    ghi_ket_qua(bang)

def in_bang(bang, cfg):
    tol = cfg["bisection"]["tol_minutes"]
    _, tp = bang["integral_summary.csv"]
    print("\n== (1) TICH PHAN: tong tai moi luoi ==")
    print("%-4s %-4s %5s %12s %14s %10s" % ("Doan", "Luoi", "Moc", "Phu(phut)", "I_tot(xe.ph)", "TB(xe)"))
    for r in tp:
        print("%-4s %-4s %5s %12.4f %14.4f %10.4f" % (r[0], r[2], r[3], float(r[4]), float(r[5]), float(r[6])))

    _, cd = bang["bisection_results.csv"]
    print("\n== (2) CHIA DOI: thoi diem T (tol = %g phut) ==" % tol)
    print("%-4s %-4s %-4s %12s %6s %12s" % ("Doan", "Luoi", "q", "T(phut)", "Vong", "Residual"))
    for r in cd:
        print("%-4s %-4s %-4s %12.6f %6s %12s" % (r[0], r[2], r[3], float(r[5]), r[6], r[8]))

    _, ls = bang["sampling_summary.csv"]
    print("\n== (3) LAM THUA LUOI: do lech T so voi luoi goc f1 (phut) ==")
    print("%-4s %-10s %9s %9s %9s %8s" % ("Doan", "Luoi", "MAE", "RMSE", "E_inf", "p"))
    for r in ls:
        print("%-4s %-10s %9s %9s %9s %8s" % (r[0], r[2], r[3], r[4], r[5], r[6]))

    _, ds = bang["tolerance_study.csv"]
    print("\n== (4) DUNG SAI: |T(tol) - T(%g)| tren luoi f1 (phut) ==" % tol)
    print("%-4s %-4s %8s %6s %12s" % ("Doan", "q", "tol", "Vong", "Do lech"))
    for r in ds:
        print("%-4s %-4s %8s %6s %12s" % (r[0], r[2], r[3], r[4], r[6]))

    # So sánh: biến động lớn nhất do lấy mẫu với biến động do dung sai chính thức
    lay_mau = max(float(r[5]) for r in ls if r[2] != "chi_bao_p")
    min_hon = [float(r[6]) for r in ds if float(r[3]) < tol]       # các mức mịn hơn tol chính thức
    dung_sai = max(min_hon) if min_hon else tol / 2                 # không có thì dùng cận tol/2
    print("\n== SO SANH (Buoc 5) ==")
    print("Bien dong do LAY MAU (E_inf lon nhat)       = %.4f phut" % lay_mau)
    print("Bien dong do DUNG SAI chinh thuc (tol = %g) = %s phut" % (tol, sci(dung_sai)))
    if lay_mau > 10 * dung_sai:
        print("=> Bien dong do lay mau lon hon rat nhieu: do tin cay cua T bi gioi han boi mat do anh,")
        print("   khong phai boi thuat toan chia doi.")
    else:
        print("=> Hai nguon bien dong cung bac, can xem them.")
    print("Luu y: nhan la prelabel -> ket qua SO BO; chi bao p tren du lieu co nhieu chi de tham khao.")

# 5.3: Menu tính riêng (gom các hàm thử của Phần 2-4)

def menu():
    lua_chon = {
        "1": ("Xem hinh thang cua khoang k", thu_tich_phan),
        "2": ("Tinh tai tich luy I(T) tai T bat ky", thu_nhap),
        "3": ("Tim T theo q bang chia doi", thu_chia_doi),
        "4": ("Xem khao sat lam thua va dung sai cua mot doan", thu_khao_sat),
    }
    while True:
        print("\n=== TINH RIENG (De 20) ===")
        for so, (ten, _) in lua_chon.items():
            print("%s) %s" % (so, ten))
        print("0) Thoat")
        c = input("Chon: ").strip()
        if c == "0":
            break
        if c not in lua_chon:
            print("Hay chon 0-%d." % len(lua_chon))
            continue
        try:
            lua_chon[c][1]()                        # gọi hàm thử tương ứng
        except (ValueError, OSError) as e:          # nhập sai hoặc không có file lưới
            print("Loi:", e)

# 5.4: Chương trình chính

def main():
    ap = argparse.ArgumentParser(description="De 20: thoi diem dat chi so tai tich luy")
    ap.add_argument("--het", action="store_true", help="chay het mo hinh, khong hoi")
    ap.add_argument("--demo", action="store_true", help="mo menu tinh rieng, khong hoi")
    args = ap.parse_args()
    cfg = load_config()
    if args.het:
        c = "1"
    elif args.demo:
        c = "2"
    else:                               # bấm ▷ hoặc chạy không kèm gì -> hỏi
        print("=== DE 20 ===\n1) Chay het mo hinh (ghi file + in ket qua)\n2) Tinh rieng (menu thu)"
              "\n3) Kiem chung y = 1 + t\n0) Thoat")
        c = input("Chon: ").strip()
    if c == "1":
        bang = lap_bang(cfg)            # tính cho A, B
        ghi_ket_qua(bang)               # ghi 4 file CSV
        in_bang(bang, cfg)              # in bảng và dòng so sánh
    elif c == "2":
        menu()
    elif c == "3":
        import sys
        sys.path.insert(0, str(ROOT / "src"))           # cho Python tìm thấy kiem_chung.py trong src
        from kiem_chung import kiem_chung, kiem_chung_lam_thua   # chỉ nạp khi chọn mục này
        kiem_chung(cfg)
        kiem_chung_lam_thua(cfg)


if __name__ == "__main__":
    main()