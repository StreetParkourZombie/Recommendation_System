# Quy tắc Nghiên cứu cho Project Recommendation System

## Nguồn tài liệu
1. `01_Tổng quan PPNCKH.pdf` - Tổng quan nghiên cứu khoa học
2. `02_Tong Quan Tai Lieu.pdf` - Tổng quan tài liệu  
3. `03_Phuong Phap Luan Thiet Ke NC.pdf` - Phương pháp luận thiết kế nghiên cứu

## Quy tắc tổng hợp từ 3 bài giảng

### 1. Phương pháp luận nghiên cứu (PPNCKH)
- **DIKW Model**: Data → Information → Knowledge → Wisdom
- **Tư duy khoa học 3 cách**: Phân tích, tổng hợp, đánh giá
- **W5H2 Framework**: What, Who, Where, When, Why, How, How Much
- **FINER Criteria**: Feasible, Interesting, Novel, Ethical, Relevant

### 2. Thiết kế nghiên cứu
- **Quy trình 7 bước**:
  1. Xác định vấn đề
  2. Tổng quan tài liệu  
  3. Xây dựng giả thuyết
  4. Thiết kế nghiên cứu
  5. Thu thập dữ liệu
  6. Phân tích dữ liệu
  7. Báo cáo kết quả

- **Phân loại nghiên cứu CNTT**:
  - Nghiên cứu cơ bản (basic research)
  - Nghiên cứu ứng dụng (applied research)  
  - Nghiên cứu thực nghiệm (experimental research)
  - Nghiên cứu đánh giá (evaluative research)

### 3. Đạo đức nghiên cứu
- **Liêm chính học thuật**: Trích dẫn đúng, chống đạo văn
- **Bảo mật dữ liệu**: Ẩn danh hóa dữ liệu cá nhân
- **Xung đột lợi ích**: Khai báo rõ ràng

### 4. Viết báo cáo khoa học
- **Cấu trúc IMRAD**: Introduction, Methods, Results, and Discussion
- **Trích dẫn IEEE**: Chuẩn trích dẫn cho công nghệ
- **Định dạng 30-50 trang**: Quy mô báo cáo học phần
- **LaTeX/Overleaf**: Công cụ viết chuyên nghiệp

### 5. Đánh giá chất lượng nghiên cứu
- **Tính mới (Novelty)**: Đóng góp mới về giải thuật, kiến trúc, phương pháp
- **Khả năng tái lập (Reproducibility)**: Công bố code, dataset, cấu hình
- **Tính khái quát (Generalizability)**: Áp dụng trên nhiều dataset/domain
- **Ý nghĩa thực tiễn (Practical Impact)**: Giải quyết vấn đề thực tế

## Áp dụng cho Project Recommendation System

### A. Xác định bài toán nghiên cứu
- **Vấn đề**: Tác động của chiến lược chia tập dữ liệu đến tín hiệu đo và thiên lệch phổ biến
- **Tính mới**: Đề xuất SLI (Split Leakage Index) tương đối theo user và giao thức audit 3 bước
- **FINER Check**:
  - Feasible: Có dataset MovieLens 25M, code Spark đã chạy
  - Interesting: Gap nghiên cứu về leakage measurement
  - Novel: SLI tương đối (99.9988% vs 0% cho LOO)
  - Ethical: Dữ liệu công khai, không PII
  - Relevant: Ứng dụng cho hệ thống recommender thực tế

### B. Thiết kế nghiên cứu
- **Phương pháp**: Thực nghiệm (experimental research)
- **Biến độc lập**: 3 chiến lược chia tập (random, temporal global, leave-one-out)
- **Biến phụ thuộc**: Metric đo (NDCG, Recall), thiên lệch phổ biến, SLI
- **Kiểm soát**: 10 seed, phần cứng log, baseline 3 tầng

### C. Quy trình thực hiện
1. **Tổng quan tài liệu**: 14 bài báo Q1/CORE A, ma trận 5 cột, loại arXiv
2. **Thiết kế thực nghiệm**: 3 split × 3 tầng baseline × 10 seed
3. **Triển khai code**: MapReduce Java, PySpark, MongoDB, R, Streamlit
4. **Phân tích kết quả**: Mean ± Std, statistical significance, ablation study
5. **Viết báo cáo**: IMRAD structure, LaTeX, trích dẫn IEEE

### D. Yêu cầu chất lượng
- **Tái lập**: Public code trên GitHub, commit hash, requirements.txt
- **Phần cứng khai báo**: CPU, RAM, GPU, spark.version, thời gian chạy
- **Seed công bố**: 10 seed fixed cho mọi thí nghiệm
- **So sánh công bằng**: Chỉ so khi chênh lệch mẫu < 20% (giao thức audit)
- **Kết quả âm báo cáo**: Negative results về leakage measurement

### E. Sản phẩm đầu ra
1. **Báo cáo học phần**: 30-50 trang, định dạng học thuật
2. **Code repository**: Đầy đủ scripts, documentation
3. **Dataset splits**: Public splits theo [12] RecSys'20
4. **Logs thực nghiệm**: Hardware logs, runtime, seed values
5. **Bài báo conference**: Target RecSys/SIGIR workshop

## Lưu ý đặc biệt từ bài giảng
- **Phân biệt dự án kỹ thuật vs nghiên cứu**: Sử dụng công nghệ mới chưa đủ, cần câu hỏi nghiên cứu và đóng góp tri thức
- **4 dạng tạo tác khoa học**: Concepts, Models, Methods, Instantiations
- **Yêu cầu ThS**: Đóng góp ít nhất dạng 2 (Models) và 3 (Methods)
- **SO2 chiếm 40%**: Đề xuất kiến trúc cốt lõi là bắt buộc

## Checklist triển khai
- [x] Tổng quan 14 tài liệu Q1/CORE A (loại arXiv)
- [x] Xác định gap: thiếu chỉ số leakage tương đối theo user
- [x] Đề xuất SLI + giao thức audit (Models + Methods)
- [x] Thiết kế 3 tầng baseline (truyền thống, kinh điển, SOTA)
- [ ] Triển khai đầy đủ 3 split × 3 tầng × 10 seed
- [ ] Log hardware + seed + runtime
- [ ] Phân tích statistical significance
- [ ] Viết báo cáo IMRAD + LaTeX
- [ ] Chuẩn bị defense presentation

---
*Tổng hợp ngày 08/11/2026 từ 3 bài giảng PPNCKH HUFLIT*
