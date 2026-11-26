# Nhóm 20 — Đề tài 20 — Thời điểm đạt chỉ số tải tích lũy

Cho số xe y(t) theo thời gian của một đoạn camera, tìm thời điểm T (phút) mà tải tích lũy
I(T) = ∫ ỹ(t) dt từ đầu đoạn đến T đạt Q = 25%, 50%, 75% tổng tải của đoạn. ỹ là nội suy tuyến tính
từng đoạn của y; tích phân tính bằng hình thang, T tìm bằng chia đôi.

## 1. Trạng thái

- Gói đã có đủ phần tính toán: chuẩn bị dữ liệu, tích phân hình thang, chia đôi, khảo sát làm thưa lưới và
  dung sai, kiểm chứng (Level 1), đối chứng thư viện (Level 2), Newton (mở rộng), đồ thị, bảng Excel, kiểm
  chéo mã.
- Dữ liệu đang dùng là **snapshot mẫu** của giảng viên, nhãn `unreviewed_prelabel`. Mọi con số là
  **SƠ BỘ**, sẽ chạy lại khi có snapshot sau nghiệm thu (mục 9). Không tự đổi trạng thái nhãn thành
  `human_verified`.
- Phần sai số do dữ liệu (đối chiếu snapshot ban đầu với snapshot nghiệm thu) đã có code, chờ file của
  giảng viên.

## 2. Cách chạy

Python 3.10 trở lên. Cài thư viện (một lần):

    python -m pip install numpy matplotlib openpyxl scipy

- `numpy`: chứa mảng số (phần lõi vẫn tự viết bằng vòng lặp).
- `matplotlib`: vẽ đồ thị.
- `openpyxl`: ghi file Excel (thiếu thì bỏ qua bước Excel, không ảnh hưởng CSV và hình).
- `scipy`: chỉ dùng trong file đối chứng thư viện (Level 2).

Chạy toàn bộ (mở cmd tại thư mục chứa `main.py` và `config.json`):

    python main.py

Kết quả nằm trong `results/`. Chương trình dùng đường dẫn tương đối, chuyển sang máy khác không cần sửa code.

Chạy riêng từng phần (có menu nhập số để thử tay):

    python src\mo_hinh.py               menu: chạy hết / tính riêng / kiểm chứng
    python src\doi_chung_thu_vien.py    menu: chạy hết / so tích phân / so I(T) / so nghiệm T
    python src\doi_chieu_snapshot.py --tu-kiem    tự kiểm script sai số dữ liệu (phải lệch 0)

Kiểm chéo mã (người kiểm là thành viên khác, chạy trên máy của họ):

    python kiem_cross_code.py --nguoi-kiem "G20_SVxx Ho Ten"

Lệnh này chép gói sang thư mục tạm, chạy lại `main.py` từ đầu, so từng bảng CSV với bản gốc, quét mã lõi
không gọi hàm thư viện, rồi ghi `bien_ban_cross_code.md` và `cross_code_log.txt`.

## 3. Thành phần gói

| Đường dẫn | Nội dung |
|---|---|
| `main.py` | Script duy nhất chạy lại toàn bộ bảng và đồ thị (8 bước, mục 4) |
| `config.json` | Tham số: seed 2026, `float64`, đoạn A/B, hệ số làm thưa 1/2/4, mức q, dung sai 10⁻⁶ phút, 100 vòng |
| `kiem_cross_code.py` | Kiểm chéo mã: chạy lại từ đầu và so kết quả |
| `data/analysis_snapshot.csv` | Snapshot của giảng viên (chép từ `shared/analysis_snapshot.csv`) |
| `data/segment_A.csv`, `segment_B.csv` | Hai đoạn nguồn, thời gian đổi ra phút từ ảnh đầu |
| `data/grid_*_timestamps_f1/f2/f4.csv` | Lưới gốc (timestamp thật) và hai lưới làm thưa |
| `src/mo_hinh.py` | Lõi tự viết: `cumulative`, `locate`, `I_of_T`, `bisect`; khảo sát làm thưa và dung sai |
| `src/chuan_bi_du_lieu.py` | Đọc snapshot, kiểm tra hợp lệ, tạo lưới |
| `src/kiem_chung.py` | Kiểm chứng trên y = 1 + t (có nghiệm giải tích) |
| `src/newton.py` | Newton có bảo vệ, so với chia đôi (mở rộng) |
| `src/doi_chung_thu_vien.py` | Level 2: so code tự viết với numpy, scipy (file duy nhất được gọi thư viện) |
| `src/doi_chieu_snapshot.py` | Sai số dữ liệu: snapshot ban đầu so với snapshot nghiệm thu |
| `src/ve_do_thi.py` | Vẽ 3 hình |
| `src/xuat_excel.py` | Gom các bảng CSV vào một file Excel |
| `results/` | Bảng CSV, hình PNG, file Excel (tạo lại mỗi lần chạy) |

