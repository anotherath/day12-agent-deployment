from langchain_core.tools import tool
import requests
import re
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# ============================================================
# MOCK DATA — Dữ liệu giả lập hệ thống bán hàng VinFast
# Phục vụ tính toán ước lượng cấu hình và giá
# ============================================================


@tool
def search_car(model: str) -> str:
    """
    Tra cứu thông tin cơ bản và giá niêm yết (Cả gói Thuê pin và Mua pin mới nhất) của xe VinFast từ website vinfastgiare.vn.
    Tham số:
    - model: mã xe hoặc tên dòng xe (VD: 'VF 3', 'VF 5', 'VF 6', 'VF 7', 'VF 8', 'VF 9')
    """
    url = "https://r.jina.ai/https://vinfastgiare.vn/San-pham/"
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        text_content = response.text
    except Exception as e:
        return f"Không thể lấy dữ liệu giá xe gốc từ website lúc này. Lỗi: {e}"
        
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = f"""Bạn là chuyên gia cập nhật giá xe VinFast trực tuyến.
Dưới đây là danh sách sản phẩm và giá cả mới nhất từ website bán hàng:
---
{text_content[:25000]}
---
Khách hàng đang muốn tra cứu giá của dòng xe: "{model}".
Nhiệm vụ của bạn là tìm thông tin phiên bản tiêu chuẩn hoặc Plus của dòng xe này và trích xuất giá bán tĩnh.
Yêu cầu bắt buộc về cấu trúc khi trả kết quả:
Dòng xe {model}:
- Giá thuê pin (Base price): [Giá trị thực tế lấy trên web lớn nhất] VNĐ (hoặc 'Không rõ' nếu web không ghi)
- Giá mua luôn pin (có pin): [Giá trị thực tế lấy trên web cao hơn] VNĐ (hoặc 'Không rõ' nếu web không ghi)

Lưu ý: 
- Chỉ in định dạng số đầy đủ (ví dụ: 468,000,000 VNĐ) dựa vào dữ liệu web, không tự bịa ra.
- Nếu không tìm thấy, hãy báo Không tìm thấy.
"""
    try:
        res = llm.invoke([HumanMessage(content=prompt)])
        return res.content
    except Exception as e:
        return f"Lỗi xử lý ngôn ngữ khi trích xuất giá xe: {e}"

@tool
def check_promotions(condition: str) -> str:
    """
    Tìm kiếm và đào sâu tài liệu trong file Sale.md để tra cứu mọi thông tin khuyến mại, voucher, chính sách bán hàng.
    Gọi công cụ này ngay lập tức mỗi khi khách hàng hỏi về ưu đãi (VD: 'Giờ trái đất', 'vinhomes', 'thu cũ đổi mới').
    Tham số:
    - condition: cụm từ sự kiện hoặc ưu đãi khách muốn hỏi (VD: 'Giờ trái đất')
    """
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    # Tạm thời đọc file Sale.md thay vì cào web
    sale_md_path = "Sale.md"
    try:
        with open(sale_md_path, "r", encoding="utf-8") as f:
            text_content = f.read()
    except Exception as e:
        return f"Không thể lấy dữ liệu ưu đãi từ file lúc này. Lỗi: {e}"

    selected_pdf_text = ""

    # Bước 2: Tổng hợp và trích xuất số tiền
    vinhomes_promo = ""
    import os
    if os.path.exists("vinhomes_promotion.md"):
        with open("vinhomes_promotion.md", "r", encoding="utf-8") as f:
            vinhomes_promo = f"\n\n--- THÔNG TIN CHUYÊN BIỆT (LUÔN ÁP DỤNG MỚI NHẤT MỌI THỜI ĐIỂM) ---\n" + f.read()

    final_context = text_content + selected_pdf_text + vinhomes_promo
    
    prompt = f"""Bạn là chuyên gia trích xuất thông tin Khuyến mại VinFast.
Dưới đây là nội dung chính sách ưu đãi mới nhất (gồm website, tài liệu chi tiết và cập nhật đặc quyền riêng):
---
{final_context}
---
Hãy tìm và tóm tắt TẤT CẢ thông tin ưu đãi liên quan chặt chẽ đến TOÀN BỘ các điều kiện của khách hàng: "{condition}".
Đặc biệt lưu ý KHÔNG BỎ SÓT các từ khóa về: nghề nghiệp (Quân đội, Công an, CBNV), chương trình đổi xe (thu cũ đổi mới, xe xăng sang điện), nơi ở (cư dân Vinhomes). 
Lưu ý quan trọng: 
1. Nếu ưu đãi quy định giảm theo tỷ lệ % (Ví dụ 4% hay 1.5% hay 5%), hãy GHI RÕ số % đó và nhắc hệ thống AI tự nhân % này với giá xe để ra số tiền VNĐ. 
2. Nếu là một khoản tiền cố định (VD: 100 triệu), ghi rõ số đó.
3. Chú ý các điều kiện KHÔNG ÁP DỤNG ĐỒNG THỜI (ví dụ: Công an/Quân đội không áp dụng cùng Vinclub). Hãy phân tích rõ ràng cái nào được cộng dồn, cái nào không.
4. ĐỐI VỚI CÁC ĐIỀU KIỆN ẨN: Nếu ưu đãi liên quan đến từ khóa mà đòi hỏi thêm điều kiện phụ (VD: CBNV Vingroup phải sở hữu xe xăng thì mới được giảm thêm), HÃY CẢNH BÁO rõ ràng để AI bên ngoài hiểu rằng "chỉ được tính % nếu khách chứng minh họ có xe xăng".
Hãy tóm tắt và format thật gọn gàng, rõ ý nhất để trợ lý chatbot đọc hiểu.
"""
    
    try:
        res = llm.invoke([HumanMessage(content=prompt)])
        return res.content
    except Exception as e:
        return f"Lỗi xử lý ngôn ngữ khi đọc khuyến mại tĩnh: {e}"

