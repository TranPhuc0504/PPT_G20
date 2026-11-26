"""Level 2 - Đối chứng thư viện (Đề 20): so kết quả code TỰ VIẾT với hàm chuẩn của thư viện Python.

Chạy từ thư mục gốc:
  python src\\doi_chung_thu_vien.py          -> menu nhập số (1 chạy hết, 2-4 thử từng phép so)
  python src\\doi_chung_thu_vien.py --het    -> chạy hết, không hỏi (main.py gọi kiểu này)

Ghi: results/library_check.csv (77 phép so, xếp theo 5 mục, mỗi mục có dòng tổng hợp)

Cần: numpy và scipy (python -m pip install numpy scipy). Thiếu scipy thì dừng và báo cách cài.
File này là file DUY NHẤT được gọi hàm tính của thư viện, và CHỈ để so sánh; mọi kết quả chính vẫn
lấy từ code tự viết trong mo_hinh.py (cumulative, I_of_T, bisect).

Năm mục so (trên lưới f1, f2, f4 của đoạn A, B và trên hàm kiểm chứng y = 1 + t):
  1. Tổng tải I_tot      : cumulative()[-1]  <-> numpy.trapezoid(y, t)
  2. Dãy tích lũy I_k    : cumulative()      <-> scipy.integrate.cumulative_trapezoid (so mọi mốc, ghi mốc lệch nhất)
  3. I(T) tại T          : I_of_T(T)         <-> numpy.interp + numpy.trapezoid
  4. Nghiệm T (đúng)     : bisect(), T = b   <-> nghiệm đúng: I(T) bậc 2 trên khoảng chứa nghiệm, giải bằng numpy.roots
  5. Nghiệm T (chia đôi) : bisect(), T = b   <-> scipy.optimize.bisect (CÙNG thuật toán, cùng tol)
"""
import argparse
import sys

import numpy as np

from mo_hinh import DTYPE, I_of_T, bisect, cumulative, grid_path, load_config, q_levels, read_grid, write_csv

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

NGUONG_TICH_PHAN = 1e-9      # xe·phút: chênh lệch cho phép giữa hai cách tính tích phân (chỉ do làm tròn)
KC = "Kiểm chứng y=1+t"      # tên "đoạn" của hàm kiểm chứng
MUC = [("1", "Tổng tải I_tot", "cumulative()[-1]", "numpy.trapezoid", "xe·phút"),
       ("2", "Dãy tích lũy I_k (mốc có sai số lớn nhất)", "cumulative()", "scipy.integrate.cumulative_trapezoid", "xe·phút"),
       ("3", "Tải I(T) tại T", "I_of_T()", "numpy.interp + trapezoid", "xe·phút"),
       ("4", "Nghiệm T so với nghiệm đúng", "bisect(), T = b", "numpy.searchsorted + roots", "phút"),
       ("5", "Nghiệm T so với chia đôi thư viện", "bisect(), T = b", "scipy.optimize.bisect (cùng tol)", "phút")]


# ==== Phần 1: các phép tính bằng THƯ VIỆN (đuôi _tv) ====

def trapezoid_tv(y, t):
    # numpy >= 2.0 có trapezoid; bản cũ chỉ có trapz
    f = getattr(np, "trapezoid", None) or getattr(np, "trapz")
    return float(f(y, t))


def tich_luy_tv(t, y):
    # Dãy tích lũy bằng phép toán mảng của numpy: diện tích từng hình thang rồi cộng dồn, thêm I_0 = 0
    return np.concatenate(([0.0], np.cumsum(np.diff(t) * (y[:-1] + y[1:]) / 2.0)))


def I_T_tv(t, y, T):
    # I(T): các mốc t_k < T, thêm điểm T với ỹ(T) = numpy.interp, rồi numpy.trapezoid
    m = t < T
    tt = np.append(t[m], T)
    yy = np.append(y[m], np.interp(T, t, y))
    return trapezoid_tv(yy, tt)


def T_dung_tv(t, y, Q):
    # Nghiệm đúng của I(T) = Q: khoảng k có I_k < Q <= I_k+1 (numpy.searchsorted);
    # trong khoảng đó I(t_k + s) = I_k + y_k·s + (m/2)·s² -> giải (m/2)s² + y_k s + (I_k − Q) = 0 bằng numpy.roots
    I = tich_luy_tv(t, y)
    k = int(np.searchsorted(I, Q, side="left")) - 1
    k = min(max(k, 0), len(t) - 2)
    h = t[k + 1] - t[k]
    m = (y[k + 1] - y[k]) / h
    r = np.roots([m / 2.0, y[k], I[k] - Q]) if m != 0 else np.array([(Q - I[k]) / y[k]])
    s = [float(x.real) for x in np.atleast_1d(r) if abs(x.imag) < 1e-12 and -1e-12 <= x.real <= h + 1e-12]
    return float(t[k]) + min(s)                                  # nghiệm sớm nhất trong khoảng