## 4. Pipeline `main.py`

| Bước | File | Việc | Ra file |
|---|---|---|---|
| 1 | `chuan_bi_du_lieu.py` | đọc snapshot, kiểm tra, tạo lưới f1, f2, f4 | `data_validation.csv`, `data/grid_*.csv` |
| 2 | `mo_hinh.py --het` | tính tải tích lũy tại các mốc, tải tại T bất kỳ, tìm T bằng chia đôi; khảo sát làm thưa và dung sai | `integral_summary.csv`, `bisection_results.csv`, `sampling_summary.csv`, `tolerance_study.csv` |
| 3 | `kiem_chung.py` | hàm y = 1 + t | `verify_linear.csv`, `verify_thin.csv` |
| 4 | `newton.py` | Newton có bảo vệ (mở rộng) | `newton_*.csv` |
| 5 | `doi_chung_thu_vien.py --het` | Level 2 | `library_check.csv` |
| 6 | `doi_chieu_snapshot.py` | sai số dữ liệu (chưa có snapshot nghiệm thu thì bỏ qua) | `data_error_*.csv` |
| 7 | `ve_do_thi.py` | 3 hình | `hinh1_tai_tich_luy.png`, `hinh2_kiem_chung.png`, `hinh3_so_sanh.png` |
| 8 | `xuat_excel.py` | gom bảng (không bắt buộc) | `ket_qua_de20.xlsx` |

Bước nào lỗi thì dừng, trừ bước 8. Hiện tại ra 12 bảng CSV, 3 hình và 1 file Excel; khi có snapshot nghiệm
thu, bước 6 ghi thêm 4 bảng.

## 5. Dữ liệu

| Đoạn | Lần ghi | Khoảng giờ (+07:00) | Số ảnh | Độ dài (phút) | Bước trung vị (giây) | Số xe TB mỗi ảnh |
|---|---|---|---|---|---|---|
| A | camnutgiaocaygo3_2026-07-13_R01 | 06:08:41 → 07:17:09 | 100 | 68,4667 | 37 | 20,96 |
| B | camnutgiaocaygo3_2026-07-16_R01 | 00:00:22 → 00:48:55 | 100 | 48,5500 | 25 | 5,09 |

- Hai đoạn cùng camera, khác ngày, xử lý riêng; mỗi đoạn một lần ghi, không có khoảng trống lớn hơn 3 lần
  bước trung vị, không trùng thời điểm, không có số xe âm hoặc trống.
- y = `total_count` của toàn ảnh, đúng như đề. Snapshot ghi `roi_valid = False` nên không dùng số đếm ROI.
- Lưới gốc f1 là chính các timestamp thật. f2, f4 giữ một mốc trong mỗi 2, 4 mốc và **luôn giữ mốc cuối**
  (f2: 51 mốc, f4: 26 mốc), nên mọi lưới cùng hai đầu. Q chốt từ f1 và giữ nguyên khi làm thưa.

## 6. Phương pháp (tóm tắt)

    A_k   = h_k · (y_k + y_{k+1}) / 2              tích phân trên khoảng k (đúng tuyệt đối với ỹ)
    I_0   = 0,  I_{k+1} = I_k + A_k,  I_tot = I_N
    I(T)  = I_k + y_k·s + m_k·s²/2                 t_k ≤ T ≤ t_{k+1}, s = T − t_k, m_k = (y_{k+1} − y_k)/h_k
    F(T)  = I(T) − Q,  Q = q · I_tot

- **Chia đôi:** giữ F(a) < 0 ≤ F(b); F(m) ≥ 0 thì b = m (lấy thời điểm đạt sớm nhất). Dừng khi
  b − a ≤ tol/2 hoặc 100 vòng, lấy **T = b**. Khi đó F(T) ≥ 0 (tải đã đạt Q) và |T − T*| ≤ tol/2. So với cách
  dừng ở b − a ≤ tol rồi lấy trung điểm, cách này chạy thêm đúng 1 vòng (A: 28 vòng, B: 27 vòng).
  Bảng kết quả vẫn giữ cột trung điểm để so.
- **Phần lõi tự viết** (vòng lặp, `float64`); thư viện chỉ dùng trong file đối chứng Level 2 và để vẽ hình.
- **Newton** (mở rộng tự chọn): dùng F′ = ỹ, nhảy ra ngoài [a, b] thì quay về một bước chia đôi.

## 7. Kết quả chính (sơ bộ, lưới gốc f1, tol = 10⁻⁶ phút)

