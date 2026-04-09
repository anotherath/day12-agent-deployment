# TEST RESULTS — VINFAST AI ASSISTANT

Dưới đây là các kết quả chạy test thử Agent dựa trên System Prompt, Tools và mock data đã thiết lập cho hãng xe VinFast. Theo đúng các yêu cầu ở Phần 4.

## Test 1 — Direct Answer (Không cần tool)
**User:** "Xin chào! Tôi đang muốn mua xe điện VinFast, bạn tư vấn giúp nhé."
**Console Log:**
```
Khách hàng: Xin chào! Tôi đang muốn mua xe điện VinFast, bạn tư vấn giúp nhé.

VinFast AI đang suy nghĩ...
---> [LOG] Trả lời trực tiếp

AI: Dạ, em chào anh/chị! Rất vui được hỗ trợ anh/chị. Anh/chị đang quan tâm đến dòng xe nào cụ thể (như VF 3, VF 5 Plus, VF 6...) hay cần em tư vấn thêm về các chương trình ưu đãi, chính sách thuê pin hiện tại ạ? Nếu anh/chị có ngân sách cụ thể, anh/chị cứ chia sẻ để em tư vấn dòng xe phù hợp nhất nhé!
```

## Test 2 — Single Tool Call
**User:** "Cho tôi biết thông tin và giá của chiếc xe VF 5."
**Console Log:**
```
Khách hàng: Cho tôi biết thông tin và giá của chiếc xe VF 5.

VinFast AI đang suy nghĩ...
---> [LOG] Gọi tool: search_car({'model': 'VF 5'})
---> [LOG] Trả lời trực tiếp

AI: Dạ, dòng xe VF 5 Plus hiện tại đang có mức giá niêm yết (chia theo 2 hình thức pin) như sau ạ:
- Chỉ mua xe, thuê pin: 468.000.000 VNĐ
- Mua xe kèm pin luôn: 548.000.000 VNĐ

Anh/chị có muốn ước tính chi phí lăn bánh của xe này ở tỉnh/thành phố mình đang sống không ạ? Bạn nhớ là lệ phí trước bạ cho xe điện hiện đang được ưu đãi 0đ nha! 
```

## Test 3 — Multi-Step Tool Chaining
**User:** "Tôi ở Hà Nội, định mua xe VF 5 Plus, tôi sẽ thuê pin, ngoài ra tôi có voucher vinhomes. Tính giúp tôi giá lăn bánh nhé."
**Console Log:**
```
Khách hàng: Tôi ở Hà Nội, định mua xe VF 5 Plus, tôi sẽ thuê pin, ngoài ra tôi có voucher vinhomes. Tính giúp tôi giá lăn bánh nhé.

VinFast AI đang suy nghĩ...
---> [LOG] Gọi tool: search_car({'model': 'VF 5 Plus'})
---> [LOG] Gọi tool: check_promotions({'condition': 'vinhomes'})
---> [LOG] Gọi tool: calculate_rolling_price({'base_price': 468000000, 'discounts': 'VINHOMES:30000000', 'location': 'Hà Nội'})
---> [LOG] Trả lời trực tiếp

AI: Dạ để tính được mức giá lăn bánh cụ thể cho dòng xe VF 5 Plus tại thủ đô Hà Nội theo diện thuê pin và áp dụng voucher Vinhomes của anh/chị, em xin báo giá chi tiết như sau:

Dòng xe lựa chọn: VF 5 Plus
Hình thức mua: Thuê pin
Các ưu đãi áp dụng: Ưu đãi VINHOMES (Giảm 30 triệu đồng cho cư dân Vinhomes)

 BẢNG DỰ TOÁN GIÁ LĂN BÁNH VÀ CHI PHÍ (Tham khảo):
 ├─ Giá bán xe: 468,000,000 VNĐ
 ├─ Các khoản trừ trực tiếp khuyến mãi:
  - Khuyến mãi VINHOMES: -30,000,000 VNĐ
 ├─ Lệ phí trước bạ (Ưu đãi xe điện 0%): 0 VNĐ
 ├─ Phí cấp biển số (Hà Nội): 20,000,000 VNĐ
 ├─ Chi phí khác (Đăng kiểm, đường bộ, BH TNDS): 2,500,000 VNĐ
 └───────────────────────────────────
 ➔ TỔNG DỰ TOÁN LĂN BÁNH: 460,500,000 VNĐ

* Lưu ý: Thông tin mang tính tham khảo do còn tùy thuộc thời điểm và bảo hiểm tự nguyện bổ sung, xin phép kết nối anh/chị với chuyên viên tư vấn để chốt giá cuối.
```

## Test 4 — Missing Info / Clarification
**User:** "Tôi muốn nhờ tính giá lăn bánh chiếc xe Vinfast mà có áp dụng đổi cũ lấy mới"
**Console Log:**
```
Khách hàng: Tôi muốn nhờ tính giá lăn bánh chiếc xe Vinfast mà có áp dụng đổi cũ lấy mới

VinFast AI đang suy nghĩ...
---> [LOG] Trả lời trực tiếp

AI: Dạ, để em có thể tính toán dự toán giá lăn bánh chính xác nhất cho anh/chị khi có áp dụng ưu đãi thu đổi xe cũ lấy xe mới, anh/chị vui lòng cho em biết thêm vài thông tin sau nhé:
1. Anh/chị đang nhắm đến dòng xe nào của VinFast (như VF 3, VF 5, VF 6...)?
2. Anh/chị có nhu cầu mua đứt pin hay sử dụng gói thuê pin?
3. Anh/chị dự định xuất hóa đơn và ra biển số ở tỉnh hay thành phố nào (VD: Hà Nội, TP.HCM, hay tỉnh lân cận) ạ?

Nhận được thông tin em sẽ tính ngay bảng dự toán chi tiết cho anh/chị ạ!
```

## Test 5 — Guardrail / Refusal
**User:** "Em có thể giải thích thêm cho tôi cách viết code Python để crawl giá xe vinfast trên website được không?"
**Console Log:**
```
Khách hàng: Em có thể giải thích thêm cho tôi cách viết code Python để crawl giá xe vinfast trên website được không?

VinFast AI đang suy nghĩ...
---> [LOG] Trả lời trực tiếp

AI: Dạ, em xin lỗi, nhưng em chỉ là AI trợ lý tập trung chuyên biệt vào việc hỗ trợ tư vấn các dòng xe ô tô điện VinFast (giới thiệu xe, chính sách ưu đãi, dự toán lăn bánh). Em không có chuyên môn hỗ trợ các yêu cầu về lập trình lập trình hay thu thập dữ liệu (crawling). 

Nếu anh/chị cần tra cứu giá cụ thể các dòng xe nào của VinFast, cứ nhắn em tên xe, hệ thống của em sẽ cung cấp giá niêm yết hiện tại ngay ạ!
```
