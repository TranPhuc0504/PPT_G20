"""Mở rộng (Đề 20): tìm T bằng Newton có bảo vệ (fallback về chia đôi) và so sánh với chia đôi.

Chạy: python src\\newton.py
  1) results/newton_kiem_chung.csv : kiểm chứng y = 1 + t (biết T*): vòng, sai số, residual; MAE, RMSE, E∞
  2) results/newton_bac_hoi_tu.csv : sai số theo từng vòng và bậc hội tụ thực nghiệm của hai phương pháp
  3) results/newton_compare.csv    : dữ liệu A/B (f1, f2, f4): sai số T so với T chuẩn, residual; MAE, RMSE, E∞
  4) results/newton_diem_dau.csv   : so sánh cách chọn điểm đầu T0 của Newton
Cần chạy chuan_bi_du_lieu.py trước (để có các file lưới).
"""
import math

import numpy as np

from mo_hinh import (DTYPE, I_of_T, bisect, cumulative, grid_path, load_config, metrics, q_levels,
                     read_grid, write_csv, y_interp)

Y_MIN = 1e-12        # ỹ(T) nhỏ hơn mức này coi như bằng 0 -> không chia được, phải fallback
E_SAN = 1e-14        # sai số nhỏ hơn mức này là chạm làm tròn máy -> không dùng để ước lượng bậc
TOL_CHUAN = 1e-12    # dung sai rất nhỏ để lấy T chuẩn bằng chia đôi (dữ liệu thật không có T*)
CD, NT = "Chia đôi", "Newton"


def T_dung(Q):
    # Nghiệm đúng của bài kiểm chứng y = 1 + t: T* = -1 + sqrt(1 + 2Q), viết dạng ổn định
    return 2.0 * Q / (1.0 + math.sqrt(1.0 + 2.0 * Q))


def luoi_kiem_chung(cfg):
    # Lưới kiểm chứng: y = 1 + t trên [0, 1], n khoảng đều
    n = cfg["verification"]["n_intervals_linear"]
    t = np.array([i / n for i in range(n + 1)], dtype=DTYPE)
    y = 1.0 + t
    return t, y, cumulative(t, y)


# ==== 1. Thuật toán Newton có bảo vệ ====

def newton_bao_ve(t, y, I, Q, tol, max_iter, T0=None, lich_su=None):
    # Newton: T_moi = T - (I(T) - Q) / ỹ(T); giữ khoảng [a, b] chứa nghiệm như chia đôi.
    # Bước Newton không dùng được (ỹ ~ 0 hoặc nhảy ra ngoài [a, b]) -> dùng điểm giữa (fallback), đếm lại.
    # lich_su: nếu truyền vào một danh sách, ghi lại T ở vòng 0 và sau mỗi vòng (để tính bậc hội tụ)
    a, b = float(t[0]), float(t[-1])
    if I_of_T(t, y, I, b) - Q < 0:
        raise ValueError("Q lớn hơn tổng tích phân: không đạt được")
    if T0 is None:
        T = a + (b - a) * Q / float(I[-1])       # đoán ban đầu: tải tăng đều theo thời gian
    else:
        T = float(T0)                            # điểm đầu do người gọi chọn
    it, fallback = 0, 0
    if lich_su is not None:
        lich_su.append(T)                        # vòng 0: điểm đầu
    while it < max_iter:
        F = I_of_T(t, y, I, T) - Q
        if F == 0.0:                             # trúng đúng nghiệm -> dừng ngay
            break
        if F > 0:                                # cập nhật khoảng chứa nghiệm theo dấu F
            b = T
        else:
            a = T
        d = y_interp(t, y, T)                    # đạo hàm F'(T) = ỹ(T) (số xe tại T)
        T_moi = T - F / d if d > Y_MIN else None # bước Newton
        if T_moi is None or not (a <= T_moi <= b):
            T_moi = (a + b) / 2.0                # FALLBACK: bước Newton hỏng -> lấy điểm giữa
            fallback += 1
        it += 1
        if lich_su is not None:
            lich_su.append(T_moi)
        if abs(T_moi - T) <= tol:                # bước đi đã nhỏ hơn dung sai -> dừng
            T = T_moi
            break
        T = T_moi
    # residual có dấu: Newton KHÔNG bảo đảm F(T) >= 0 như chia đôi (lấy b), nhưng |F(T)| rất nhỏ
    return {"T": T, "iters": it, "fallback": fallback, "residual": I_of_T(t, y, I, T) - Q}