def nap_scipy():
    # scipy là thư viện BẮT BUỘC cho file đối chứng: thiếu thì dừng và chỉ cách cài
    try:
        from scipy.integrate import cumulative_trapezoid  # type: ignore
        from scipy.optimize import bisect as bisect_sp  # type: ignore
    except ImportError:
        sys.exit("Thiếu scipy cho bước đối chứng thư viện. Cài: python -m pip install scipy")
    return cumulative_trapezoid, bisect_sp


# ==== Phần 2: tiện ích ====

def cuc_nho(x, nguong=1e-12):
    # Chênh lệch nhỏ hơn mức làm tròn ghi là "< 1e-12" để file kết quả giống nhau trên mọi máy
    return "< %.0e" % nguong if abs(x) < nguong else "%.3e" % abs(x)


def ds_luoi(cfg):
    # 7 bộ dữ liệu: A, B x f1, f2, f4 và hàm kiểm chứng y = 1 + t
    out = []
    for seg in cfg["segments"]:
        for f in cfg["thin_factors"]:
            t, y = read_grid(grid_path(seg, "timestamps", f))
            out.append((seg, "f%d" % f, t, y))
    n = cfg["verification"]["n_intervals_linear"]
    tk = np.array([i / n for i in range(n + 1)], dtype=DTYPE)
    out.append((KC, "%d khoảng" % n, tk, 1.0 + tk))
    return out


def cac_muc_Q(cfg, seg, I):
    # (tên mức, Q): dữ liệu thật dùng 25/50/75% I_tot; hàm kiểm chứng dùng Q cố định trong config
    if seg == KC:
        return [("Q=%g" % q, q) for q in cfg["verification"]["q_values"]]
    return [("%d%%" % round(100 * q), Q) for q, Q in zip(cfg["q_fractions"], q_levels(float(I[-1]), cfg["q_fractions"]))]


# ==== Phần 3: chạy hết 77 phép so, ghi CSV (numpy) ====