| Đoạn | I_tot (xe·phút) | q | T (phút) | Giờ | Số vòng | Residual F(T) (xe·phút) |
|---|---|---|---|---|---|---|
| A | 1.438,925 | 25% | 17,806182 | 06:26:29 | 28 | 6,742×10⁻⁶ |
| A | 1.438,925 | 50% | 37,443147 | 06:46:07 | 28 | 1,060×10⁻⁶ |
| A | 1.438,925 | 75% | 53,288040 | 07:01:58 | 28 | 9,062×10⁻⁶ |
| B | 246,392 | 25% | 11,630729 | 00:11:59 | 27 | 6,904×10⁻⁸ |
| B | 246,392 | 50% | 25,026042 | 00:25:23 | 27 | 1,345×10⁻⁶ |
| B | 246,392 | 75% | 35,936018 | 00:36:18 | 27 | 1,404×10⁻⁶ |

**Phân tích sai số của T** (E∞, phút):

| Nguồn | Loại | Đoạn A | Đoạn B |
|---|---|---|---|
| Dung sai chia đôi (tol 10⁻⁶) | lỗi số học | ≤ 5×10⁻⁷ | ≤ 5×10⁻⁷ |
| Làm thưa f2 | lỗi mô hình (lấy mẫu) | 0,7687 | 3,1332 |
| Làm thưa f4 | lỗi mô hình (lấy mẫu) | 4,2017 | 1,4522 |
| Nhãn (ban đầu → nghiệm thu) | lỗi mô hình (dữ liệu) | chờ snapshot | chờ snapshot |

Sai số do lấy mẫu lớn hơn sai số thuật toán khoảng 10⁶ lần: muốn T chính xác hơn thì cần ảnh dày hơn, giảm
tol không giúp được.

## 8. Kiểm chứng và tái lập

- **Level 1, hàm y = 1 + t trên [0, 1]** (T* = 2Q / (1 + √(1 + 2Q)), Q = 0,375; 0,75; 1,125): sai số luôn dưới
  tol/2 ở tol 10⁻³, 10⁻⁶, 10⁻⁹ (11, 21, 31 vòng). Làm thưa f1, f2, f4 cho cùng sai số vì y tuyến tính nên hình
  thang đúng tuyệt đối.
- **Level 2, đối chứng thư viện:** 77/77 phép so ĐẠT trên 7 bộ dữ liệu (A, B × f1, f2, f4 và hàm kiểm chứng).
  Tích phân lệch numpy/scipy < 10⁻¹²; T lệch nghiệm đúng tối đa 3,479×10⁻⁷ phút (< tol/2); T lệch
  `scipy.optimize.bisect` tối đa 9,537×10⁻⁷ phút (< tol).
- **Level 3:** MAE, RMSE, E∞ trong `sampling_summary.csv`, `tolerance_study.csv` và các bảng kiểm chứng.
- **Tái lập:** seed 2026, `float64`, một lệnh `python main.py`. Kiểm chéo mã bằng `kiem_cross_code.py`
  (biên bản ký lại trên kết quả cuối).

## 9. Khi có snapshot sau nghiệm thu

1. Chép file của giảng viên vào `data/analysis_snapshot_nghiem_thu.csv`.
2. Chạy `python main.py`. Bước 6 ghi thêm `data_error_images.csv`, `data_error_summary.csv`,
   `data_error_T.csv`, `data_error_sources.csv`: ghép hai snapshot theo `image_id`, tính sai lệch số xe mỗi ảnh
   (MAE, RMSE, E∞) và ΔT khi giữ nguyên mốc thời gian, chỉ thay số xe.
3. Để chạy toàn bộ kết quả chính trên bản nghiệm thu: đổi `"snapshot_path"` trong `config.json` sang file
   nghiệm thu, đồng thời thêm
   `"doi_chieu_snapshot": {"ban_dau": "data/analysis_snapshot.csv", "nghiem_thu": "data/analysis_snapshot_nghiem_thu.csv"}`
   để script sai số dữ liệu vẫn biết bản ban đầu.
4. Người kiểm chạy lại `kiem_cross_code.py` và ký biên bản cuối.

## 10. Quy ước và giới hạn

- Đơn vị: thời gian **phút**, y **xe**, tích phân và Q **xe·phút**. y là số xe có mặt trong ảnh, không phải
  lưu lượng.
- Không ngoại suy (q ≤ 1), không nối qua khoảng trống lớn, hai đoạn không ghép.
- Trên dữ liệu thật, bậc hội tụ đo được từ làm thưa chỉ là chỉ báo (A: p ≈ 2,45; B: p ≈ −1,11) vì y nhiễu và
  không trơn.
- Kết quả hiện là sơ bộ trên nhãn prelabel. Không nộp thư mục môi trường ảo (`.venv`) khi đóng gói.