@tool
def calculate_rolling_price(base_price: int, discounts: str, location: str) -> str:
    """
    Công cụ tính toán (Rule-based engine) để xuất báo giá lăn bánh dự toán xe VinFast.
    Tham số:
    - base_price: Giá xe khởi điểm (số nguyên VNĐ).
    - discounts: Chuỗi danh sách mã giảm giá và số tiền trừ thẳng (hoặc tỷ lệ %), định dạng 'mã:số_lượng' cách nhau bằng phẩy. 
                 VD: 'VINHOMES:4%,THUCU:15000000,VINCLUB:1.5%'. Nhập 'none' nếu không có.
    - location: Thành phố ra biển (VD: 'Hà Nội', 'HCM', 'Nghệ An', 'Hải Phòng'). Ảnh hưởng phí cấp biển tĩnh.
    """
    total_disc = 0
    disc_details = ""
    
    if discounts.lower() != 'none' and discounts.strip():
        try:
            for item in discounts.split(','):
                if ':' not in item: continue
                code, amount_str = item.split(':', 1)
                code = code.strip()
                amount_str = amount_str.strip().lower()
                
                amount = 0
                if '%' in amount_str:
                    # Tính theo phần trăm
                    pct = float(re.sub(r'[^\d.]', '', amount_str))
                    amount = int(base_price * (pct / 100.0))
                    disc_details += f"  - Khuyến mãi {code} ({pct}%): -{amount:,} VNĐ\n"
                else:
                    # Tính theo số tiền cố định. Bỏ mọi ký tự không phải số
                    val = re.sub(r'[^\d]', '', amount_str)
                    if val:
                        amount = int(val)
                        disc_details += f"  - Khuyến mãi {code}: -{amount:,} VNĐ\n"
                
                total_disc += amount
        except Exception as e:
            return f"❌ Lỗi định dạng giảm giá truyền vào ({discounts}). Vui lòng kiểm tra lại. Lỗi: {e}"
            
    loc_lower = location.lower()
    if any(x in loc_lower for x in ['hà nội', 'hn', 'hcm', 'hồ chí minh', 'sg']):
        plate_fee = 20_000_000
    else:
        plate_fee = 2_000_000 # Ước tính các tỉnh khác
        
    other_fees = 2_500_000 # Đăng kiểm, phí đường bộ, BH TNDS (Cơ bản)
    
    # 0 VNĐ cho lệ phí trước bạ xe điện hiện hành
    registration_fee = 0 
    
    final_price = base_price - total_disc + plate_fee + other_fees + registration_fee
    
    ans = " BẢNG DỰ TOÁN GIÁ LĂN BÁNH VÀ CHI PHÍ (Tham khảo):\n"
    ans += f" ├─ Giá bán xe: {base_price:,} VNĐ\n"
    if total_disc:
        ans += f" ├─ Các khoản trừ trực tiếp khuyến mãi (Tổng: -{total_disc:,} VNĐ):\n{disc_details}"
    ans += f" ├─ Lệ phí trước bạ (Ưu đãi xe điện 0%): {registration_fee} VNĐ\n"
    ans += f" ├─ Phí cấp biển số ({location}): {plate_fee:,} VNĐ\n"
    ans += f" ├─ Chi phí khác (Đăng kiểm, đường bộ, BH TNDS): {other_fees:,} VNĐ\n"
    ans += " └" + "─"*35 + "\n"
    ans += f" ➔ TỔNG DỰ TOÁN LĂN BÁNH: {final_price:,} VNĐ"
    return ans
