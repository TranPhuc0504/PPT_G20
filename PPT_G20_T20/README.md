# Nhóm 20 — Đề tài 20 — Thời điểm đạt chỉ số tải tích lũy

Đề tài: cho hàm tải y(t) (số xe hiện diện theo thời gian), tìm thời điểm T sao cho tích phân tích lũy
I(T) = ∫ y(t) dt từ đầu đoạn đến T đạt ngưỡng Q (25%, 50%, 75% tổng tải của đoạn).

## 1. Phạm vi và trạng thái

Gói này là khung code Phần 2 (Phương pháp tính, 6 điểm) ở giai đoạn đầu: chọn/kiểm tra hai đoạn A/B
và chuẩn bị dữ liệu. Chưa phải hồ sơ hoàn chỉnh.

Dữ liệu camera hiện mang nhãn `unreviewed_prelabel` (PRELABEL, chưa nghiệm thu). Mọi kết quả tính từ
dữ liệu này là **SƠ BỘ**, không phải ground truth. Không tự đổi trạng thái nhãn thành `human_verified`.

## 2. Thành phần gói

| Đường dẫn | Nội dung |
|---|---|
| `config.json` | Tham số của dự án: seed 2026, kiểu `float64`, bước h0 = 30 giây, kiểu lưới gốc, hệ số làm thưa lưới, các mức Q, dung sai chia đôi, đơn vị |
| `data/analysis_snapshot.csv` | Bản chép của `shared/analysis_snapshot.csv` (giảng viên cung cấp). Tự chép vào trước khi chạy |
| `data/segment_A.csv`, `data/segment_B.csv` | Hai đoạn quan sát nguồn (giữ nguyên số đếm và nhãn), cột `t_min` là thời gian tính bằng phút từ mốc đầu đoạn |
| `data/grid_A_regular30s_f1.csv`, `grid_B_regular30s_f1.csv` | **Lưới gốc đều 30 giây** (h0 = 0,5 phút), nội suy tuyến tính từng đoạn; bắt đầu ở mốc đầu, kết thúc ở mốc h0 cuối còn nằm trong đoạn (A: 137 mốc, 0–68,0 phút; B: 98 mốc, 0–48,5 phút) |
| `data/grid_*_regular30s_f2.csv`, `..._f4.csv` | **Làm thưa mỗi 2 / mỗi 4 mốc** của lưới gốc đều (giữ mốc 0, 2, 4… / 0, 4, 8…), giá trị `y` giữ nguyên; luôn giữ mốc cuối của lưới gốc |
| `data/grid_A_timestamps_f1.csv`, `grid_B_timestamps_f1.csv` | **Lưới gốc theo timestamp thật** (100 mốc, không đều), dùng khi đề tài 20 cho phép thời gian không đều |
| `data/grid_*_timestamps_f2.csv`, `..._f4.csv` | Làm thưa mỗi 2 / mỗi 4 mốc của lưới timestamp thật, cùng hai đầu |
| `src/common.py` | Hàm dùng chung: đọc cấu hình, đặt seed, đường dẫn tương đối, kiểu `float64` |
| `src/data_prep.py` | Đọc snapshot, kiểm tra đoạn A/B, đổi thời gian ra phút, tạo các lưới |
| `src/run_all.py` | Script duy nhất chạy lại toàn bộ (hiện mới gọi bước chuẩn bị dữ liệu) |
| `results/data_validation.csv` | Bảng kiểm tra dữ liệu: số quan sát, trùng timestamp, gap, recording, nhãn… |
| `README.md` | Hướng dẫn và giới hạn sử dụng |

Các thành phần **sẽ bổ sung** khi hoàn thiện: `src/integrate.py` (nội suy + tích phân hình thang tự cài),
`src/bisection.py` (tìm T bằng chia đôi), `src/validate.py` (kiểm chứng trên hàm có nghiệm giải tích),
`src/experiments.py`, `src/make_figures.py`, thư mục `results/` (CSV, hình), `slides.pdf`, `report.pdf`,
`contributions.csv`.

## 3. Nguồn và lựa chọn dữ liệu

Nguồn: `shared/analysis_snapshot.csv` trong gói Traffic_BTL do giảng viên cung cấp; không tự đếm lại
từ ảnh để thay snapshot.

| Đoạn | Recording | Số quan sát | Thời điểm đầu (+07:00) | Thời điểm cuối (+07:00) | Độ dài (phút) |
|---|---|---:|---|---|---:|
| A | camnutgiaocaygo3_2026-07-13_R01 | 100 | 2026-07-13 06:08:41 | 2026-07-13 07:17:09 | 68,4667 |
| B | camnutgiaocaygo3_2026-07-16_R01 | 100 | 2026-07-16 00:00:22 | 2026-07-16 00:48:55 | 48,5500 |