def so_sanh(cfg):
    cumtrapz, bisect_sp = nap_scipy()
    tol, mx = cfg["bisection"]["tol_minutes"], cfg["bisection"]["max_iter"]
    theo_muc = {m[0]: [] for m in MUC}           # gom dòng theo mục 1-5 để bảng dễ đọc

    def ghi(muc, doan, luoi, muc_q, tu_viet, thu_vien, lech, nguong):
        theo_muc[muc].append({"doan": doan, "luoi": luoi, "q": muc_q, "tv": tu_viet, "lib": thu_vien,
                              "lech": abs(lech), "nguong": nguong, "ok": abs(lech) <= nguong})

    for seg, luoi, t, y in ds_luoi(cfg):
        I = cumulative(t, y)                                       # TỰ VIẾT
        tong_tv = trapezoid_tv(y, t)                               # THƯ VIỆN
        ghi("1", seg, luoi, "", "%.9f" % I[-1], "%.9f" % tong_tv, float(I[-1]) - tong_tv, NGUONG_TICH_PHAN)
        I_sp = cumtrapz(y, t, initial=0.0)                         # THƯ VIỆN: cả dãy tích lũy
        lech = np.abs(I - I_sp)
        k = int(np.argmax(lech))                                   # mốc có sai số lớn nhất (mốc đầu nếu bằng nhau)
        if lech[k] == 0.0:
            ghi("2", seg, luoi, "", "%d mốc, khớp tuyệt đối" % len(t), "%d mốc" % len(t), 0.0, NGUONG_TICH_PHAN)
        else:
            ghi("2", seg, luoi, "mốc k=%d" % k, "%.9f" % I[k], "%.9f" % I_sp[k], float(lech[k]), NGUONG_TICH_PHAN)
        for ten_q, Q in cac_muc_Q(cfg, seg, I):
            T = bisect(t, y, I, Q, tol, mx)["T"]                   # TỰ VIẾT: chia đôi, T = b
            iT, iT_tv = I_of_T(t, y, I, T), I_T_tv(t, y, T)
            ghi("3", seg, luoi, ten_q, "%.9f" % iT, "%.9f" % iT_tv, iT - iT_tv, NGUONG_TICH_PHAN)
            Td = T_dung_tv(t, y, Q)                                # nghiệm đúng
            ghi("4", seg, luoi, ten_q, "%.9f" % T, "%.9f" % Td, T - Td, tol / 2.0)
            F = lambda x, Q=Q, t=t, y=y: I_T_tv(t, y, x) - Q
            Tc = bisect_sp(F, float(t[0]), float(t[-1]), xtol=tol, maxiter=mx)
            ghi("5", seg, luoi, ten_q, "%.9f" % T, "%.9f" % Tc, T - Tc, tol)        # hai cách chia đôi lệch nhau <= tol

    H = ["STT", "Mục", "Đại lượng", "Đoạn", "Lưới", "Mức Q / mốc", "Hàm tự viết", "Hàm thư viện",
         "Giá trị tự viết", "Giá trị thư viện", "|Chênh lệch|", "Ngưỡng", "Đơn vị", "Kết quả"]
    rows, stt, tong = [], 0, []
    for so, ten, ham_tv, ham_lib, dvi in MUC:
        ds = theo_muc[so]
        for d in ds:
            stt += 1
            rows.append([stt, so, ten, d["doan"], d["luoi"], d["q"], ham_tv, ham_lib, d["tv"], d["lib"],
                         cuc_nho(d["lech"]), "%g" % d["nguong"], dvi, "ĐẠT" if d["ok"] else "KHÔNG ĐẠT"])
        lon = max(d["lech"] for d in ds)
        dat = sum(d["ok"] for d in ds)
        rows.append(["", so, "tổng hợp mục %s" % so, "", "", "", ham_tv, ham_lib, "%d phép so" % len(ds),
                     "%d/%d ĐẠT" % (dat, len(ds)), cuc_nho(lon), "%g" % ds[0]["nguong"], dvi,
                     "ĐẠT" if dat == len(ds) else "KHÔNG ĐẠT"])
        tong.append((so, ten, len(ds), dat, lon, ds[0]["nguong"], dvi))
    write_csv("library_check.csv", H, rows)
    return tong


def in_tong_hop(tong):
    print("\n== ĐỐI CHỨNG THƯ VIỆN (Level 2): tóm tắt theo mục ==")
    print("%-4s %-42s %8s %10s %14s %10s" % ("Mục", "Đại lượng", "Số phép", "Đạt", "Lệch lớn nhất", "Ngưỡng"))
    for so, ten, n, dat, lon, ng, dvi in tong:
        print("%-4s %-42s %8d %10s %14s %10s  %s" % (so, ten, n, "%d/%d" % (dat, n), cuc_nho(lon), "%g" % ng, dvi))
    n_all, d_all = sum(x[2] for x in tong), sum(x[3] for x in tong)
    print("KẾT LUẬN: %s (%d/%d phép so)" % ("ĐẠT" if n_all == d_all else "KHÔNG ĐẠT", d_all, n_all))
    print("Đã ghi results/library_check.csv")
    return n_all == d_all


# ==== Phần 4: chạy hết ====

def chay_het(cfg):
    return in_tong_hop(so_sanh(cfg))


# ==== Phần 5: menu nhập số (thử từng phép so) ====

def chon_bo(cfg):
    ds = ds_luoi(cfg)
    print("Chọn bộ dữ liệu:")
    for i, (seg, luoi, t, y) in enumerate(ds, 1):
        print("  %d) %s, %s (%d mốc)" % (i, seg, luoi, len(t)))
    s = input("Số (Enter = 1): ").strip() or "1"
    if not s.isdigit() or not 1 <= int(s) <= len(ds):
        raise ValueError("chọn từ 1 đến %d" % len(ds))
    return ds[int(s) - 1]


def thu_tich_phan(cfg):
    seg, luoi, t, y = chon_bo(cfg)
    cumtrapz, _, _ = nap_scipy()
    I, I_tv = cumulative(t, y), cumtrapz(y, t, initial=0.0)
    lech = np.abs(I - I_tv)
    k = int(np.argmax(lech))
    print("\n%s, %s: %d mốc" % (seg, luoi, len(t)))
    print("  Tổng tải  tự viết cumulative()[-1] = %.9f | numpy.trapezoid = %.9f | lệch %s xe·phút"
          % (I[-1], trapezoid_tv(y, t), cuc_nho(float(I[-1]) - trapezoid_tv(y, t))))
    print("  Dãy I_k   mốc có sai số lớn nhất k = %d: tự viết %.9f | scipy cumulative_trapezoid %.9f | lệch %s xe·phút"
          % (k, I[k], I_tv[k], cuc_nho(float(lech[k]))))