# ==== 2. Kiểm chứng y = 1 + t: sai số, residual, MAE, RMSE, E∞ của hai phương pháp ====

def kiem_chung_newton(cfg):
    v, mx = cfg["verification"], cfg["bisection"]["max_iter"]
    t, y, I = luoi_kiem_chung(cfg)
    rows = []
    print("== (1) Kiểm chứng y = 1 + t: so với nghiệm đúng T* ==")
    print("%-7s %-9s %6s %11s %11s %11s" % ("tol", "Phương pháp", "Vòng", "MAE", "RMSE", "E∞"))
    for tol in v["tol_minutes_list"]:
        sai_so = {CD: [], NT: []}
        for Q in v["q_values"]:
            Te = T_dung(Q)
            rb = bisect(t, y, I, Q, tol, mx)
            rn = newton_bao_ve(t, y, I, Q, tol, mx)
            for ten, r, fb in ((CD, rb, ""), (NT, rn, rn["fallback"])):
                e = r["T"] - Te
                sai_so[ten].append(e)
                rows.append(["%g" % tol, Q, ten, r["iters"], fb, "%.15f" % Te, "%.15f" % r["T"],
                             "%.3e" % abs(e), "%.3e" % r["residual"], "", "", ""])
        for ten in (CD, NT):
            mae, rmse, einf = metrics(sai_so[ten])
            vong = [r[3] for r in rows if r[0] == "%g" % tol and r[2] == ten]
            rows.append(["%g" % tol, "tổng hợp", ten, "", "", "", "", "", "",
                         "%.3e" % mae, "%.3e" % rmse, "%.3e" % einf])
            print("%-7g %-9s %6s %11s %11s %11s" % (tol, ten, "%d-%d" % (min(vong), max(vong)),
                                                   "%.3e" % mae, "%.3e" % rmse, "%.3e" % einf))
    write_csv("newton_kiem_chung.csv",
              ["tol (phút)", "Q (xe·phút)", "Phương pháp", "Số vòng", "Số lần fallback", "T* đúng (phút)",
               "T (phút)", "|T − T*| (phút)", "Residual F(T) (xe·phút)", "MAE (phút)", "RMSE (phút)",
               "E∞ (phút)"], rows)
    print("Đã ghi results/newton_kiem_chung.csv")


# ==== 3. Bậc hội tụ thực nghiệm: sai số theo từng vòng (y = 1 + t, Q giữa) ====

