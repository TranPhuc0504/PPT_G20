"""MOT script chay lai tu dong toan bo ket qua Phan 2 (De tai 20).

Chay tu thu muc PPT_G20_T20:   python src/run_all.py

Da co: data_prep, integrate, bisection, validate, experiments.
Cac buoc sau them vao danh sach STEPS khi viet xong; script bo qua buoc chua co file.
"""
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from common import load_config, set_seed  # noqa: E402

STEPS = [
    ("check_input", "Buoc 00: kiem tra dau vao (Quy dinh 2.1, 2.3)"),
    ("data_prep", "Buoc 0: chuan bi du lieu A/B, luoi h0/2h0/4h0"),
    ("integrate", "Buoc 1-2: tich phan hinh thang, tong, Q, ham F(T)"),        # Mang 2/3
    ("bisection", "Buoc 3: chia doi, so vong, residual"),                      # Mang 3
    ("validate", "Buoc 4: kiem chung y = 1 + t, sai so nghiem"),               # Mang 4
    ("experiments", "Buoc 5: lam thua luoi, do nhay lay mau va dung sai"),     # Mang 5
    ("make_figures", "Ve do thi tich luy va giao muc Q (dung don vi)"),        # Mang 6
]


def main():
    cfg = load_config()
    set_seed(cfg["seed"])
    print("seed = %d | dtype = %s\n" % (cfg["seed"], cfg["dtype"]))
    for mod, label in STEPS:
        if not (Path(__file__).resolve().parent / (mod + ".py")).exists():
            print("[bo qua] %s (chua co src/%s.py)" % (label, mod))
            continue
        print("[chay]   %s" % label)
        importlib.import_module(mod).main()
        print()


if __name__ == "__main__":
    main()
