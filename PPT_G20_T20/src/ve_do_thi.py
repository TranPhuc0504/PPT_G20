"""Vẽ đồ thị (Đề 20): đọc lưới trong data/ và kết quả trong results/, lưu hình PNG vào figures/.

Hình 1: tải tích lũy và giao mức Q (sản phẩm bắt buộc của đề)
Hình 2: kiểm chứng y = 1 + t, sai số theo dung sai (Bước 4)
Hình 3: biến động của T do lấy mẫu so với do dung sai (Bước 5)
Cần chạy mo_hinh.py (mục 1) và kiem_chung.py trước.
"""
import csv

import matplotlib
matplotlib.use("Agg")                    # vẽ ra file, không mở cửa sổ
import matplotlib.pyplot as plt

from mo_hinh import ROOT, bisect, cumulative, grid_path, load_config, q_levels, read_grid, results_dir

# Màu cố định theo lưới (giống nhau ở mọi hình)
MAU = {1: "#2a78d6", 2: "#eb6834", 4: "#1baf7a"}
CHU, CHU_PHU, LUOI = "#0b0b0b", "#52514e", "#e4e3df"


def kieu_truc(ax):
    # Trục và lưới nhạt, chữ màu trung tính
    ax.grid(True, color=LUOI, linewidth=0.8)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(CHU_PHU)
    ax.tick_params(colors=CHU_PHU, labelsize=9)