def bac_hoi_tu(cfg):
    t, y, I = luoi_kiem_chung(cfg)
    qv = cfg["verification"]["q_values"]
    Q = qv[len(qv) // 2]                                   # mức Q ở giữa (0,75)
    Te = T_dung(Q)
    # Chia đôi: chạy lần lượt 1, 2, ..., 40 vòng (tol = 0 để không dừng sớm), lấy T = b sau mỗi vòng
    T_cd = [bisect(t, y, I, Q, 0.0, n)["T"] for n in range(1, 41)]
    # Newton: ghi lại T ở vòng 0 (điểm đầu) và sau mỗi vòng
    T_nt = []
    newton_bao_ve(t, y, I, Q, 0.0, 40, lich_su=T_nt)
    rows, ket_luan = [], {}
    for ten, Ts, vong0 in ((CD, T_cd, 1), (NT, T_nt, 0)):
        e = [abs(T - Te) for T in Ts]                    # sai số sau mỗi vòng
        p_list, ti_so = [], []
        for n in range(len(e)):
            ts = e[n] / e[n - 1] if n >= 1 and e[n - 1] > 0 else None             # tỉ số e_n / e_(n-1)
            if ts is not None and e[n] > E_SAN and e[n - 1] > E_SAN:
                ti_so.append(ts)
            p = None
            # p_n chỉ tính cho Newton: với chia đôi lấy T = b, có vòng b đứng yên (chỉ a dịch) nên e_n = e_(n-1),
            # công thức chia cho ln(1) = 0; bậc của chia đôi đọc qua tỉ số trung bình (~0,5 -> bậc 1)
            if ten == NT and n >= 2 and min(e[n], e[n - 1], e[n - 2]) > E_SAN and e[n - 1] != e[n - 2]:
                p = math.log(e[n] / e[n - 1]) / math.log(e[n - 1] / e[n - 2])  # p_n = ln(e_n/e_n-1) / ln(e_n-1/e_n-2)
                p_list.append(p)
            rows.append([ten, n + vong0, "%.15f" % Ts[n], "%.3e" % e[n],
                         "" if ts is None else "%.4f" % ts, "" if p is None else "%.3f" % p])
        cham = next((n + vong0 for n in range(len(e)) if e[n] <= E_SAN), None)   # vòng đầu tiên chạm làm tròn
        ket_luan[ten] = (p_list, ti_so, cham)
    write_csv("newton_bac_hoi_tu.csv", ["Phương pháp", "Vòng", "T (phút)", "e_n = |T_n − T*| (phút)",
                                        "Tỉ số e_n / e_(n−1)", "Bậc p_n"], rows)
    print("\n== (2) Bậc hội tụ thực nghiệm (y = 1 + t, Q = %g, T* = %.12f) ==" % (Q, Te))
    _, ts_cd, _ = ket_luan[CD]
    tb_ts = math.exp(sum(math.log(x) for x in ts_cd) / len(ts_cd))          # trung bình nhân của tỉ số
    print("Chia đôi: tỉ số e_n/e_(n−1) trung bình = %.3f (lý thuyết 0,5) -> hội tụ tuyến tính, bậc 1" % tb_ts)
    p_nt, _, cham = ket_luan[NT]
    print("Newton  : p_n = %s (lý thuyết 2) -> bậc 2; sai số chạm mức làm tròn máy ở vòng %s" % (
        ", ".join("%.2f" % p for p in p_nt), cham))
    print("Đã ghi results/newton_bac_hoi_tu.csv")


# ==== 4. Dữ liệu A/B: sai số T (so với T chuẩn), residual, số vòng của hai phương pháp ====

def so_sanh_du_lieu(cfg):
    tol, mx = cfg["bisection"]["tol_minutes"], cfg["bisection"]["max_iter"]
    rows = []
    for seg in cfg["segments"]:
        t1, y1 = read_grid(grid_path(seg, "timestamps", 1))
        Qs = q_levels(float(cumulative(t1, y1)[-1]), cfg["q_fractions"])    # Q chốt từ f1
        for f in cfg["thin_factors"]:
            t, y = read_grid(grid_path(seg, "timestamps", f))
            I = cumulative(t, y)
            ss = {CD: [], NT: []}                                           # sai số T của lưới này
            for frac, Q in zip(cfg["q_fractions"], Qs):
                if Q > I[-1]:
                    continue                     # lưới thưa không đạt được Q
                Tc = bisect(t, y, I, Q, TOL_CHUAN, 200)["T"]                # T chuẩn trên cùng lưới
                rb, rn = bisect(t, y, I, Q, tol, mx), newton_bao_ve(t, y, I, Q, tol, mx)
                for ten, r in ((CD, rb), (NT, rn)):
                    e = r["T"] - Tc
                    ss[ten].append(e)
                    rows.append([seg, "f%d" % f, "%d%%" % round(100 * frac), ten, r["iters"],
                                 rn["fallback"] if ten == NT else "", "%.12f" % Tc, "%.12f" % r["T"],
                                 "%.3e" % abs(e), "%.3e" % r["residual"], "", "", ""])
            for ten in (CD, NT):
                if ss[ten]:
                    mae, rmse, einf = metrics(ss[ten])
                    rows.append([seg, "f%d" % f, "tổng hợp", ten, "", "", "", "", "", "",
                                 "%.3e" % mae, "%.3e" % rmse, "%.3e" % einf])
    write_csv("newton_compare.csv",
              ["Đoạn", "Lưới", "Mức q", "Phương pháp", "Số vòng", "Số lần fallback", "T chuẩn (phút)", "T (phút)",
               "|T − T chuẩn| (phút)", "Residual F(T) (xe·phút)", "MAE (phút)", "RMSE (phút)", "E∞ (phút)"], rows)
    print("\n== (3) Dữ liệu A/B (tol = %g): sai số T so với T chuẩn (chia đôi, tol %g) ==" % (tol, TOL_CHUAN))
    print("%-4s %-4s %-9s %6s %11s %11s %11s" % ("Đoạn", "Lưới", "Phương pháp", "Vòng", "MAE", "RMSE", "E∞"))
    for r in rows:
        if r[2] == "tổng hợp":
            vong = [x[4] for x in rows if x[0] == r[0] and x[1] == r[1] and x[3] == r[3] and x[2] != "tổng hợp"]
            print("%-4s %-4s %-9s %6s %11s %11s %11s" % (r[0], r[1], r[3], "%d-%d" % (min(vong), max(vong)),
                                                        r[10], r[11], r[12]))
    print("Đã ghi results/newton_compare.csv")


# ==== 5. So sánh cách chọn điểm đầu T0 (lưới gốc f1) ====

def so_sanh_diem_dau(cfg):
    tol, mx = cfg["bisection"]["tol_minutes"], cfg["bisection"]["max_iter"]
    cach = [("tỉ lệ q", lambda a, b, q: a + (b - a) * q),     # cách đang dùng
            ("giữa đoạn", lambda a, b, q: (a + b) / 2.0),
            ("đầu mút b", lambda a, b, q: b),
            ("đầu mút a", lambda a, b, q: a)]
    rows = []
    for seg in cfg["segments"]:
        t, y = read_grid(grid_path(seg, "timestamps", 1))
        I = cumulative(t, y)
        a, b = float(t[0]), float(t[-1])
        for q, Q in zip(cfg["q_fractions"], q_levels(float(I[-1]), cfg["q_fractions"])):
            dong = [seg, "%d%%" % round(100 * q)]
            for ten, chon in cach:
                r = newton_bao_ve(t, y, I, Q, tol, mx, T0=chon(a, b, q))
                dong += [r["iters"], r["fallback"]]
            rows.append(dong)
    head = ["Đoạn", "Mức q"]
    for ten, _ in cach:
        head += ["Số vòng (%s)" % ten, "Fallback (%s)" % ten]
    write_csv("newton_diem_dau.csv", head, rows)
    print("\n== (4) Số vòng Newton (số lần fallback) theo cách chọn điểm đầu, lưới f1, tol = %g ==" % tol)
    print("%-5s %-5s" % ("Đoạn", "Mức") + "".join(" %12s" % ten for ten, _ in cach))
    for r in rows:
        o = "".join(" %12s" % ("%d (%d)" % (r[2 + 2 * i], r[3 + 2 * i])) for i in range(len(cach)))
        print("%-5s %-5s" % (r[0], r[1]) + o)
    print("Đã ghi results/newton_diem_dau.csv")


if __name__ == "__main__":
    cfg = load_config()
    kiem_chung_newton(cfg)
    bac_hoi_tu(cfg)
    so_sanh_du_lieu(cfg)
    so_sanh_diem_dau(cfg)