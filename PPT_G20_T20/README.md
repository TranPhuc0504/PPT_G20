# PPT_G20_T20 - Phan 2 Phuong phap tinh, De tai 20 (khung code)

Thoi diem dat chi so tai tich luy: tim T sao cho tich phan y(t) tu t0 den T bang Q.

## Cai dat (mot lan)
    pip install numpy pandas matplotlib

## Cach chay
1. Chep `shared/analysis_snapshot.csv` vao thu muc `data/`.
2. Mo cmd tai thu muc `PPT_G20_T20`, go:

       python src/run_all.py

Ket qua: `data/segment_A.csv`, `data/segment_B.csv`, `data/grid_*_f1|f2|f4.csv`,
`results/data_validation.csv`.

## Cau truc
    config.json     tham so (seed 2026, float64, h0 = 30 s, Q, dung sai)
    data/           CSV doan A/B dung cho bai toan
    src/            script loi chay tu dong bang duong dan tuong doi
    results/        bang CSV, hinh do thi
    (can them) slides.pdf, report.pdf, contributions.csv

## Quy uoc
- Thoi gian tinh bang PHUT, y la so xe, tich phan co don vi xe.phut.
- Luoi h0, 2h0, 4h0 deu chua moc dau va moc cuoi THAT cua doan (`append_true_endpoint`),
  nen moi luoi co cung hai dau. Day la gia dinh cua nhom, can ghi trong bao cao.
- Q chot tu du lieu goc (hinh thang tren timestamp that), khong doi theo luoi.
- Nhan hien la `unreviewed_prelabel` => moi ket qua la SO BO cho den khi co nhan nghiem thu.
- Phan loi (hinh thang, chia doi) phai TU CAI DAT, khong goi ham thu vien;
  thu vien chi dung de doi chung (Level 2) va ve hinh.