def doc_csv(name):
    # Đọc một file kết quả trong results/
    with open(results_dir() / name, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def luu(fig, ten):
    # Lưu hình vào figures/ (tự tạo thư mục nếu chưa có)
    d = ROOT / "figures"
    d.mkdir(exist_ok=True)
    fig.tight_layout()
    fig.savefig(d / ten, dpi=200)
    plt.close(fig)
    print("Da luu figures/%s" % ten)


# Hình 1: số xe ỹ(t) và tải tích lũy I(t), giao mức Q tại T (lưới gốc f1)
def hinh_tai_tich_luy(cfg):
    segs = cfg["segments"]
    tol, mx = cfg["bisection"]["tol_minutes"], cfg["bisection"]["max_iter"]
    fig, axs = plt.subplots(2, len(segs), figsize=(6 * len(segs), 7.5))
    for j, seg in enumerate(segs):
        t, y = read_grid(grid_path(seg, "timestamps", 1))
        I = cumulative(t, y)
        ax = axs[0, j]                                           # hàng trên: số xe
        ax.plot(t, y, color=MAU[1], linewidth=1.5)
        ax.set_title("Đoạn %s: số xe theo thời gian (nối thẳng giữa các ảnh)" % seg, fontsize=10, color=CHU)
        ax.set_xlabel("Thời gian từ đầu đoạn (phút)", color=CHU_PHU)
        ax.set_ylabel("Số xe ỹ(t) (xe)", color=CHU_PHU)
        kieu_truc(ax)
        ax = axs[1, j]                                           # hàng dưới: tải tích lũy và giao mức
        ax.plot(t, I, color=MAU[1], linewidth=2)
        for frac, Q in zip(cfg["q_fractions"], q_levels(float(I[-1]), cfg["q_fractions"])):
            T = bisect(t, y, I, Q, tol, mx)["T"]
            ax.plot([t[0], T], [Q, Q], color=CHU_PHU, linewidth=1, linestyle="--")   # mức Q
            ax.plot([T, T], [0, Q], color=CHU_PHU, linewidth=1, linestyle="--")      # thời điểm T
            ax.plot([T], [Q], marker="o", markersize=8, color=MAU[1], markeredgecolor="white", markeredgewidth=1.5)
            ax.annotate("%d%%: T = %.2f phút\nQ = %.1f xe·phút" % (round(100 * frac), T, Q), (T, Q),
                        xytext=(-8, 6), textcoords="offset points", ha="right", va="bottom",
                        fontsize=8.5, color=CHU)                  # đặt chữ phía trên-trái điểm (vùng trống)
        ax.set_title("Đoạn %s: tải tích lũy I(t) và thời điểm T đạt mức Q" % seg, fontsize=10, color=CHU)
        ax.set_xlabel("Thời gian từ đầu đoạn (phút)", color=CHU_PHU)
        ax.set_ylabel("I(t) (xe·phút)", color=CHU_PHU)
        ax.set_ylim(bottom=0)
        kieu_truc(ax)
    luu(fig, "hinh1_tai_tich_luy.png")


# Hình 2: kiểm chứng y = 1 + t, sai số lớn nhất theo dung sai (thang log)
def hinh_kiem_chung():
    rows = [r for r in doc_csv("verify_linear.csv") if r["Q_xe_phut"] == "tong_hop"]   # chỉ lấy dòng tổng hợp
    tol = [float(r["tol_phut"]) for r in rows]
    einf = [float(r["Einf_phut"]) for r in rows]
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.plot(tol, [x / 2 for x in tol], color=CHU_PHU, linestyle="--", linewidth=1, label="Cận lý thuyết tol/2")
    ax.plot(tol, einf, color=MAU[1], linewidth=2, marker="o", markersize=8, markeredgecolor="white",
            markeredgewidth=1.5, label="E∞ = max |T − T*|")
    for x, e in zip(tol, einf):
        ax.annotate("%.1e" % e, (x, e), xytext=(6, 6), textcoords="offset points", fontsize=9, color=CHU)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.invert_xaxis()                                            # dung sai nhỏ dần sang phải
    ax.set_title("Kiểm chứng y = 1 + t: sai số theo dung sai chia đôi", fontsize=10, color=CHU)
    ax.set_xlabel("Dung sai tol (phút)", color=CHU_PHU)
    ax.set_ylabel("Sai số (phút)", color=CHU_PHU)
    ax.legend(frameon=False, fontsize=9)
    kieu_truc(ax)
    luu(fig, "hinh2_kiem_chung.png")


# Hình 3: biến động lớn nhất của T do làm thưa lưới và do dung sai (thang log)
def hinh_so_sanh(cfg):
    tol = cfg["bisection"]["tol_minutes"]
    ls = [r for r in doc_csv("sampling_summary.csv") if r["thin"] != "chi_bao_p"]
    ds = [r for r in doc_csv("tolerance_study.csv") if float(r["tol_phut"]) < tol]   # mức mịn hơn tol
    nhan, gia_tri, mau = [], [], []
    for seg in cfg["segments"]:
        for r in ls:
            if r["segment"] == seg:
                nhan.append("%s · làm thưa %s" % (seg, r["thin"]))
                gia_tri.append(float(r["Einf_phut"]))
                mau.append(MAU[int(r["thin"][1:])])
        lech = [float(r["|T - T(tol chinh thuc)|_phut"]) for r in ds if r["segment"] == seg]
        if lech:
            nhan.append("%s · dung sai %g" % (seg, tol))
            gia_tri.append(max(lech))
            mau.append(CHU_PHU)
    fig, ax = plt.subplots(figsize=(7, 0.55 * len(nhan) + 1.5))
    yv = list(range(len(nhan)))[::-1]                            # dòng đầu ở trên cùng
    ax.barh(yv, gia_tri, color=mau, height=0.6)
    for yy, v in zip(yv, gia_tri):
        ax.annotate("%.2g phút" % v, (v, yy), xytext=(4, 0), textcoords="offset points", va="center",
                    fontsize=9, color=CHU)
    ax.set_yticks(yv)
    ax.set_yticklabels(nhan, fontsize=9, color=CHU)
    ax.set_xscale("log")
    ax.set_xlim(right=max(gia_tri) * 30)
    ax.set_title("Biến động lớn nhất của T: do lấy mẫu so với do dung sai", fontsize=10, color=CHU)
    ax.set_xlabel("E∞ (phút, thang log)", color=CHU_PHU)
    kieu_truc(ax)
    ax.grid(False, axis="y")
    luu(fig, "hinh3_so_sanh.png")


def main():
    cfg = load_config()
    hinh_tai_tich_luy(cfg)
    hinh_kiem_chung()
    hinh_so_sanh(cfg)
    import os
    os.startfile(ROOT / "figures")      # Windows: mở thư mục figures sau khi vẽ xong


if __name__ == "__main__":
    main()