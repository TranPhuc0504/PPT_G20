"""Gom mọi bảng kết quả .csv trong results/ vào MỘT file Excel dễ đọc: results/ket_qua_de20.xlsx.

Chạy (sau các file khác): python src\\xuat_excel.py
Cần: pip install openpyxl   (chỉ để ghi file Excel, không dùng cho tính toán)

Vì sao cần: Excel trên máy cài định dạng Việt Nam dùng dấu phẩy cho phần thập phân, nên khi mở thẳng
file .csv (dùng dấu chấm), số bị hiểu là chữ (ô có tam giác xanh, không tính toán được). File .xlsx lưu
số thật nên hiển thị đúng ở mọi máy.
"""
import csv

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from mo_hinh import results_dir

# Thứ tự trang tính và tên hiển thị (tên trang tối đa 31 ký tự)
TRANG = [
    ("data_validation.csv", "Kiểm tra dữ liệu"),
    ("integral_summary.csv", "Tích phân"),
    ("bisection_results.csv", "Chia đôi"),
    ("sampling_summary.csv", "Làm thưa lưới"),
    ("tolerance_study.csv", "Dung sai"),
    ("verify_linear.csv", "Kiểm chứng - dung sai"),
    ("verify_thin.csv", "Kiểm chứng - làm thưa"),
    ("newton_kiem_chung.csv", "Newton - kiểm chứng"),
    ("newton_bac_hoi_tu.csv", "Newton - bậc hội tụ"),
    ("newton_compare.csv", "Newton - dữ liệu AB"),
    ("newton_diem_dau.csv", "Newton - điểm đầu"),
    ("library_check.csv", "Đối chứng thư viện"),
    ("data_error_summary.csv", "Sai số dữ liệu - đếm"),
    ("data_error_T.csv", "Sai số dữ liệu - T"),
    ("data_error_sources.csv", "So 3 nguồn sai số"),
    ("data_error_images.csv", "Sai số dữ liệu - từng ảnh"),
]
NEN_TIEU_DE = PatternFill("solid", fgColor="DDE7F5")    # nền xanh nhạt: dòng tên cột
NEN_MOI = PatternFill("solid", fgColor="E3F1E6")        # nền xanh lá nhạt: cột [Mới]
NEN_CU = PatternFill("solid", fgColor="FBEBDD")         # nền cam nhạt: cột [Cũ]
NEN_TONG = PatternFill("solid", fgColor="F2F2F2")       # nền xám: dòng tổng hợp
# Bảng đối chứng thư viện: mỗi mục một màu nền nhạt để dễ tách nhóm; tổng hợp đậm hơn cùng tông
MAU_MUC = {"1": ("EAF2FB", "C9DEF4"), "2": ("EEF7EE", "CDE8CF"), "3": ("FDF3E7", "F7DDBA"),
           "4": ("F3EEF9", "DCCDEE"), "5": ("E9F6F6", "C4E5E5")}
CHU_DAT, CHU_KHONG = Font(bold=True, color="1E7B3A"), Font(bold=True, color="B3261E")


def doi_so(chu):
    # Đổi chữ trong CSV thành số thật (nếu được) và chọn định dạng hiển thị cho ô
    s = chu.strip()
    if s == "" or s.endswith("%"):
        return chu, None
    try:
        if "e" in s.lower():
            return float(s), "0.000E+00"                # số rất nhỏ: dạng khoa học 2.551E-07
        if "." in s:
            le = len(s.split(".")[1])                   # giữ đúng số chữ số thập phân như trong CSV
            return float(s), "0." + "0" * le
        return int(s), "0"
    except ValueError:
        return chu, None                                # không phải số: giữ nguyên chữ


def them_trang(wb, file_csv, ten_trang):
    with open(results_dir() / file_csv, encoding="utf-8-sig", newline="") as fh:
        bang = list(csv.reader(fh))
    ws = wb.create_sheet(ten_trang)
    cot_muc = bang[0].index("Mục") if bang and "Mục" in bang[0] else None          # chỉ bảng đối chứng có cột Mục
    cot_kq = bang[0].index("Kết quả") if bang and "Kết quả" in bang[0] else None
    for i, dong in enumerate(bang):
        tong_hop = any("tổng hợp" in str(x) or "chỉ báo p" in str(x) or str(x).startswith("p =") for x in dong)
        for j, chu in enumerate(dong):
            o = ws.cell(row=i + 1, column=j + 1)
            if i == 0:                                  # dòng tên cột
                o.value = chu
                o.font = Font(bold=True)
                o.alignment = Alignment(wrap_text=True, vertical="center", horizontal="center")
                o.fill = NEN_MOI if chu.startswith("[Mới]") else NEN_CU if chu.startswith("[Cũ]") else NEN_TIEU_DE
                continue
            o.value, dinh_dang = doi_so(chu)
            if dinh_dang:
                o.number_format = dinh_dang
            if cot_muc is not None and dong[cot_muc] in MAU_MUC:          # tô theo mục
                nhat, dam = MAU_MUC[dong[cot_muc]]
                o.fill = PatternFill("solid", fgColor=dam if tong_hop else nhat)
                if tong_hop:
                    o.font = Font(bold=True)
            elif tong_hop:
                o.fill = NEN_TONG
                o.font = Font(bold=True)
            if j == cot_kq and chu in ("ĐẠT", "KHÔNG ĐẠT"):              # chữ xanh ĐẠT / đỏ KHÔNG ĐẠT
                o.font = CHU_DAT if chu == "ĐẠT" else CHU_KHONG
    ws.freeze_panes = "A2"                              # cố định dòng tên cột khi cuộn
    ws.row_dimensions[1].height = 60
    for j in range(1, ws.max_column + 1):               # độ rộng cột vừa nội dung
        dai = max(len(str(ws.cell(row=i, column=j).value or "")) for i in range(2, ws.max_row + 1)) \
            if ws.max_row > 1 else 8
        ws.column_dimensions[get_column_letter(j)].width = min(max(dai + 2, 12), 26)


def main():
    wb = Workbook()
    wb.remove(wb.active)
    co = []
    for file_csv, ten in TRANG:
        if (results_dir() / file_csv).exists():
            them_trang(wb, file_csv, ten)
            co.append(ten)
    if not co:
        raise SystemExit("Chưa có file kết quả nào trong results/. Hãy chạy các bước trước.")
    duong_dan = results_dir() / "ket_qua_de20.xlsx"
    try:
        wb.save(duong_dan)
    except PermissionError:
        raise SystemExit("Không ghi được %s: file đang mở trong Excel. Đóng file rồi chạy lại." % duong_dan.name)
    print("Đã ghi results/ket_qua_de20.xlsx (%d trang: %s)" % (len(co), ", ".join(co)))


if __name__ == "__main__":
    main()