def thu_I_T(cfg):
    seg, luoi, t, y = chon_bo(cfg)
    I = cumulative(t, y)
    while True:
        s = input("\nNhập T trong [%.4f, %.4f] phút (Enter để quay lại): " % (t[0], t[-1])).strip()
        if s == "":
            break
        try:
            T = float(s)
        except ValueError:
            print("  Hãy nhập một số.")
            continue
        if not t[0] <= T <= t[-1]:
            print("  T phải nằm trong đoạn.")
            continue
        a, b = I_of_T(t, y, I, T), I_T_tv(t, y, T)
        print("  ỹ(T) numpy.interp = %.6f xe" % np.interp(T, t, y))
        print("  I(T) tự viết I_of_T() = %.9f | numpy interp+trapezoid = %.9f | lệch %s xe·phút" % (a, b, cuc_nho(a - b)))


def thu_nghiem(cfg):
    seg, luoi, t, y = chon_bo(cfg)
    I = cumulative(t, y)
    mx = cfg["bisection"]["max_iter"]
    _, bisect_sp = nap_scipy()
    while True:
        hoi = "q trong (0, 1]" if seg != KC else "Q trong (0, %.4g]" % I[-1]
        s = input("\nNhập %s (Enter để quay lại): " % hoi).strip()
        if s == "":
            break
        try:
            v = float(s)
        except ValueError:
            print("  Hãy nhập một số.")
            continue
        Q = v * float(I[-1]) if seg != KC else v
        if not 0 < Q <= I[-1]:
            print("  Q phải nằm trong (0, I_tot].")
            continue
        s = input("  Dung sai tol = 10^? (Enter = -6): ").strip()
        try:
            tol = 10.0 ** float(s or -6)
        except ValueError:
            print("  Hãy nhập số mũ, ví dụ -6.")
            continue
        r = bisect(t, y, I, Q, tol, mx)
        Td = T_dung_tv(t, y, Q)
        print("  Q = %.6f xe·phút, tol = %g phút" % (Q, tol))
        print("  %-36s %18s %14s" % ("Cách tìm", "T (phút)", "Lệch T tự viết"))
        print("  %-36s %18.12f %14s   (%d vòng)" % ("Tự viết: bisect(), T = b", r["T"], "", r["iters"]))
        print("  %-36s %18.12f %14.3e   (nghiệm đúng)" % ("numpy: searchsorted + roots", Td, abs(r["T"] - Td)))
        F = lambda x: I_T_tv(t, y, x) - Q
        Tc = bisect_sp(F, float(t[0]), float(t[-1]), xtol=tol, maxiter=mx)
        print("  %-36s %18.12f %14.3e" % ("scipy.optimize.bisect (cùng tol)", Tc, abs(r["T"] - Tc)))
        print("  Cận lý thuyết |T − T*| <= tol/2 = %g phút: %s" % (tol / 2, "ĐẠT" if abs(r["T"] - Td) <= tol / 2 else "KHÔNG ĐẠT"))


def menu(cfg):
    lua_chon = {
        "1": ("Chạy hết đối chứng (ghi results/library_check.csv)", lambda: chay_het(cfg)),
        "2": ("So tích phân: tổng tải và dãy tích lũy của một bộ dữ liệu", lambda: thu_tich_phan(cfg)),
        "3": ("So tải I(T) tại một T tự nhập", lambda: thu_I_T(cfg)),
        "4": ("So nghiệm T theo q tự nhập (tự viết, numpy, scipy)", lambda: thu_nghiem(cfg)),
    }
    while True:
        print("\n=== ĐỐI CHỨNG THƯ VIỆN (Level 2) ===")
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
        except (ValueError, OSError) as e:
            print("Lỗi:", e)


def main():
    ap = argparse.ArgumentParser(description="Level 2: đối chứng code tự viết với thư viện")
    ap.add_argument("--het", action="store_true", help="chạy hết, không hỏi")
    a = ap.parse_args()
    cfg = load_config()
    if a.het or not sys.stdin.isatty():          # main.py / chạy tự động: không hỏi
        if not chay_het(cfg):
            sys.exit(1)
    else:
        menu(cfg)


if __name__ == "__main__":
    main()