Hai đoạn khác ngày, không giao nhau, mỗi đoạn nằm trong khoảng 80–300 quan sát và chỉ có một recording.
Hai đoạn được xử lý riêng, không ngoại suy và không nội suy qua khoảng trống (gap) lớn.

## 4. Dữ liệu gốc, lưới gốc và làm thưa lưới

- `segment_A.csv`, `segment_B.csv` là đầu vào chính: timestamp thật (ISO 8601), giữ nguyên giây.
- **Lưới gốc** có hai biến thể (cả hai đều được tạo, chọn dùng biến thể nào sau khi giảng viên xác nhận):
  - `regular30s`: lưới đều h0 = 30 giây = 0,5 phút (không phải 0,5 giây), nội suy tuyến tính trong từng đoạn,
    không ngoại suy, kết thúc tại mốc h0 cuối còn trong đoạn (Quy định mục 2.3, điểm 4). Giá trị `y` thập phân
    là kết quả nội suy, không phải số xe quan sát nguyên.
  - `timestamps`: chính các timestamp thật của đoạn (đề tài 20 cho phép thời gian không đều).
- **Làm thưa (Bước 5 của đề):** f2 giữ một mốc trong mỗi 2 mốc của lưới gốc, f4 giữ một mốc trong mỗi 4 mốc.
  Các điểm còn lại là **tập con của lưới gốc** (không nội suy lại), luôn giữ cùng hai đầu; Q được chốt từ lưới gốc
  và giữ cố định khi làm thưa.
- Với lưới `regular30s`, bước cuối của f2/f4 có thể ngắn hơn bước chuẩn vì phải giữ mốc cuối của lưới gốc.
- Số mốc lưới không phải số quan sát thật độc lập; không coi lưới mới là quan sát độc lập.

## 5. Phương pháp (tóm tắt)

Với t tính bằng phút, y là `total_count` (xe):

    h_i = t_(i+1) − t_i
    ỹ(t): nội suy tuyến tính từng đoạn qua các điểm (t_i, y_i)
    I(T) = S_k + y_k·s + m_k·s²/2        (s = T − t_k, m_k = độ dốc đoạn k, S_k = tích lũy đến t_k)
    F(T) = I(T) − Q ;  tìm T nhỏ nhất sao cho F(T) = 0 bằng chia đôi

- Q = 25%, 50%, 75% tổng tích phân của đoạn (chốt từ lưới gốc, giữ cố định khi làm thưa lưới).
- Dung sai chia đôi 1e-6 phút, tối đa 100 vòng; cập nhật cận trên khi F(m) ≥ 0 để lấy nghiệm sớm nhất.
- Kiểm chứng: y(t) = 1 + t có I(T) = T + T²/2, nghiệm T = −1 + √(1 + 2Q).
- Đơn vị: thời gian là **phút**; y là **xe**; tích phân/chỉ số tích lũy là **xe·phút**.
  Số xe hiện diện không phải lưu lượng; I không phải tổng số xe duy nhất đi qua.
- Phần lõi (nội suy, hình thang, chia đôi) **tự cài đặt**, không gọi hàm tích phân/tìm nghiệm của thư viện.
  Thư viện (NumPy/SciPy) chỉ dùng để đối chứng (Level 2) và vẽ hình.
- Mọi tính toán dùng `float64`. Các bước hiện tại là xác định (deterministic); seed quy ước của dự án là 2026
  nếu có bước ngẫu nhiên.

## 6. Cách chạy

Python 3.10 trở lên. Cài thư viện (một lần):

    pip install numpy pandas matplotlib

1. Chép `shared/analysis_snapshot.csv` vào thư mục `data/` của gói này.
2. Mở Terminal / cmd tại thư mục chứa README này và chạy:

       python src/run_all.py

Chương trình đọc đường dẫn tương đối từ vị trí của `config.json`, nên chuyển gói sang máy khác không cần sửa code.
Kết quả: `data/segment_A.csv`, `data/segment_B.csv`, `data/grid_*_<regular30s|timestamps>_f*.csv`, `results/data_validation.csv`.
Nếu có dòng mức `ERROR` trong bảng kiểm tra thì chương trình dừng và không chạy bước sau.

## 7. Giới hạn và cập nhật sau nghiệm thu

- Nhãn hiện là PRELABEL: kết quả chỉ mang tính **sơ bộ**, có thể thay đổi sau khi cập nhật snapshot nghiệm thu.
- Đề tài dùng `total_count` trên toàn ảnh, không dùng số đo ROI. Giữ nguyên `roi_valid = False` và các số đo ROI
  trống khi chưa được xác nhận; không thay bằng 0.
- Tuần 5–6: chạy lại trên snapshot chính thức do giảng viên cung cấp sau nghiệm thu, rồi cập nhật bảng kết quả,
  hình vẽ và báo cáo.
- Không nộp thư mục môi trường ảo (`.venv`) khi đóng gói.
